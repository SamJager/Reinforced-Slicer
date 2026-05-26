"""M4: direction field, stripe scalar field, iso-curves, fiber paths.

Property coverage:

* Direction field projects onto the tangent plane (orthogonal to normal).
* On a flat horizontal surface with fiber direction = +X, the stripe
  scalar field equals y (up to constant), so iso-lines are horizontal
  lines in world coordinates.
* On a tilted iso-surface (z + 0.3·x = const), the stripe paths still
  follow the requested fiber direction projected onto the surface.
* Iso-curve extraction returns ordered polylines whose points all lie
  on the requested iso-level.
* End-to-end ``plan_fiber_path_on_surface`` produces enough paths to
  cover the surface at the requested spacing.
"""

from __future__ import annotations

import numpy as np
import pytest

from reinforced_slicer.mesh.isosurface import extract_isosurface
from reinforced_slicer.mesh.tet import cube_tet_mesh
from reinforced_slicer.pathing.direction_field import (
    direction_field_from_xy_angle,
    project_target_direction,
)
from reinforced_slicer.pathing.fiber import plan_fiber_path_on_surface
from reinforced_slicer.pathing.iso_curves import extract_iso_curves
from reinforced_slicer.pathing.stripe_field import (
    estimate_field_spacing,
    stripe_scalar_field,
)


def _flat_iso(level: float = 0.55):
    mesh = cube_tet_mesh(extent=1.0, subdivisions=4)
    field = mesh.vertices[:, 2].astype(float)
    return extract_isosurface(mesh, field, level=level)


def _tilted_iso(slope_x: float = 0.3, level: float = 0.55):
    mesh = cube_tet_mesh(extent=1.0, subdivisions=4)
    field = (mesh.vertices[:, 2] + slope_x * mesh.vertices[:, 0]).astype(float)
    return extract_isosurface(mesh, field, level=level)


class TestDirectionField:
    def test_field_lies_in_tangent_plane(self) -> None:
        iso = _flat_iso()
        field = direction_field_from_xy_angle(iso, angle_deg=30.0)
        # vectors should be unit and orthogonal to the surface normals.
        norms = np.linalg.norm(field.vectors, axis=1)
        assert norms == pytest.approx(np.ones_like(norms), abs=1e-6)
        dots = np.einsum("ij,ij->i", field.vectors, iso.normals)
        assert np.max(np.abs(dots)) < 1e-6

    def test_target_xy_direction_recovered_on_flat_surface(self) -> None:
        # Flat horizontal surface: tangent plane is XY, so the field
        # equals the requested XY direction exactly.
        iso = _flat_iso()
        field = direction_field_from_xy_angle(iso, angle_deg=0.0)
        expected = np.array([1.0, 0.0, 0.0])
        for v in field.vectors:
            assert v == pytest.approx(expected, abs=1e-6)

    def test_target_along_normal_falls_back_gracefully(self) -> None:
        # Flat horizontal surface, target = +Z (parallel to normal).
        # Projection is zero; code should pick a tangent fallback.
        iso = _flat_iso()
        field = project_target_direction(iso, np.array([0.0, 0.0, 1.0]))
        # Still must produce unit tangent vectors orthogonal to normal.
        norms = np.linalg.norm(field.vectors, axis=1)
        assert norms == pytest.approx(np.ones_like(norms), abs=1e-6)
        dots = np.einsum("ij,ij->i", field.vectors, iso.normals)
        assert np.max(np.abs(dots)) < 1e-6


class TestStripeField:
    def test_flat_surface_stripe_field_is_linear_in_y(self) -> None:
        # On a flat horizontal slice with fiber direction +X, the
        # stripe scalar field should satisfy ∇φ ≈ (0, 1, 0), i.e. φ ≈ y.
        iso = _flat_iso(level=0.55)
        field = direction_field_from_xy_angle(iso, angle_deg=0.0)
        phi = stripe_scalar_field(field)
        # Linear regression: phi vs y, expecting slope ≈ 1.
        y = iso.vertices[:, 1]
        # phi = a*y + b (with b absorbing the vertex-0 pin)
        slope = float(np.polyfit(y, phi, 1)[0])
        assert slope == pytest.approx(1.0, abs=0.05)

    def test_rate_per_mm_is_close_to_one_for_unit_stripe_field(self) -> None:
        iso = _flat_iso(level=0.55)
        field = direction_field_from_xy_angle(iso, angle_deg=0.0)
        phi = stripe_scalar_field(field)
        rate = estimate_field_spacing(field, phi)
        assert rate == pytest.approx(1.0, abs=0.1)


class TestIsoCurves:
    def test_horizontal_iso_lines_match_constant_y(self) -> None:
        iso = _flat_iso(level=0.55)
        # Use y as the scalar field directly.
        y_field = iso.vertices[:, 1].astype(float)
        curves = extract_iso_curves(iso, y_field, level=0.5)
        assert curves, "expected at least one iso-curve crossing y=0.5"
        for curve in curves:
            # All points should sit on y=0.5 (within interpolation tolerance).
            assert np.max(np.abs(curve.points[:, 1] - 0.5)) < 1e-9

    def test_iso_curves_have_unit_normals(self) -> None:
        iso = _flat_iso(level=0.55)
        y_field = iso.vertices[:, 1].astype(float)
        curves = extract_iso_curves(iso, y_field, level=0.5)
        for curve in curves:
            norms = np.linalg.norm(curve.normals, axis=1)
            assert norms == pytest.approx(np.ones_like(norms), abs=1e-6)


class TestPlanFiberPath:
    def test_paths_cover_flat_surface(self) -> None:
        iso = _flat_iso(level=0.55)
        paths = plan_fiber_path_on_surface(iso, spacing=0.15, fiber_angle_deg=0.0)
        assert len(paths) >= 3, f"expected several stripe paths, got {len(paths)}"
        all_pts = np.vstack([np.array([p.position for p in path]) for path in paths])
        # X extent should cover most of the unit square; Y spans the stripe set.
        assert all_pts[:, 0].max() - all_pts[:, 0].min() > 0.7
        assert all_pts[:, 1].max() - all_pts[:, 1].min() > 0.5

    def test_fiber_angle_orients_paths(self) -> None:
        # Fiber along +Y -> stripes are horizontal in Y, vary in X.
        iso = _flat_iso(level=0.55)
        paths_y = plan_fiber_path_on_surface(iso, spacing=0.2, fiber_angle_deg=90.0)
        # Average path direction should be ~ +Y.
        for path in paths_y:
            if len(path) < 2:
                continue
            pts = np.array([p.position for p in path])
            # Path tangent: end minus start.
            tangent = pts[-1] - pts[0]
            tangent_norm = float(np.linalg.norm(tangent))
            if tangent_norm > 0.3:  # only check non-trivial paths
                unit = tangent / tangent_norm
                # |unit · +Y| should dominate over |unit · +X|.
                assert abs(unit[1]) > abs(unit[0]) - 0.1

    def test_tool_axes_lie_on_tilted_surface_normal(self) -> None:
        iso = _tilted_iso(slope_x=0.3, level=0.55)
        paths = plan_fiber_path_on_surface(iso, spacing=0.2, fiber_angle_deg=0.0)
        expected = np.array([0.3, 0.0, 1.0]) / np.sqrt(1.0 + 0.09)
        for path in paths:
            for pose in path:
                assert pose.tool_axis == pytest.approx(expected, abs=1e-5)

    def test_empty_iso_returns_empty(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        f = mesh.vertices[:, 2].astype(float)
        iso = extract_isosurface(mesh, f, level=10.0)
        assert plan_fiber_path_on_surface(iso, spacing=0.2) == []


class TestFiberStrategyEndToEnd:
    def test_pipeline_with_fiber_strategy_produces_gcode(self) -> None:
        from reinforced_slicer.kinematics import AcTableMachine
        from reinforced_slicer.mesh.tet import (
            bottom_face_indices,
            cube_tet_mesh,
            top_face_indices,
        )
        from reinforced_slicer.slicing.curved_5axis import curved_layer_5axis_pipeline

        s = 4
        mesh = cube_tet_mesh(extent=10.0, subdivisions=s)
        result = curved_layer_5axis_pipeline(
            mesh,
            top_face_indices(s),
            bottom_face_indices(s),
            AcTableMachine(),
            layer_height=2.0,
            path_spacing=1.5,
            path_strategy="fiber",
            fiber_angle_deg=30.0,
            alternate_infill_angle=False,
        )
        assert result.n_paths > 0
        assert "G1" in result.gcode

    def test_unknown_strategy_rejected(self) -> None:
        from reinforced_slicer.kinematics import AcTableMachine
        from reinforced_slicer.mesh.tet import (
            bottom_face_indices,
            cube_tet_mesh,
            top_face_indices,
        )
        from reinforced_slicer.slicing.curved_5axis import curved_layer_5axis_pipeline

        s = 3
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        with pytest.raises(ValueError, match="path_strategy"):
            curved_layer_5axis_pipeline(
                mesh,
                top_face_indices(s),
                bottom_face_indices(s),
                AcTableMachine(),
                layer_height=0.25,
                path_strategy="bogus",
            )

    def test_gui_handler_runs_with_fiber_strategy(self) -> None:
        from reinforced_slicer.gui.app import _make_synthetic_cube, _run_curved_slice

        _, _, _, _, shoebox = _make_synthetic_cube(extent=10.0, subdivisions=3, tilt_slope=0.0)
        result = _run_curved_slice(
            mesh=None, shoebox=shoebox, subdivisions=3,
            layer_height=2.0, path_spacing=1.5,
            tau_min=0.5, tau_max=2.0,
            flatness_weight=10.0, smoothness_weight=1e-4,
            z_target_override=10.0, use_z_target_override=False,
            backend="shoebox",
            path_strategy="fiber",
            fiber_angle_deg=45.0,
        )
        fig, summary, *_ = result
        assert fig is not None
        assert "n_layers" in summary
