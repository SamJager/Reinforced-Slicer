"""STL → TetMesh adapter for the GUI.

Thin wrapper around ``reinforced_slicer.mesh.tetrahedralize_surface``
that also keeps a demo-only ``synthetic_tilted_cube`` constructor for
the Tab-1 synthetic-cube generator.

The GUI deals in ``TetMeshResult`` (from the backend dispatch module)
rather than the older ``ShoeboxTetMesh``; the two have the same
slicer-relevant fields (``mesh``, ``top_indices``, ``bottom_indices``,
``note``) so this is a near-drop-in change.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import trimesh

from reinforced_slicer.mesh.tet import (
    TetMesh,
    bottom_face_indices,
    cube_tet_mesh,
    top_face_indices,
)
from reinforced_slicer.mesh.tetmesh_backends import (
    TetMeshResult,
    tetrahedralize_surface,
)


# Backwards-compatible alias used by existing GUI code.
ShoeboxTetMesh = TetMeshResult


def shoebox_tet_mesh_from_stl(
    stl_mesh: trimesh.Trimesh,
    subdivisions: int = 4,
    backend: Literal["auto", "gmsh", "shoebox"] = "auto",
) -> TetMeshResult:
    """Tetrahedralise ``stl_mesh`` using the best available backend.

    The default ``backend="auto"`` picks the real ``gmsh`` mesher when
    available and falls back to a Kuhn-triangulation of the AABB
    shoebox when no real backend is installed. Pass ``backend="shoebox"``
    explicitly to force the fallback even when gmsh is available — useful
    for benchmarking or for cases where the real mesher chokes on
    non-watertight inputs.

    ``subdivisions`` is honoured by the shoebox backend only; the real
    backend's resolution is controlled via ``tetrahedralize_surface``'s
    ``target_size_mm`` argument (this wrapper picks a default based on
    the AABB diagonal).
    """
    if backend == "shoebox":
        return tetrahedralize_surface(stl_mesh, backend="shoebox")
    return tetrahedralize_surface(stl_mesh, backend=backend)


def synthetic_tilted_cube(
    extent: float = 10.0,
    subdivisions: int = 4,
    tilt_slope_x: float = 0.0,
) -> TetMeshResult:
    """Build a synthetic cube with optional tilted top — the demo mesh.

    With ``tilt_slope_x != 0`` the top-face vertices get a linear ramp
    ``z = extent + tilt_slope_x * x``; the mesh interior is then
    relaxed to a linear column to keep tets non-degenerate. This is
    the exact fixture used in ``test_curvi_3d``.
    """
    mesh = cube_tet_mesh(extent=extent, subdivisions=subdivisions)
    if abs(tilt_slope_x) < 1e-12:
        top = top_face_indices(subdivisions)
        bottom = bottom_face_indices(subdivisions)
        is_surface = np.zeros(mesh.n_vertices, dtype=bool)
        for idx in np.concatenate(
            [top, bottom, _side_face_indices(subdivisions)]
        ):
            is_surface[idx] = True
        return TetMeshResult(
            mesh=mesh,
            top_indices=top,
            bottom_indices=bottom,
            backend="shoebox",
            note="Synthetic axis-aligned cube.",
            is_surface_vertex=is_surface,
        )

    s = subdivisions
    n = s + 1
    top = top_face_indices(s)
    perturbed = mesh.vertices.copy()
    perturbed[top, 2] = extent + tilt_slope_x * perturbed[top, 0]
    for i in range(n):
        for j in range(n):
            top_idx = i + j * n + (n * n * s)
            new_top_z = perturbed[top_idx, 2]
            for k in range(n):
                idx = i + j * n + k * n * n
                perturbed[idx, 2] = (k / s) * new_top_z
    tilted = TetMesh(vertices=perturbed, tets=mesh.tets)
    bottom = bottom_face_indices(s)
    is_surface = np.zeros(tilted.n_vertices, dtype=bool)
    for idx in np.concatenate([top, bottom, _side_face_indices(s)]):
        is_surface[idx] = True
    return TetMeshResult(
        mesh=tilted,
        top_indices=top,
        bottom_indices=bottom,
        backend="shoebox",
        note=f"Synthetic cube with tilted top (slope_x = {tilt_slope_x}).",
        is_surface_vertex=is_surface,
    )


def _side_face_indices(s: int) -> np.ndarray:
    """Vertices on the four non-top/bottom faces of a cube_tet_mesh."""
    n = s + 1
    idxs: list[int] = []
    for k in range(n):
        for j in range(n):
            for i in range(n):
                on_x = i == 0 or i == s
                on_y = j == 0 or j == s
                if on_x or on_y:
                    idxs.append(k * n * n + j * n + i)
    return np.array(idxs, dtype=int)

