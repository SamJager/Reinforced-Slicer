"""M2c.1: 3D CurviSlicer QP tests.

Property coverage mirrors test_curvi_2d:

* Flat input is a no-op.
* z_target shifts the top face uniformly.
* Stretch bounds are always respected.
* Bottom face stays pinned at h = 0.
* A tilted-top cube flattens its top face substantially.
"""

from __future__ import annotations

import numpy as np
import pytest

from reinforced_slicer.mesh.tet import (
    TetMesh,
    bottom_face_indices,
    cube_tet_mesh,
    top_face_indices,
)
from reinforced_slicer.slicing.curvi_3d import (
    CurviSlicer3DConfig,
    solve_displacement_3d,
    vertical_stretch_3d,
)


def _tilted_top_cube(s: int = 3, tilt_slope: float = 0.3) -> TetMesh:
    """A cube_tet_mesh whose top-face vertex z values are tilted along +x."""
    mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
    top = top_face_indices(s)
    perturbed = mesh.vertices.copy()
    # Shift top vertices' z by a linear ramp in x: z' = 1 + tilt_slope * x.
    perturbed[top, 2] = 1.0 + tilt_slope * perturbed[top, 0]
    # Smoothly interpolate the interior columns so the mesh stays well-formed
    # (each column's z is linear from 0 at the bottom to the perturbed top).
    n = s + 1
    for i in range(n):
        for j in range(n):
            top_idx = i + j * n + (n * n * s)
            new_top_z = perturbed[top_idx, 2]
            for k in range(n):
                idx = i + j * n + k * n * n
                perturbed[idx, 2] = (k / s) * new_top_z
    return TetMesh(vertices=perturbed, tets=mesh.tets)


class TestNoOp:
    def test_flat_input_gives_near_zero_displacement(self) -> None:
        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        result = solve_displacement_3d(mesh, top_face_indices(s), bottom_face_indices(s))
        assert np.max(np.abs(result.displacement)) < 1e-5


class TestTargetShift:
    def test_uniform_target_shifts_top_uniformly(self) -> None:
        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        top = top_face_indices(s)
        # Top is at z=1; ask for z=1.2 (within stretch bounds: 20% over unit
        # height is well inside [0.5, 2.0]).
        result = solve_displacement_3d(
            mesh,
            top,
            bottom_face_indices(s),
            CurviSlicer3DConfig(flatness_weight=10.0, z_target=1.2),
        )
        top_z = result.deformed_mesh.vertices[top, 2]
        # Top vertices should all be ≈ 1.2.
        assert top_z.max() - top_z.min() < 1e-3
        assert top_z.mean() == pytest.approx(1.2, abs=5e-3)


class TestFlatten:
    def test_tilted_top_becomes_much_flatter(self) -> None:
        s = 4
        mesh = _tilted_top_cube(s=s, tilt_slope=0.3)
        top = top_face_indices(s)
        before_z = mesh.vertices[top, 2]
        before_dev = float(before_z.max() - before_z.min())
        assert before_dev > 0.2  # sanity: the tilt is real

        result = solve_displacement_3d(
            mesh,
            top,
            bottom_face_indices(s),
            CurviSlicer3DConfig(flatness_weight=10.0, smoothness_weight=1e-4),
        )
        after_z = result.deformed_mesh.vertices[top, 2]
        after_dev = float(after_z.max() - after_z.min())
        assert after_dev < 0.05, f"top still varies by {after_dev:.3f}"


class TestStretchConstraints:
    def test_solution_respects_stretch_bounds(self) -> None:
        s = 3
        mesh = _tilted_top_cube(s=s, tilt_slope=0.3)
        cfg = CurviSlicer3DConfig(tau_min=0.5, tau_max=2.0, flatness_weight=10.0)
        result = solve_displacement_3d(
            mesh, top_face_indices(s), bottom_face_indices(s), cfg
        )
        # Stretch must be evaluated on the ORIGINAL mesh geometry (the QP
        # constraint is on the linear operator built from undeformed shapes).
        stretches = vertical_stretch_3d(mesh, result.displacement)
        slack = 1e-4
        assert stretches.min() >= cfg.tau_min - slack
        assert stretches.max() <= cfg.tau_max + slack


class TestPinning:
    def test_bottom_face_stays_at_zero_displacement(self) -> None:
        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        bottom = bottom_face_indices(s)
        result = solve_displacement_3d(
            mesh,
            top_face_indices(s),
            bottom,
            CurviSlicer3DConfig(z_target=1.3),
        )
        assert np.max(np.abs(result.displacement[bottom])) < 1e-6


class TestValidation:
    def test_overlapping_top_and_pin_rejected(self) -> None:
        s = 2
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        top = top_face_indices(s)
        bottom = bottom_face_indices(s)
        overlap = np.concatenate([top, [bottom[0]]])
        with pytest.raises(ValueError, match="disjoint"):
            solve_displacement_3d(mesh, overlap, np.concatenate([bottom, [top[0]]]))

    def test_bad_tau_range_rejected(self) -> None:
        s = 2
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        with pytest.raises(ValueError, match="tau_min"):
            solve_displacement_3d(
                mesh,
                top_face_indices(s),
                bottom_face_indices(s),
                CurviSlicer3DConfig(tau_min=2.0, tau_max=1.0),
            )
