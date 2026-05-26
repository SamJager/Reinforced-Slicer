"""Tests for the 3-axis vs 5-axis comparison feature."""

from __future__ import annotations

from pathlib import Path

import pytest
import trimesh

from reinforced_slicer.gui.serialize import (
    comparison_summary_markdown,
    side_by_side_plotly,
)
from reinforced_slicer.mesh.isosurface import extract_curved_layers
from reinforced_slicer.mesh.tet import cube_tet_mesh
from reinforced_slicer.pathing.curved import plan_path_on_surface
from reinforced_slicer.slicing.planar import PlanarSliceConfig, slice_planar


@pytest.fixture(scope="module")
def cube() -> trimesh.Trimesh:
    m = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    m.apply_translation([5.0, 5.0, 5.0])
    return m


class TestSideBySidePlot:
    def test_plot_has_traces_in_both_subplots(self, cube: trimesh.Trimesh) -> None:
        part = slice_planar(cube, PlanarSliceConfig(layer_height=1.0, infill_spacing=0.8))
        tet = cube_tet_mesh(extent=10.0, subdivisions=3)
        field = tet.vertices[:, 2].astype(float)
        iso = extract_curved_layers(tet, field, layer_height=2.5)
        oriented = [plan_path_on_surface(s, spacing=1.5) for s in iso]
        fig = side_by_side_plotly(part, iso, oriented, show_normals_every=8)

        # Need at least one trace in subplot 1 and one in subplot 2.
        scene_xrefs = {trace.scene for trace in fig.data if hasattr(trace, "scene")}
        # plotly subplot scenes are named "scene" and "scene2"
        assert "scene" in scene_xrefs and "scene2" in scene_xrefs


class TestComparisonSummary:
    def test_summary_markdown_includes_both_columns(self) -> None:
        planar_geo = {"n_layers": 20, "n_path_points": 240}
        curved_geo = {"n_layers": 5, "n_path_points": 60}
        planar_print = {
            "print_time": "1.2 min", "total_time": "1.5 min",
            "print_distance_mm": 2400, "travel_distance_mm": 600,
            "filament_used_m": 0.5,
        }
        curved_print = {
            "print_time": "0.4 min", "total_time": "0.6 min",
            "print_distance_mm": 700, "travel_distance_mm": 180,
            "filament_used_m": 0.15,
        }
        md = comparison_summary_markdown(planar_geo, curved_geo, planar_print, curved_print)
        assert "| Metric |" in md
        assert "3-axis planar" in md
        assert "5-axis curved" in md
        assert "Print time" in md
        assert "1.2 min" in md and "0.4 min" in md


class TestComparisonHandler:
    def test_handler_runs_with_synthetic_cube(self) -> None:
        from reinforced_slicer.gui.app import _make_synthetic_cube, _run_comparison

        mesh, _, _, _, shoebox = _make_synthetic_cube(
            extent=10.0, subdivisions=3, tilt_slope=0.0
        )
        fig, summary, planar_path, curved_path = _run_comparison(
            mesh=mesh, shoebox=shoebox, subdivisions=3,
            planar_layer_h=0.5, planar_spacing=0.6,
            curved_layer_h=2.0, curved_spacing=1.5,
            arrow_density=16,
        )
        assert fig is not None
        assert "3-axis planar" in summary
        assert Path(planar_path).exists()
        assert Path(curved_path).exists()

    def test_handler_rejects_missing_mesh(self) -> None:
        from reinforced_slicer.gui.app import _run_comparison

        fig, summary, p, c = _run_comparison(
            mesh=None, shoebox=None, subdivisions=3,
            planar_layer_h=0.5, planar_spacing=0.6,
            curved_layer_h=2.0, curved_spacing=1.5,
            arrow_density=16,
        )
        assert fig is None
        assert "Load a mesh first" in summary
