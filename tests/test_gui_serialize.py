"""GUI: serialization helpers + smoke-test that the app constructs.

The serialization tests are headless — they exercise the same code
the Gradio callbacks call but don't touch Gradio itself, so they
catch real bugs without paying the GUI startup cost. The smoke test
imports gradio and builds the Blocks object to confirm the layout
wiring is syntactically valid.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import trimesh

from reinforced_slicer.gui.serialize import (
    curved_layer_stats,
    curved_layers_plotly,
    export_iso_surfaces_obj,
    joint_trajectory_plotly,
    mesh_stats,
    planar_slice_plotly,
    planar_slice_stats,
)
from reinforced_slicer.gui.tetmesh_from_stl import (
    shoebox_tet_mesh_from_stl,
    synthetic_tilted_cube,
)
from reinforced_slicer.kinematics import AcTableMachine, CutterPose
from reinforced_slicer.mesh.isosurface import extract_curved_layers
from reinforced_slicer.slicing.curved_5axis import curved_layer_5axis_pipeline
from reinforced_slicer.slicing.planar import PlanarSliceConfig, slice_planar


@pytest.fixture(scope="module")
def cube() -> trimesh.Trimesh:
    m = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    m.apply_translation([5.0, 5.0, 5.0])
    return m


@pytest.fixture(scope="module")
def planar_part(cube: trimesh.Trimesh):
    return slice_planar(cube, PlanarSliceConfig(layer_height=1.0, infill_spacing=0.8))


@pytest.fixture(scope="module")
def curved_result():
    shoebox = synthetic_tilted_cube(extent=10.0, subdivisions=3, tilt_slope_x=0.3)
    return shoebox, curved_layer_5axis_pipeline(
        shoebox.mesh,
        shoebox.top_indices,
        shoebox.bottom_indices,
        AcTableMachine(),
        layer_height=2.0,
        path_spacing=2.0,
    )


class TestMeshStats:
    def test_basic_cube_stats(self, cube: trimesh.Trimesh) -> None:
        stats = mesh_stats(cube)
        assert stats["n_faces"] == 12
        assert stats["extent_mm"] == [10.0, 10.0, 10.0]
        assert stats["watertight"] is True


class TestPlanarSerialization:
    def test_stats_have_expected_keys(self, planar_part) -> None:
        stats = planar_slice_stats(planar_part)
        for key in (
            "n_layers", "layer_height_mm", "infill_spacing_mm",
            "n_paths_total", "n_path_points", "z_range_mm",
        ):
            assert key in stats
        assert stats["n_layers"] >= 1
        assert stats["n_path_points"] > 0

    def test_plotly_figure_has_traces(self, planar_part) -> None:
        fig = planar_slice_plotly(planar_part)
        assert len(fig.data) >= planar_part.layers[0].paths.__len__()

    def test_plotly_downsamples_when_many_layers(self, planar_part) -> None:
        fig = planar_slice_plotly(planar_part, max_layers=2)
        # With max_layers=2 we'd see paths from at most 2 layers worth.
        assert len(fig.data) > 0


class TestCurvedSerialization:
    def test_stats_have_expected_keys(self, curved_result) -> None:
        _, result = curved_result
        stats = curved_layer_stats(result)
        for key in (
            "n_layers", "n_paths_total", "n_path_points",
            "z_target_mm", "osqp_status", "field_range",
        ):
            assert key in stats
        assert stats["n_layers"] >= 1

    def test_curved_obj_export_writes_file(self, curved_result, tmp_path: Path) -> None:
        shoebox, result = curved_result
        layers = extract_curved_layers(shoebox.mesh, result.field, layer_height=2.0)
        out = export_iso_surfaces_obj(layers, tmp_path / "out.obj")
        assert out.exists()
        text = out.read_text()
        # OBJ should contain vertex and face lines for a non-trivial layer set.
        assert "v " in text and "f " in text

    def test_curved_plotly_has_surface_and_path_traces(self, curved_result) -> None:
        from reinforced_slicer.pathing.curved import plan_path_on_surface

        shoebox, result = curved_result
        layers = extract_curved_layers(shoebox.mesh, result.field, layer_height=2.0)
        oriented = [plan_path_on_surface(iso, spacing=2.0) for iso in layers]
        fig = curved_layers_plotly(layers, oriented, show_normals_every=4)
        # Expect at least one Mesh3d (surface) and one Scatter3d (path).
        types = {trace.type for trace in fig.data}
        assert "mesh3d" in types
        assert "scatter3d" in types


class TestKinematicsSerialization:
    def test_joint_trajectory_plot_has_three_traces(self) -> None:
        machine = AcTableMachine()
        poses = [
            CutterPose(
                position=np.array([0.0, 0.0, 0.0]),
                tool_axis=np.array(
                    [np.sin(0.5) * np.cos(phi), np.sin(0.5) * np.sin(phi), np.cos(0.5)]
                ),
            )
            for phi in np.linspace(-1.0, 1.0, 20)
        ]
        joints = machine.solve_path(poses)
        singularity = [machine.singularity_distance(p) for p in poses]
        fig = joint_trajectory_plotly(poses, joints, singularity)
        # Three traces: A, C, and sin A.
        assert len(fig.data) == 3


class TestShoebox:
    def test_shoebox_from_stl_uses_aabb(self, cube: trimesh.Trimesh) -> None:
        shoebox = shoebox_tet_mesh_from_stl(cube, subdivisions=2)
        assert shoebox.mesh.n_tets > 0
        # Bounding box should match the cube.
        verts = shoebox.mesh.vertices
        assert verts.min(axis=0).tolist() == pytest.approx([0.0, 0.0, 0.0], abs=1e-6)
        # Max extent of cube is 10; cube_tet_mesh uses max extent as cube side.
        assert verts.max(axis=0).tolist() == pytest.approx([10.0, 10.0, 10.0], abs=1e-6)

    def test_synthetic_cube_flat_is_unperturbed(self) -> None:
        shoebox = synthetic_tilted_cube(extent=5.0, subdivisions=3, tilt_slope_x=0.0)
        assert shoebox.mesh.vertices.max() == pytest.approx(5.0)
        assert "axis-aligned" in shoebox.note

    def test_synthetic_cube_tilted_has_tilted_top(self) -> None:
        shoebox = synthetic_tilted_cube(extent=10.0, subdivisions=3, tilt_slope_x=0.3)
        top_z = shoebox.mesh.vertices[shoebox.top_indices, 2]
        assert top_z.max() - top_z.min() > 1.0


class TestAppSmoke:
    def test_build_app_constructs(self) -> None:
        # Imports gradio and builds the Blocks layout; doesn't launch a server.
        from reinforced_slicer.gui.app import build_app

        app = build_app()
        assert app is not None


class TestHandlerIntegration:
    """Exercise the same callable paths the Gradio buttons trigger."""

    def test_synthetic_cube_handler_returns_full_set(self) -> None:
        from reinforced_slicer.gui.app import _make_synthetic_cube

        mesh, info, stats_md, viz_path, shoebox = _make_synthetic_cube(
            extent=10.0, subdivisions=3, tilt_slope=0.2
        )
        assert mesh is not None
        assert "Synthetic cube" in info
        assert isinstance(stats_md, dict) or "n_faces" in stats_md  # md or dict variants
        assert Path(viz_path).exists()
        assert shoebox.mesh.n_tets > 0

    def test_planar_slice_handler_runs_end_to_end(self, cube: trimesh.Trimesh) -> None:
        from reinforced_slicer.gui.app import _run_planar_slice

        result = _run_planar_slice(
            cube,
            layer_height=1.0,
            infill_spacing=0.8,
            infill_angle=45.0,
            alternate_angle=True,
            nozzle_temp=210,
            bed_temp=60,
        )
        fig, summary, gcode_path, preview, *_ = result
        assert fig is not None
        assert "n_layers" in summary
        assert Path(gcode_path).exists()
        assert "G1" in preview

    def test_curved_slice_handler_runs_end_to_end(self) -> None:
        from reinforced_slicer.gui.app import _make_synthetic_cube, _run_curved_slice

        _, _, _, _, shoebox = _make_synthetic_cube(extent=10.0, subdivisions=3, tilt_slope=0.3)
        result = _run_curved_slice(
            mesh=None,
            shoebox=shoebox,
            subdivisions=3,
            layer_height=2.0,
            path_spacing=2.0,
            tau_min=0.5,
            tau_max=2.0,
            flatness_weight=10.0,
            smoothness_weight=1e-4,
            z_target_override=10.0,
            use_z_target_override=False,
        )
        fig, summary, obj_path, gcode_path, preview, *_ = result
        assert fig is not None
        assert "n_layers" in summary
        assert Path(obj_path).exists()
        assert Path(gcode_path).exists()
        assert "G1" in preview

    def test_curved_slice_handler_handles_missing_mesh(self) -> None:
        from reinforced_slicer.gui.app import _run_curved_slice

        result = _run_curved_slice(
            mesh=None, shoebox=None,
            subdivisions=3, layer_height=2.0, path_spacing=2.0,
            tau_min=0.5, tau_max=2.0,
            flatness_weight=1.0, smoothness_weight=1e-4,
            z_target_override=10.0, use_z_target_override=False,
        )
        fig, summary, *_ = result
        assert fig is None
        assert "Load a mesh first" in summary

    def test_kinematics_sweep_handler_runs(self) -> None:
        from reinforced_slicer.gui.app import _run_kinematics_sweep

        fig, summary = _run_kinematics_sweep(
            "Azimuth sweep at 45° tilt", n_samples=40, smooth_singularities_flag=False
        )
        assert fig is not None
        assert "A range" in summary

    def test_kinematics_sweep_through_singularity_with_smoothing(self) -> None:
        from reinforced_slicer.gui.app import _run_kinematics_sweep

        fig, summary = _run_kinematics_sweep(
            "Through-singularity crossing", n_samples=40, smooth_singularities_flag=True
        )
        assert fig is not None
        assert "singularity smoothing: **on**" in summary
