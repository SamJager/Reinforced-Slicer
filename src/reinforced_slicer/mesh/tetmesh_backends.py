"""Real tet meshing backends for arbitrary surface meshes.

Until this lands, the GUI's curved-layer pipeline ran on an axis-aligned
bounding box of the input — geometrically wrong for non-box parts. This
module exposes ``tetrahedralize_surface`` which:

1. Tries the **gmsh** backend (LGPL, installed via the ``[tet]`` extra).
   gmsh is distributed as a separate Python wheel and dynamically linked,
   so an MIT consumer of this package stays MIT — the user installs the
   LGPL component themselves, and can swap it out.
2. Falls back to the **shoebox** AABB approximation when no real backend
   is available, with a clear ``Shoebox`` annotation on the result so the
   GUI can warn the user.

After tetrahedralisation the adapter also classifies surface vertices by
z extremes so the CurviSlicer QP gets sensible default top / bottom sets.
For a typical part oriented on a build plate this gives the right answer;
users wanting a different "up" direction can pass explicit index arrays
to ``solve_displacement_3d`` instead.
"""

from __future__ import annotations

import os
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import trimesh

from reinforced_slicer.mesh.tet import TetMesh

BackendName = Literal["gmsh", "shoebox"]


@dataclass(frozen=True)
class TetMeshResult:
    """A tet mesh plus default top/bottom index sets and the backend used."""

    mesh: TetMesh
    top_indices: np.ndarray
    bottom_indices: np.ndarray
    backend: BackendName
    note: str
    # Per-vertex flag: True if the vertex lies on the original surface
    # (i.e. is on the boundary of the tet mesh). Useful for visualisation
    # and for users who want to override the default top/bottom heuristic.
    is_surface_vertex: np.ndarray


def available_backends() -> list[BackendName]:
    """Return the names of currently-installed real backends."""
    out: list[BackendName] = []
    try:
        import gmsh  # noqa: F401
        out.append("gmsh")
    except ImportError:
        pass
    return out


def tetrahedralize_surface(
    surface_mesh: trimesh.Trimesh,
    backend: BackendName | Literal["auto"] = "auto",
    target_size_mm: float | None = None,
    z_tolerance: float = 1e-3,
) -> TetMeshResult:
    """Tetrahedralise a surface mesh and detect default top/bottom faces.

    ``backend="auto"`` picks the first available real backend, falling
    back to the shoebox AABB when none is installed.

    ``target_size_mm`` controls element size (default: a sensible
    fraction of the AABB diagonal).

    ``z_tolerance`` is the band width around z_max / z_min used to
    classify "top" / "bottom" surface vertices. Default is 0.1 % of the
    z extent.
    """
    if backend == "auto":
        avail = available_backends()
        backend = avail[0] if avail else "shoebox"

    if backend == "gmsh":
        return _tetrahedralize_with_gmsh(
            surface_mesh, target_size_mm=target_size_mm, z_tolerance=z_tolerance
        )
    if backend == "shoebox":
        return _shoebox_fallback(surface_mesh, z_tolerance=z_tolerance)
    raise ValueError(f"Unknown backend {backend!r}")


# --- gmsh backend ---------------------------------------------------------


def _tetrahedralize_with_gmsh(
    surface_mesh: trimesh.Trimesh,
    target_size_mm: float | None = None,
    z_tolerance: float = 1e-3,
) -> TetMeshResult:
    import gmsh

    bounds = surface_mesh.bounds
    extent = float(np.linalg.norm(bounds[1] - bounds[0]))
    if target_size_mm is None:
        target_size_mm = extent / 12.0

    # gmsh works through a stateful global API; isolate per call with try/finally.
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", target_size_mm)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", target_size_mm / 4.0)
        # Faster Delaunay-based 3D mesher.
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)

        with tempfile.TemporaryDirectory() as tmp:
            stl_path = Path(tmp) / "input.stl"
            surface_mesh.export(stl_path)
            gmsh.merge(str(stl_path))
            # Discrete surface -> geometry classification -> volume.
            angle = 40.0 * np.pi / 180.0
            gmsh.model.mesh.classifySurfaces(angle, True, True, angle)
            gmsh.model.mesh.createGeometry()

            surfaces = [s[1] for s in gmsh.model.getEntities(2)]
            if not surfaces:
                raise RuntimeError("gmsh classified no surfaces from the input mesh")
            loop = gmsh.model.geo.addSurfaceLoop(surfaces)
            gmsh.model.geo.addVolume([loop])
            gmsh.model.geo.synchronize()

            gmsh.model.mesh.generate(3)

            node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
            vertices = np.asarray(node_coords, dtype=float).reshape(-1, 3)
            # gmsh tags are 1-indexed and may not be contiguous.
            tag_to_index = {int(tag): i for i, tag in enumerate(node_tags)}

            elem_types, _, elem_node_tags = gmsh.model.mesh.getElements(dim=3)
            tet_list: list[list[int]] = []
            for etype, conn in zip(elem_types, elem_node_tags, strict=True):
                if int(etype) != 4:  # 4 = linear tetrahedron in gmsh's element types
                    continue
                conn_arr = np.asarray(conn, dtype=int).reshape(-1, 4)
                for row in conn_arr:
                    tet_list.append([tag_to_index[int(t)] for t in row])

            if not tet_list:
                raise RuntimeError("gmsh produced no tetrahedra")

    finally:
        gmsh.finalize()

    tets = np.asarray(tet_list, dtype=int)
    tet_mesh = TetMesh(vertices=vertices, tets=tets)
    is_surface, top_idx, bottom_idx = _classify_surface(
        tet_mesh, z_tolerance=z_tolerance
    )
    note = (
        f"gmsh ({len(tets)} tets, {len(vertices)} vertices, "
        f"~{target_size_mm:.2f} mm target element size)"
    )
    return TetMeshResult(
        mesh=tet_mesh,
        top_indices=top_idx,
        bottom_indices=bottom_idx,
        backend="gmsh",
        note=note,
        is_surface_vertex=is_surface,
    )


# --- Shoebox fallback ----------------------------------------------------


def _shoebox_fallback(
    surface_mesh: trimesh.Trimesh, z_tolerance: float = 1e-3
) -> TetMeshResult:
    from reinforced_slicer.mesh.tet import cube_tet_mesh

    bounds = surface_mesh.bounds
    origin = tuple(float(x) for x in bounds[0])
    extent_xyz = bounds[1] - bounds[0]
    extent = float(max(extent_xyz))
    sub = 4
    mesh = cube_tet_mesh(extent=extent, subdivisions=sub, origin=origin)
    is_surface, top_idx, bottom_idx = _classify_surface(mesh, z_tolerance=z_tolerance)
    note = (
        "Shoebox AABB fallback — install `pip install reinforced-slicer[tet]` "
        "for real STL tetrahedralisation."
    )
    return TetMeshResult(
        mesh=mesh,
        top_indices=top_idx,
        bottom_indices=bottom_idx,
        backend="shoebox",
        note=note,
        is_surface_vertex=is_surface,
    )


# --- Surface classification ---------------------------------------------


def _classify_surface(
    tet_mesh: TetMesh, z_tolerance: float = 1e-3
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Identify surface vertices and bin by z-extremes for default top/bottom.

    Returns ``(is_surface, top_indices, bottom_indices)``.
    """
    boundary_faces = _boundary_triangles(tet_mesh)
    surface_vertex_ids = np.unique(boundary_faces.reshape(-1))
    is_surface = np.zeros(tet_mesh.n_vertices, dtype=bool)
    is_surface[surface_vertex_ids] = True

    z = tet_mesh.vertices[:, 2]
    z_min, z_max = float(z[surface_vertex_ids].min()), float(z[surface_vertex_ids].max())
    band = max(z_tolerance * max(z_max - z_min, 1.0), 1e-9)

    top_mask = is_surface & (z >= z_max - band)
    bottom_mask = is_surface & (z <= z_min + band)
    return is_surface, np.where(top_mask)[0], np.where(bottom_mask)[0]


def _boundary_triangles(tet_mesh: TetMesh) -> np.ndarray:
    """Return faces of the tet mesh that border the outside (appear in 1 tet only)."""
    # Each tet has 4 triangular faces. Canonicalise each as sorted tuple.
    counts: Counter[tuple[int, int, int]] = Counter()
    face_origin: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for tet in tet_mesh.tets:
        a, b, c, d = int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3])
        for face in ((b, c, d), (a, c, d), (a, b, d), (a, b, c)):
            key = tuple(sorted(face))  # canonical hashing key
            counts[key] += 1
            face_origin.setdefault(key, face)
    boundary = [face_origin[key] for key, count in counts.items() if count == 1]
    if not boundary:
        return np.zeros((0, 3), dtype=int)
    return np.asarray(boundary, dtype=int)
