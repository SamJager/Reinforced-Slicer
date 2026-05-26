"""5-axis G-code emitter tests.

The seam-check property: with the tool axis fixed vertical, the AC-table
machine returns A = C = 0 for every pose, so the 5-axis G-code's XYZ
trajectory must match the 3-axis G-code's XY trajectory point for point.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import trimesh

from reinforced_slicer.kinematics import AcTableMachine
from reinforced_slicer.postproc.gcode import GcodeConfig, write_gcode
from reinforced_slicer.postproc.gcode_5axis import write_gcode_5axis
from reinforced_slicer.slicing.planar import PlanarSliceConfig, slice_planar


def _cube(side: float = 10.0) -> trimesh.Trimesh:
    cube = trimesh.creation.box(extents=(side, side, side))
    cube.apply_translation([side / 2.0, side / 2.0, side / 2.0])
    return cube


def _slice() -> tuple[PlanarSliceConfig, GcodeConfig, trimesh.Trimesh]:
    return (
        PlanarSliceConfig(layer_height=0.5, infill_spacing=0.4),
        GcodeConfig(),
        _cube(10.0),
    )


_PRINT_LINE = re.compile(
    r"^G1 X(?P<x>[-\d.]+) Y(?P<y>[-\d.]+)(?: Z(?P<z>[-\d.]+))?"
    r"(?: A(?P<a>[-\d.]+))?(?: C(?P<c>[-\d.]+))? E(?P<e>[-\d.]+)$",
    re.MULTILINE,
)


def test_5axis_header_initializes_rotaries() -> None:
    slice_cfg, gcode_cfg, cube = _slice()
    part = slice_planar(cube, slice_cfg)
    text = write_gcode_5axis(part, AcTableMachine(), gcode_cfg)
    assert "; reinforced-slicer M1 5-axis emitter" in text
    assert "G92 E0 A0 C0" in text


def test_5axis_emits_a_and_c_zero_for_vertical_tool_axis() -> None:
    slice_cfg, gcode_cfg, cube = _slice()
    part = slice_planar(cube, slice_cfg)
    text = write_gcode_5axis(part, AcTableMachine(), gcode_cfg)
    a_values = [float(m["a"]) for m in _PRINT_LINE.finditer(text) if m["a"] is not None]
    c_values = [float(m["c"]) for m in _PRINT_LINE.finditer(text) if m["c"] is not None]
    assert a_values, "expected at least one G1 line with an A word"
    assert max(abs(v) for v in a_values) < 1e-3
    assert max(abs(v) for v in c_values) < 1e-3


def test_5axis_xy_trajectory_matches_3axis_xy(tmp_path: Path) -> None:
    slice_cfg, gcode_cfg, cube = _slice()
    part = slice_planar(cube, slice_cfg)
    three_axis = write_gcode(part, tmp_path / "out_3axis.gcode", gcode_cfg).read_text()
    five_axis = write_gcode_5axis(part, AcTableMachine(), gcode_cfg)

    three_xy = [(float(m["x"]), float(m["y"])) for m in _PRINT_LINE.finditer(three_axis)]
    five_xy = [(float(m["x"]), float(m["y"])) for m in _PRINT_LINE.finditer(five_axis)]
    # 5-axis emitter writes Z on every G1 line; 3-axis only writes Z on layer
    # change. That changes the *line count* but not the XY trajectory of
    # the extruding moves. Strip travels that have no E word in 3-axis by
    # construction (regex requires E).
    assert len(three_xy) == len(five_xy)
    for (x3, y3), (x5, y5) in zip(three_xy, five_xy, strict=True):
        assert x3 == x5
        assert y3 == y5


def test_5axis_z_increases_per_layer() -> None:
    slice_cfg, gcode_cfg, cube = _slice()
    part = slice_planar(cube, slice_cfg)
    text = write_gcode_5axis(part, AcTableMachine(), gcode_cfg)
    z_values = sorted(
        {float(m["z"]) for m in _PRINT_LINE.finditer(text) if m["z"] is not None}
    )
    # 10 mm height, 0.5 mm layers, mid-layer offset -> 20 distinct Z values.
    assert len(z_values) == 20
    diffs = np.diff(z_values)
    assert np.allclose(diffs, 0.5, atol=1e-6)
