"""M2a: 2D CurviSlicer QP tests.

Properties we check, listed by what they prove about the solver:

* No-op on a flat input  – the QP recognises there's nothing to do
                            (objective minimum is at h = 0 trivially).
* Parabolic top flattens  – the main use case; deviation from the
                            target line must shrink by a large factor.
* Stretch bounds respected – the OSQP solution honours per-triangle
                            inequality constraints.
* Bottom pin held         – equality constraints work.
* Tight stretch binds     – when bounds are too tight to flatten fully,
                            the constraints become active and the
                            residual flatness error stays bounded.
"""

from __future__ import annotations

import numpy as np
import pytest

from reinforced_slicer.mesh.triangle2d import (
    bottom_row_indices,
    grid_mesh,
    top_row_indices,
)
from reinforced_slicer.slicing.curvi_2d import (
    CurviSlicer2DConfig,
    solve_displacement,
    vertical_stretch,
)


def _parabolic_mesh(x_count: int = 21, y_count: int = 11, width: float = 20.0):
    """Mesh whose top edge is y = 10 + 0.05·(x - 10)² — a shallow parabola."""
    height_fn = lambda x: 10.0 + 0.05 * (x - 10.0) ** 2
    mesh = grid_mesh(x_count, y_count, width, height_fn)
    top = top_row_indices(mesh, x_count, y_count)
    bottom = bottom_row_indices(mesh, x_count, y_count)
    return mesh, top, bottom


def _flat_mesh(x_count: int = 11, y_count: int = 6, width: float = 10.0, height: float = 5.0):
    mesh = grid_mesh(x_count, y_count, width, lambda x: height)
    top = top_row_indices(mesh, x_count, y_count)
    bottom = bottom_row_indices(mesh, x_count, y_count)
    return mesh, top, bottom


class TestNoOp:
    def test_flat_input_gives_near_zero_displacement(self) -> None:
        mesh, top, bottom = _flat_mesh()
        result = solve_displacement(mesh, top, bottom)
        assert np.max(np.abs(result.displacement)) < 1e-5
        # Bottom is pinned exactly.
        assert np.max(np.abs(result.displacement[bottom])) < 1e-9


class TestFlatten:
    def test_parabolic_top_becomes_much_flatter(self) -> None:
        mesh, top, bottom = _parabolic_mesh()
        before_y = mesh.vertices[top, 1]
        before_dev = float(before_y.max() - before_y.min())

        result = solve_displacement(
            mesh,
            top,
            bottom,
            CurviSlicer2DConfig(flatness_weight=10.0, smoothness_weight=1e-4),
        )
        after_y = result.deformed_mesh.vertices[top, 1]
        after_dev = float(after_y.max() - after_y.min())

        # Parabolic top spans ~5 mm before; should collapse by at least 50×.
        assert before_dev > 4.0
        assert after_dev < 0.1, f"top edge still varies by {after_dev:.3f} mm"

    def test_y_target_overrides_default(self) -> None:
        mesh, top, bottom = _parabolic_mesh()
        result = solve_displacement(
            mesh,
            top,
            bottom,
            CurviSlicer2DConfig(flatness_weight=10.0, smoothness_weight=1e-4, y_target=12.0),
        )
        mean_after = float(result.deformed_mesh.vertices[top, 1].mean())
        assert mean_after == pytest.approx(12.0, abs=0.05)


class TestStretchConstraints:
    def test_solution_respects_stretch_bounds(self) -> None:
        mesh, top, bottom = _parabolic_mesh()
        cfg = CurviSlicer2DConfig(tau_min=0.5, tau_max=2.0, flatness_weight=10.0)
        result = solve_displacement(mesh, top, bottom, cfg)
        stretches = vertical_stretch(result.deformed_mesh.__class__(
            vertices=mesh.vertices, triangles=mesh.triangles
        ), result.displacement)
        # OSQP polishes to ~1e-7; allow a small tolerance.
        assert stretches.min() >= cfg.tau_min - 1e-5
        assert stretches.max() <= cfg.tau_max + 1e-5

    def test_tight_bounds_become_active(self) -> None:
        # A taller parabola with tight stretch bounds: the top can't fully
        # flatten because the bounds saturate first. Verify (a) some
        # constraint actually binds, (b) the result is still much flatter
        # than the input even if not perfectly flat.
        mesh = grid_mesh(21, 11, 20.0, lambda x: 5.0 + 0.2 * (x - 10.0) ** 2)
        top = top_row_indices(mesh, 21, 11)
        bottom = bottom_row_indices(mesh, 21, 11)

        before_dev = float(mesh.vertices[top, 1].max() - mesh.vertices[top, 1].min())
        cfg = CurviSlicer2DConfig(
            tau_min=0.7, tau_max=1.5, flatness_weight=10.0, smoothness_weight=1e-5
        )
        result = solve_displacement(mesh, top, bottom, cfg)
        stretches = vertical_stretch(mesh, result.displacement)

        # At least one triangle must hit a bound (within OSQP tolerance).
        slack = 1e-3
        any_bound_active = bool(
            np.any(stretches <= cfg.tau_min + slack)
            or np.any(stretches >= cfg.tau_max - slack)
        )
        assert any_bound_active, "expected at least one stretch bound to be active"

        # Even if not perfectly flat, top must shrink substantially.
        after_dev = float(
            result.deformed_mesh.vertices[top, 1].max()
            - result.deformed_mesh.vertices[top, 1].min()
        )
        assert after_dev < 0.5 * before_dev


class TestPinning:
    def test_bottom_vertices_stay_at_zero_displacement(self) -> None:
        mesh, top, bottom = _parabolic_mesh()
        result = solve_displacement(mesh, top, bottom)
        assert np.max(np.abs(result.displacement[bottom])) < 1e-6
        # The original bottom y was 0; the deformed bottom y must also be 0.
        assert np.max(np.abs(result.deformed_mesh.vertices[bottom, 1])) < 1e-6


class TestValidation:
    def test_overlapping_top_and_pin_rejected(self) -> None:
        mesh, top, bottom = _flat_mesh()
        overlap = np.concatenate([top, [bottom[0]], [top[0]]])  # top[0] in both
        with pytest.raises(ValueError, match="disjoint"):
            solve_displacement(mesh, overlap, top)

    def test_bad_tau_range_rejected(self) -> None:
        mesh, top, bottom = _flat_mesh()
        with pytest.raises(ValueError, match="tau_min"):
            solve_displacement(
                mesh, top, bottom, CurviSlicer2DConfig(tau_min=2.0, tau_max=1.0)
            )
