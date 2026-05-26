"""M2c.4: end-to-end curved-layer 5-axis pipeline tests.

This is the integration sanity check that all M2 pieces hold hands:
QP solve → iso-surfaces → curved paths → 5-axis G-code via the M1.5
emitter. Properties checked:

* Flat-top input collapses to vertical tool axes (the curved-layer
  pipeline degenerates to the planar 5-axis case from M1.5).
* Tilted-top input produces NON-zero A and C values somewhere — the
  whole point of multi-axis printing.
* Layer count matches the field range divided by layer height.
* G-code parses with the expected structure.
"""

from __future__ import annotations

import re

import numpy as np
import pytest

from reinforced_slicer.kinematics import AcTableMachine
from reinforced_slicer.mesh.tet import (
    TetMesh,
    bottom_face_indices,
    cube_tet_mesh,
    top_face_indices,
)
from reinforced_slicer.slicing.curved_5axis import curved_layer_5axis_pipeline
from reinforced_slicer.slicing.curvi_3d import CurviSlicer3DConfig


def _tilted_top_cube(s: int, tilt_slope: float) -> TetMesh:
    """Same fixture as in test_curvi_3d — duplicated to keep tests independent."""
    mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
    top = top_face_indices(s)
    perturbed = mesh.vertices.copy()
    perturbed[top, 2] = 1.0 + tilt_slope * perturbed[top, 0]
    n = s + 1
    for i in range(n):
        for j in range(n):
            top_idx = i + j * n + (n * n * s)
            new_top_z = perturbed[top_idx, 2]
            for k in range(n):
                idx = i + j * n + k * n * n
                perturbed[idx, 2] = (k / s) * new_top_z
    return TetMesh(vertices=perturbed, tets=mesh.tets)


_G1_LINE = re.compile(
    r"^G1 X(?P<x>[-\d.]+) Y(?P<y>[-\d.]+) Z(?P<z>[-\d.]+) "
    r"A(?P<a>[-\d.]+) C(?P<c>[-\d.]+) E(?P<e>[-\d.]+)$",
    re.MULTILINE,
)


class TestFlatTopDegenerates:
    def test_flat_top_yields_zero_rotaries(self) -> None:
        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        result = curved_layer_5axis_pipeline(
            mesh,
            top_face_indices(s),
            bottom_face_indices(s),
            AcTableMachine(),
            layer_height=0.25,
            path_spacing=0.3,
        )
        # A and C should all be ~0 because the displacement field is ~0
        # and so iso-surfaces are horizontal planes.
        a_values = [float(m["a"]) for m in _G1_LINE.finditer(result.gcode)]
        c_values = [float(m["c"]) for m in _G1_LINE.finditer(result.gcode)]
        assert a_values, "expected at least one G1 line"
        assert max(abs(v) for v in a_values) < 0.05  # near 0 in degrees
        assert max(abs(v) for v in c_values) < 0.05


class TestTiltedTopUsesRotaries:
    def test_tilted_top_emits_nonzero_a_axis(self) -> None:
        s = 4
        mesh = _tilted_top_cube(s=s, tilt_slope=0.3)
        # Push z_target higher than the natural mean so the QP actively
        # uses curved layers (otherwise it sometimes solves to h≈0).
        cfg = CurviSlicer3DConfig(
            flatness_weight=10.0, smoothness_weight=1e-4, z_target=1.15
        )
        result = curved_layer_5axis_pipeline(
            mesh,
            top_face_indices(s),
            bottom_face_indices(s),
            AcTableMachine(),
            layer_height=0.25,
            path_spacing=0.3,
            curvi_config=cfg,
        )
        a_values = [float(m["a"]) for m in _G1_LINE.finditer(result.gcode)]
        max_a = max(abs(v) for v in a_values)
        # With slope 0.3 on x, expected A ~= atan(0.3) in degrees ~= 16.7.
        # We just require *some* non-trivial tilt.
        assert max_a > 5.0, f"expected meaningful A-axis tilt, got max |A|={max_a:.2f}°"


class TestLayerCount:
    def test_layer_count_matches_field_range(self) -> None:
        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        result = curved_layer_5axis_pipeline(
            mesh,
            top_face_indices(s),
            bottom_face_indices(s),
            AcTableMachine(),
            layer_height=0.25,
        )
        # Field f = z + h ~= z spans roughly [0, 1]; with layer_height=0.25
        # and mid-layer start at 0.125, we expect 4 layers.
        assert result.n_layers == 4

    def test_path_points_are_non_trivial(self) -> None:
        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        result = curved_layer_5axis_pipeline(
            mesh,
            top_face_indices(s),
            bottom_face_indices(s),
            AcTableMachine(),
            layer_height=0.25,
            path_spacing=0.2,
        )
        assert result.n_paths >= result.n_layers
        assert result.n_path_points > 10 * result.n_layers


class TestGcodeStructure:
    def test_gcode_has_header_layer_comments_and_footer(self) -> None:
        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        result = curved_layer_5axis_pipeline(
            mesh,
            top_face_indices(s),
            bottom_face_indices(s),
            AcTableMachine(),
            layer_height=0.25,
        )
        text = result.gcode
        assert "G21" in text and "G90" in text  # mm, absolute
        assert "G28" in text  # home
        assert "M84" in text  # disable steppers (footer)
        layer_comments = re.findall(r"^; LAYER \d+", text, re.MULTILINE)
        assert len(layer_comments) == result.n_layers
