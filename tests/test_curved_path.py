"""M2c.3: paths on a curved iso-surface."""

from __future__ import annotations

import numpy as np
import pytest

from reinforced_slicer.mesh.isosurface import extract_isosurface
from reinforced_slicer.mesh.tet import cube_tet_mesh
from reinforced_slicer.pathing.curved import plan_path_on_surface


def _flat_iso(level: float = 0.5):
    mesh = cube_tet_mesh(extent=1.0, subdivisions=4)
    field = mesh.vertices[:, 2].astype(float)
    return extract_isosurface(mesh, field, level=level)


def _tilted_iso(slope_x: float = 0.3, level: float = 0.5):
    mesh = cube_tet_mesh(extent=1.0, subdivisions=4)
    field = (mesh.vertices[:, 2] + slope_x * mesh.vertices[:, 0]).astype(float)
    return extract_isosurface(mesh, field, level=level)


class TestFlatSurface:
    def test_path_lies_on_iso_plane(self) -> None:
        iso = _flat_iso(level=0.55)  # off-vertex so all iso pts are interior
        paths = plan_path_on_surface(iso, spacing=0.2)
        assert paths, "expected at least one zigzag stroke"
        pts = np.vstack([np.stack([p.position for p in path]) for path in paths])
        assert pts[:, 2] == pytest.approx(0.55, abs=1e-8)

    def test_tool_axis_is_vertical_for_flat_surface(self) -> None:
        iso = _flat_iso(level=0.55)
        paths = plan_path_on_surface(iso, spacing=0.2)
        for path in paths:
            for pose in path:
                assert pose.tool_axis == pytest.approx([0.0, 0.0, 1.0], abs=1e-6)


class TestTiltedSurface:
    def test_path_lies_on_tilted_iso_plane(self) -> None:
        # iso of (z + 0.3 x) at 0.5 -> z = 0.5 - 0.3 x.
        iso = _tilted_iso(slope_x=0.3, level=0.55)
        paths = plan_path_on_surface(iso, spacing=0.2)
        assert paths
        pts = np.vstack([np.stack([p.position for p in path]) for path in paths])
        residuals = pts[:, 2] + 0.3 * pts[:, 0] - 0.55
        assert np.max(np.abs(residuals)) < 1e-6

    def test_tool_axis_matches_iso_normal(self) -> None:
        iso = _tilted_iso(slope_x=0.3, level=0.55)
        paths = plan_path_on_surface(iso, spacing=0.2)
        expected = np.array([0.3, 0.0, 1.0]) / np.sqrt(1.0 + 0.09)
        for path in paths:
            for pose in path:
                assert pose.tool_axis == pytest.approx(expected, abs=1e-5)


class TestCoverage:
    def test_paths_cover_the_footprint(self) -> None:
        iso = _flat_iso(level=0.55)
        paths = plan_path_on_surface(iso, spacing=0.1)
        pts = np.vstack([np.stack([p.position for p in path]) for path in paths])
        # XY extent should span most of the unit square footprint.
        assert pts[:, 0].min() < 0.05
        assert pts[:, 0].max() > 0.95
        assert pts[:, 1].min() < 0.05
        assert pts[:, 1].max() > 0.95

    def test_finer_spacing_yields_more_points(self) -> None:
        iso = _flat_iso(level=0.55)
        coarse = plan_path_on_surface(iso, spacing=0.4)
        fine = plan_path_on_surface(iso, spacing=0.1)
        n_coarse = sum(len(p) for p in coarse)
        n_fine = sum(len(p) for p in fine)
        assert n_fine > 3 * n_coarse


class TestEdgeCases:
    def test_empty_iso_returns_empty(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        field = mesh.vertices[:, 2].astype(float)
        iso = extract_isosurface(mesh, field, level=10.0)  # above range
        paths = plan_path_on_surface(iso, spacing=0.2)
        assert paths == []
