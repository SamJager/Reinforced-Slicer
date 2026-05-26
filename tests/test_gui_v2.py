"""GUI v2 features: G-code parser, layer-range filtering, mesh quality."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import trimesh

from reinforced_slicer.gui.gcode_stats import GcodeStats, parse_gcode_stats
from reinforced_slicer.gui.serialize import (
    curved_layers_plotly,
    mesh_quality_warning,
    mesh_stats,
    planar_slice_plotly,
)
from reinforced_slicer.mesh.isosurface import extract_curved_layers
from reinforced_slicer.mesh.tet import cube_tet_mesh
from reinforced_slicer.pathing.curved import plan_path_on_surface
from reinforced_slicer.postproc.gcode import GcodeConfig, write_gcode
from reinforced_slicer.slicing.planar import PlanarSliceConfig, slice_planar


@pytest.fixture(scope="module")
def cube() -> trimesh.Trimesh:
    m = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    m.apply_translation([5.0, 5.0, 5.0])
    return m


@pytest.fixture(scope="module")
def cube_gcode(cube: trimesh.Trimesh, tmp_path_factory: pytest.TempPathFactory) -> tuple[str, Path]:
    part = slice_planar(cube, PlanarSliceConfig(layer_height=1.0, infill_spacing=0.8))
    out = tmp_path_factory.mktemp("gcode") / "cube.gcode"
    write_gcode(part, out, GcodeConfig())
    return out.read_text(), out


class TestGcodeStatsParser:
    def test_parser_finds_print_and_travel_moves(self, cube_gcode: tuple[str, Path]) -> None:
        text, _ = cube_gcode
        stats = parse_gcode_stats(text)
        assert isinstance(stats, GcodeStats)
        assert stats.n_print_moves > 0
        assert stats.n_travel_moves > 0
        assert stats.print_distance_mm > 0
        assert stats.travel_distance_mm > 0

    def test_extrusion_total_matches_last_e_command(self, cube_gcode: tuple[str, Path]) -> None:
        text, _ = cube_gcode
        stats = parse_gcode_stats(text)
        # Sum of E deltas should be ~ the final positive E coordinate.
        assert stats.total_extrusion_mm > 0
        assert stats.total_extrusion_mm < 1000  # sanity: 10mm cube doesn't need a km of filament

    def test_time_estimate_is_positive_and_reasonable(self, cube_gcode: tuple[str, Path]) -> None:
        text, _ = cube_gcode
        stats = parse_gcode_stats(text)
        assert stats.total_time_s > 0
        # 10mm cube with 1mm layers shouldn't take hours.
        assert stats.total_time_s < 600

    def test_bounding_box_matches_cube(self, cube_gcode: tuple[str, Path]) -> None:
        text, _ = cube_gcode
        stats = parse_gcode_stats(text)
        bbox_min = np.array(stats.bounding_box_min_mm)
        bbox_max = np.array(stats.bounding_box_max_mm)
        # Cube is in [0, 10]^3.
        assert np.all(bbox_min >= -0.1)
        assert np.all(bbox_max <= 10.1)
        assert np.all(bbox_max - bbox_min > 5.0)

    def test_to_dict_has_human_readable_time(self, cube_gcode: tuple[str, Path]) -> None:
        text, _ = cube_gcode
        d = parse_gcode_stats(text).to_dict()
        assert "total_time" in d
        assert "filament_used_m" in d
        assert isinstance(d["total_time"], str)

    def test_handles_empty_gcode(self) -> None:
        stats = parse_gcode_stats("; nothing here\n")
        assert stats.total_time_s == 0
        assert stats.n_print_moves == 0
        # Empty BBox falls back to origin to keep downstream code safe.
        assert stats.bounding_box_min_mm == (0.0, 0.0, 0.0)

    def test_relative_extrusion_handled(self) -> None:
        gcode = """
M83
G1 X10 Y0 E1 F1800
G1 X20 Y0 E1 F1800
"""
        stats = parse_gcode_stats(gcode)
        # Two relative E moves of 1 mm each.
        assert stats.total_extrusion_mm == pytest.approx(2.0)
        assert stats.print_distance_mm == pytest.approx(20.0)


class TestLayerRangeFilter:
    def test_planar_full_range_matches_no_filter(self, cube: trimesh.Trimesh) -> None:
        part = slice_planar(cube, PlanarSliceConfig(layer_height=1.0, infill_spacing=0.8))
        fig_all = planar_slice_plotly(part)
        fig_full = planar_slice_plotly(part, layer_range=(0, len(part.layers) - 1))
        assert len(fig_all.data) == len(fig_full.data)

    def test_planar_single_layer_filter_shows_fewer(self, cube: trimesh.Trimesh) -> None:
        part = slice_planar(cube, PlanarSliceConfig(layer_height=1.0, infill_spacing=0.8))
        fig_one = planar_slice_plotly(part, layer_range=(0, 0))
        fig_all = planar_slice_plotly(part)
        assert len(fig_one.data) < len(fig_all.data)

    def test_curved_layer_filter_skips_layers(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=3)
        field = mesh.vertices[:, 2].astype(float)
        layers = extract_curved_layers(mesh, field, layer_height=0.25)
        oriented = [plan_path_on_surface(iso, spacing=0.3) for iso in layers]
        fig_all = curved_layers_plotly(layers, oriented)
        fig_one = curved_layers_plotly(layers, oriented, layer_range=(0, 0))
        assert len(fig_one.data) < len(fig_all.data)


class TestMeshQuality:
    def test_clean_cube_is_slicing_ready(self, cube: trimesh.Trimesh) -> None:
        stats = mesh_stats(cube)
        assert stats["watertight"] is True
        assert stats["slicing_ready"] is True
        assert stats["n_open_edges"] == 0
        assert mesh_quality_warning(stats) is None

    def test_open_cube_has_open_edges(self) -> None:
        # Remove one face to break watertightness.
        cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
        broken = trimesh.Trimesh(vertices=cube.vertices, faces=cube.faces[:-2])
        stats = mesh_stats(broken)
        assert stats["watertight"] is False
        assert stats["n_open_edges"] > 0
        assert stats["slicing_ready"] is False
        warning = mesh_quality_warning(stats)
        assert warning is not None
        assert "Not watertight" in warning

    def test_warning_lists_each_issue(self) -> None:
        bad = {
            "watertight": False,
            "winding_consistent": False,
            "n_open_edges": 4,
            "n_non_manifold_edges": 0,
            "n_broken_faces": 2,
        }
        warning = mesh_quality_warning(bad)
        assert warning is not None
        assert "Not watertight" in warning
        assert "Winding inconsistent" in warning
        assert "broken" in warning


class TestUpdatedHandlerShape:
    def test_run_planar_slice_returns_state_and_sliders(self, cube: trimesh.Trimesh) -> None:
        from reinforced_slicer.gui.app import _run_planar_slice

        result = _run_planar_slice(
            cube, layer_height=1.0, infill_spacing=0.8, infill_angle=0.0,
            alternate_angle=True, nozzle_temp=210, bed_temp=60,
        )
        # New shape: (fig, summary, gcode_path, preview, part_state, lo_update, hi_update)
        assert len(result) == 7
        fig, summary, gcode_path, preview, state, lo_u, hi_u = result
        assert fig is not None
        assert state is not None
        assert "Print stats" in summary

    def test_run_curved_slice_returns_state_and_sliders(self) -> None:
        from reinforced_slicer.gui.app import _make_synthetic_cube, _run_curved_slice

        _, _, _, _, shoebox = _make_synthetic_cube(extent=10.0, subdivisions=3, tilt_slope=0.3)
        result = _run_curved_slice(
            mesh=None, shoebox=shoebox, subdivisions=3,
            layer_height=2.0, path_spacing=2.0,
            tau_min=0.5, tau_max=2.0,
            flatness_weight=10.0, smoothness_weight=1e-4,
            z_target_override=10.0, use_z_target_override=False,
        )
        # New shape: 8 elements
        assert len(result) == 8
        fig, summary, obj_path, gcode_path, preview, state, lo_u, hi_u = result
        assert fig is not None
        assert state is not None and "iso" in state and "oriented" in state
        assert "Print stats" in summary

    def test_replot_planar_with_no_state_returns_none(self) -> None:
        from reinforced_slicer.gui.app import _replot_planar

        assert _replot_planar(None, 0.0, 100.0) is None

    def test_replot_curved_with_no_state_returns_none(self) -> None:
        from reinforced_slicer.gui.app import _replot_curved

        assert _replot_curved(None, 0.0, 100.0) is None
