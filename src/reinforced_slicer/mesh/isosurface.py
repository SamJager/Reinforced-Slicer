"""Marching tetrahedra: extract iso-surfaces of a scalar field on a TetMesh.

For curved-layer slicing the scalar field is ``f(p) = z_p + h_p`` where
``h`` is the CurviSlicer displacement: iso-surfaces of f at uniform
values are the curved layers in the original mesh's coordinates,
spaced by one nominal layer height each. The output ``IsoSurface``
carries the surface triangles, the original-coordinate vertex
positions, and area-weighted vertex normals — those normals are the
tool-axis directions the M2c.3 path planner consumes.

Marching tets is conceptually simpler than marching cubes (no ambiguous
cases) — each tet has 4 vertices, classified above or below the iso
value, and the 16 sign masks reduce to three case families:

* 0 or 4 vertices above: no intersection.
* 1 or 3 vertices above: one triangle, three edge crossings.
* 2 vertices above: a quadrilateral, four edge crossings, split into
  two triangles along the diagonal.

Triangle winding is fixed up after construction by checking the
triangle normal against the tet's gradient direction (which we know
points toward higher f); if they disagree, we reverse the winding.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reinforced_slicer.mesh.tet import TetMesh, tet_gradient


@dataclass(frozen=True)
class IsoSurface:
    """An iso-surface as a triangle mesh in the original space.

    ``normals`` are unit, area-weighted, and point in the direction of
    increasing ``f`` (the build direction for a curved layer).
    """

    vertices: np.ndarray  # (N, 3)
    triangles: np.ndarray  # (M, 3) int
    normals: np.ndarray  # (N, 3), unit

    @property
    def n_vertices(self) -> int:
        return int(self.vertices.shape[0])

    @property
    def n_triangles(self) -> int:
        return int(self.triangles.shape[0])

    def is_empty(self) -> bool:
        return self.n_triangles == 0


def extract_isosurface(
    mesh: TetMesh, field: np.ndarray, level: float
) -> IsoSurface:
    """Extract the iso-surface ``{p : f(p) = level}`` via marching tets."""
    if field.shape != (mesh.n_vertices,):
        raise ValueError(f"field must be shape ({mesh.n_vertices},), got {field.shape}")

    vertices_out: list[np.ndarray] = []
    triangles_out: list[tuple[int, int, int]] = []
    edge_cache: dict[tuple[int, int], int] = {}
    vertex_cache: dict[int, int] = {}

    for tet in mesh.tets:
        f_local = field[tet]
        above = [int(i) for i in range(4) if f_local[i] > level]
        below = [int(i) for i in range(4) if f_local[i] <= level]
        if not above or not below:
            continue

        crossings = _crossings_for_case(above, below)
        triangles_local = _triangles_for_case(len(crossings))

        pts = mesh.vertices[tet]
        grad_f = tet_gradient(pts[0], pts[1], pts[2], pts[3]) @ f_local

        # Materialise the crossing vertices in the output. When the iso
        # passes exactly through an original mesh vertex (t == 0 or 1 on
        # the incident edge), we snap to that vertex via vertex_cache so
        # all triangles touching the snap point share a single output
        # vertex rather than duplicating it under different edge keys.
        global_indices: list[int] = []
        for a, b in crossings:
            global_indices.append(
                _ensure_edge_point(
                    edge_cache=edge_cache,
                    vertex_cache=vertex_cache,
                    vertices_out=vertices_out,
                    mesh=mesh,
                    field=field,
                    level=level,
                    v_a=int(tet[a]),
                    v_b=int(tet[b]),
                )
            )

        for i0, i1, i2 in triangles_local:
            ia, ib, ic = global_indices[i0], global_indices[i1], global_indices[i2]
            # Skip triangles that collapsed when two crossings snapped to
            # the same mesh vertex — they carry no surface information.
            if ia == ib or ib == ic or ia == ic:
                continue
            p0, p1, p2 = vertices_out[ia], vertices_out[ib], vertices_out[ic]
            normal = np.cross(p1 - p0, p2 - p0)
            if np.linalg.norm(normal) < 1e-15:
                continue  # collinear (numerical degenerate)
            if normal @ grad_f < 0:
                triangles_out.append((ia, ic, ib))
            else:
                triangles_out.append((ia, ib, ic))

    if not vertices_out:
        return IsoSurface(
            vertices=np.zeros((0, 3)),
            triangles=np.zeros((0, 3), dtype=int),
            normals=np.zeros((0, 3)),
        )

    vertices = np.array(vertices_out)
    triangles = np.array(triangles_out, dtype=int)
    normals = _area_weighted_vertex_normals(vertices, triangles)
    return IsoSurface(vertices=vertices, triangles=triangles, normals=normals)


def extract_curved_layers(
    mesh: TetMesh,
    field: np.ndarray,
    layer_height: float,
    *,
    levels: np.ndarray | None = None,
) -> list[IsoSurface]:
    """Extract a stack of iso-surfaces at uniform field values.

    The defaults span ``[f_min + layer_height/2, f_max]`` so the first
    layer sits half a layer above the bottom — same convention as the
    planar slicer. Pass ``levels`` explicitly to override (e.g. for
    adaptive layer heights).
    """
    if levels is None:
        f_min, f_max = float(field.min()), float(field.max())
        start = f_min + layer_height / 2.0
        n_layers = max(1, int(np.floor((f_max - start) / layer_height)) + 1)
        levels = start + np.arange(n_layers) * layer_height
    return [extract_isosurface(mesh, field, level=float(c)) for c in levels]


# --- internals -----------------------------------------------------------


def _crossings_for_case(above: list[int], below: list[int]) -> list[tuple[int, int]]:
    """Edge crossings as ``(above_vertex, below_vertex)`` pairs."""
    if len(above) == 1 or len(below) == 1:
        if len(above) == 1:
            a = above[0]
            return [(a, b) for b in below]
        b = below[0]
        return [(a, b) for a in above]
    # 2 above, 2 below: order crossings around the quad so we can split
    # into two non-overlapping triangles via diagonal 0-2.
    a0, a1 = above
    b0, b1 = below
    return [(a0, b0), (a0, b1), (a1, b1), (a1, b0)]


def _triangles_for_case(n_crossings: int) -> list[tuple[int, int, int]]:
    if n_crossings == 3:
        return [(0, 1, 2)]
    if n_crossings == 4:
        return [(0, 1, 2), (0, 2, 3)]
    raise ValueError(f"unexpected crossing count: {n_crossings}")


_SNAP_TOL = 1e-9


def _ensure_edge_point(
    edge_cache: dict[tuple[int, int], int],
    vertex_cache: dict[int, int],
    vertices_out: list[np.ndarray],
    mesh: TetMesh,
    field: np.ndarray,
    level: float,
    v_a: int,
    v_b: int,
) -> int:
    """Return the global iso-vertex index for the crossing on edge (v_a, v_b).

    When the crossing parameter ``t`` is at the edge (``t≈0`` or ``t≈1``),
    snap to the corresponding original mesh vertex via ``vertex_cache`` so
    iso-points falling on a mesh vertex are de-duplicated globally.
    """
    f_a, f_b = float(field[v_a]), float(field[v_b])
    denom = f_b - f_a
    if abs(denom) < 1e-15:
        # Edge lies entirely on the iso level; arbitrarily snap to v_a.
        return _ensure_vertex_point(vertex_cache, vertices_out, mesh, v_a)
    t = (level - f_a) / denom
    if t <= _SNAP_TOL:
        return _ensure_vertex_point(vertex_cache, vertices_out, mesh, v_a)
    if t >= 1.0 - _SNAP_TOL:
        return _ensure_vertex_point(vertex_cache, vertices_out, mesh, v_b)

    key = (min(v_a, v_b), max(v_a, v_b))
    cached = edge_cache.get(key)
    if cached is not None:
        return cached
    p = mesh.vertices[v_a] + t * (mesh.vertices[v_b] - mesh.vertices[v_a])
    idx = len(vertices_out)
    vertices_out.append(p)
    edge_cache[key] = idx
    return idx


def _ensure_vertex_point(
    vertex_cache: dict[int, int],
    vertices_out: list[np.ndarray],
    mesh: TetMesh,
    v: int,
) -> int:
    cached = vertex_cache.get(v)
    if cached is not None:
        return cached
    idx = len(vertices_out)
    vertices_out.append(mesh.vertices[v].copy())
    vertex_cache[v] = idx
    return idx


def _area_weighted_vertex_normals(
    vertices: np.ndarray, triangles: np.ndarray
) -> np.ndarray:
    """Sum of incident face normals (each weighted by 2·area via cross magnitude),
    then normalise per vertex."""
    normals = np.zeros_like(vertices)
    for tri in triangles:
        p0, p1, p2 = vertices[tri]
        face_normal = np.cross(p1 - p0, p2 - p0)
        for v in tri:
            normals[v] += face_normal
    magnitudes = np.linalg.norm(normals, axis=1, keepdims=True)
    magnitudes[magnitudes < 1e-12] = 1.0
    return normals / magnitudes
