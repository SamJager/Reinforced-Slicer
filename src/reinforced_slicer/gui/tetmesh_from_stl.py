"""STL → TetMesh adapter for the GUI.

Real STL tetrahedralisation needs an external mesher (see the licence
discussion in ``reinforced_slicer/mesh/__init__.py``). Until that lands
the GUI falls back to a *shoebox* approximation: fit an axis-aligned
bounding box around the input mesh and tetrahedralise the box itself.
This is **geometrically wrong** for non-box parts — the curved-layer
slicer will operate on the AABB, not the real geometry — but it lets
the whole UI flow exercise end-to-end and prove the pipeline works.

Once a real tet mesher is wired up, swap ``shoebox_tet_mesh_from_stl``
for a real ``tetrahedralise(stl) -> TetMesh`` call; the GUI doesn't
need to change.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import trimesh

from reinforced_slicer.mesh.tet import (
    TetMesh,
    bottom_face_indices,
    cube_tet_mesh,
    top_face_indices,
)


@dataclass(frozen=True)
class ShoeboxTetMesh:
    """A cube-from-AABB tet mesh plus the top/bottom index sets."""

    mesh: TetMesh
    top_indices: np.ndarray
    bottom_indices: np.ndarray
    extent_mm: tuple[float, float, float]
    origin_mm: tuple[float, float, float]
    subdivisions: int
    note: str


def shoebox_tet_mesh_from_stl(
    stl_mesh: trimesh.Trimesh, subdivisions: int = 4
) -> ShoeboxTetMesh:
    """Fit an AABB to ``stl_mesh`` and tetrahedralise the box."""
    bounds = stl_mesh.bounds
    origin = tuple(float(x) for x in bounds[0])
    extent_xyz = tuple(float(x) for x in (bounds[1] - bounds[0]))
    extent = float(max(extent_xyz))
    mesh = cube_tet_mesh(extent=extent, subdivisions=subdivisions, origin=origin)
    note = (
        "Shoebox approximation: curved-layer pipeline operates on the AABB "
        "of the uploaded mesh, not the real geometry. Swap in a real tet "
        "mesher when available."
    )
    return ShoeboxTetMesh(
        mesh=mesh,
        top_indices=top_face_indices(subdivisions),
        bottom_indices=bottom_face_indices(subdivisions),
        extent_mm=extent_xyz,
        origin_mm=origin,
        subdivisions=subdivisions,
        note=note,
    )


def synthetic_tilted_cube(
    extent: float = 10.0,
    subdivisions: int = 4,
    tilt_slope_x: float = 0.0,
) -> ShoeboxTetMesh:
    """Build a synthetic cube with optional tilted top — the demo mesh.

    With ``tilt_slope_x != 0`` the top-face vertices get a linear ramp
    ``z = extent + tilt_slope_x * x``; the mesh interior is then
    relaxed to a linear column to keep tets non-degenerate. This is
    the exact fixture used in ``test_curvi_3d``.
    """
    mesh = cube_tet_mesh(extent=extent, subdivisions=subdivisions)
    if abs(tilt_slope_x) < 1e-12:
        note = "Synthetic axis-aligned cube."
        return ShoeboxTetMesh(
            mesh=mesh,
            top_indices=top_face_indices(subdivisions),
            bottom_indices=bottom_face_indices(subdivisions),
            extent_mm=(extent, extent, extent),
            origin_mm=(0.0, 0.0, 0.0),
            subdivisions=subdivisions,
            note=note,
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
    note = f"Synthetic cube with tilted top (slope_x = {tilt_slope_x})."
    return ShoeboxTetMesh(
        mesh=tilted,
        top_indices=top,
        bottom_indices=bottom_face_indices(s),
        extent_mm=(extent, extent, extent),
        origin_mm=(0.0, 0.0, 0.0),
        subdivisions=subdivisions,
        note=note,
    )
