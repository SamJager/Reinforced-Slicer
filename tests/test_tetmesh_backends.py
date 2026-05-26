"""Tests for the real tet-meshing backends (gmsh) + the shoebox fallback.

The gmsh tests are conditionally skipped if gmsh isn't installed, so the
suite stays green on machines without the [tet] extra. The shoebox path
must always work — it's the licence-clean fallback.
"""

from __future__ import annotations

import numpy as np
import pytest
import trimesh

from reinforced_slicer.mesh.tetmesh_backends import (
    _boundary_triangles,
    _classify_surface,
    available_backends,
    tetrahedralize_surface,
)
from reinforced_slicer.mesh.tet import TetMesh, cube_tet_mesh, tet_volume

GMSH_AVAILABLE = "gmsh" in available_backends()


@pytest.fixture
def unit_cube_stl() -> trimesh.Trimesh:
    m = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    m.apply_translation([0.5, 0.5, 0.5])
    return m


@pytest.fixture
def sphere_stl() -> trimesh.Trimesh:
    return trimesh.creation.icosphere(subdivisions=2, radius=1.0)


class TestShoeboxFallback:
    def test_shoebox_volume_matches_aabb(self, unit_cube_stl: trimesh.Trimesh) -> None:
        result = tetrahedralize_surface(unit_cube_stl, backend="shoebox")
        assert result.backend == "shoebox"
        total = sum(
            tet_volume(*[result.mesh.vertices[v] for v in tet]) for tet in result.mesh.tets
        )
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_shoebox_top_bottom_classification(self, unit_cube_stl: trimesh.Trimesh) -> None:
        result = tetrahedralize_surface(unit_cube_stl, backend="shoebox")
        # Top vertices should all have z near 1, bottom near 0.
        assert np.all(result.mesh.vertices[result.top_indices, 2] == pytest.approx(1.0, abs=1e-6))
        assert np.all(result.mesh.vertices[result.bottom_indices, 2] == pytest.approx(0.0, abs=1e-6))
        assert np.intersect1d(result.top_indices, result.bottom_indices).size == 0

    def test_shoebox_is_surface_vertex_flag(self, unit_cube_stl: trimesh.Trimesh) -> None:
        result = tetrahedralize_surface(unit_cube_stl, backend="shoebox")
        # Subdivisions = 4 -> 5^3 = 125 vertices, surface = 5^3 - 3^3 = 98.
        assert result.is_surface_vertex.sum() == 98


class TestBoundaryFaceDetection:
    def test_cube_has_correct_boundary_face_count(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        faces = _boundary_triangles(mesh)
        # 6 cube faces, each subdivided into 2x2 quads -> 4 quads per face -> 8 triangles per face -> 48 total.
        assert len(faces) == 48

    def test_classify_top_bottom_uses_z_extremes(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        is_surface, top, bottom = _classify_surface(mesh)
        # Each z-face has 9 vertices for subdivisions=2.
        assert len(top) == 9
        assert len(bottom) == 9


@pytest.mark.skipif(not GMSH_AVAILABLE, reason="gmsh backend not installed")
class TestGmshBackend:
    def test_gmsh_cube_volume_matches(self, unit_cube_stl: trimesh.Trimesh) -> None:
        result = tetrahedralize_surface(
            unit_cube_stl, backend="gmsh", target_size_mm=0.3
        )
        assert result.backend == "gmsh"
        assert result.mesh.n_tets > 0
        total = sum(
            tet_volume(*[result.mesh.vertices[v] for v in tet]) for tet in result.mesh.tets
        )
        # Real meshing should match the cube volume tightly.
        assert total == pytest.approx(1.0, abs=1e-3)

    def test_gmsh_sphere_produces_nonzero_volume(self, sphere_stl: trimesh.Trimesh) -> None:
        result = tetrahedralize_surface(sphere_stl, backend="gmsh", target_size_mm=0.25)
        assert result.backend == "gmsh"
        total = sum(
            tet_volume(*[result.mesh.vertices[v] for v in tet]) for tet in result.mesh.tets
        )
        # Sphere of radius 1 has volume 4π/3 ≈ 4.189. Allow ~5% slack for tessellation.
        assert 3.8 < total < 4.3

    def test_gmsh_cube_top_bottom_match_cube_faces(self, unit_cube_stl: trimesh.Trimesh) -> None:
        result = tetrahedralize_surface(
            unit_cube_stl, backend="gmsh", target_size_mm=0.4
        )
        # All top indices should sit near z=1, all bottom near z=0.
        top_z = result.mesh.vertices[result.top_indices, 2]
        bottom_z = result.mesh.vertices[result.bottom_indices, 2]
        assert top_z.size > 0
        assert bottom_z.size > 0
        assert top_z.max() == pytest.approx(1.0, abs=0.01)
        assert top_z.min() >= 0.99
        assert bottom_z.max() <= 0.01
        assert bottom_z.min() == pytest.approx(0.0, abs=0.01)


@pytest.mark.skipif(not GMSH_AVAILABLE, reason="gmsh backend not installed")
class TestEndToEndWithGmsh:
    def test_curved_pipeline_runs_on_real_tet_mesh(self, unit_cube_stl) -> None:
        """Tetrahedralise a real STL with gmsh, then run the curved-layer
        pipeline through to G-code emission. This is the integration that
        the GUI users hit when they upload an STL with the [tet] extra."""
        from reinforced_slicer.kinematics import AcTableMachine
        from reinforced_slicer.slicing.curved_5axis import (
            curved_layer_5axis_pipeline,
        )

        tet_result = tetrahedralize_surface(
            unit_cube_stl, backend="gmsh", target_size_mm=0.3
        )
        result = curved_layer_5axis_pipeline(
            tet_result.mesh,
            tet_result.top_indices,
            tet_result.bottom_indices,
            AcTableMachine(),
            layer_height=0.2,
            path_spacing=0.2,
        )
        assert result.n_layers > 0
        assert result.n_paths > 0
        assert "G1" in result.gcode

    def test_gui_handler_runs_with_gmsh_backend(self, unit_cube_stl) -> None:
        from reinforced_slicer.gui.app import _run_curved_slice

        # Pre-tetrahedralise with gmsh so the handler uses the cached result.
        tet_result = tetrahedralize_surface(
            unit_cube_stl, backend="gmsh", target_size_mm=0.3
        )
        result = _run_curved_slice(
            mesh=unit_cube_stl,
            shoebox=tet_result,  # cached real tet mesh
            subdivisions=3,
            layer_height=0.2,
            path_spacing=0.2,
            tau_min=0.5, tau_max=2.0,
            flatness_weight=10.0, smoothness_weight=1e-4,
            z_target_override=0.5,
            use_z_target_override=False,
            backend="gmsh",
        )
        fig, summary, *_ = result
        assert fig is not None
        assert "backend**: `gmsh`" in summary


class TestAutoDispatch:
    def test_auto_picks_gmsh_when_available(self, unit_cube_stl: trimesh.Trimesh) -> None:
        result = tetrahedralize_surface(unit_cube_stl, backend="auto")
        expected = "gmsh" if GMSH_AVAILABLE else "shoebox"
        assert result.backend == expected

    def test_unknown_backend_rejected(self, unit_cube_stl: trimesh.Trimesh) -> None:
        with pytest.raises(ValueError, match="Unknown backend"):
            tetrahedralize_surface(unit_cube_stl, backend="bogus")  # type: ignore[arg-type]
