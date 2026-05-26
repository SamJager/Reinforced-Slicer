"""3D tet mesh primitives.

The 3D analogue of ``triangle2d``: a ``TetMesh`` dataclass plus the
constant-per-tet gradient operator and volume helper that the 3D
CurviSlicer QP (M2c) needs. Hand-built cube-as-tets constructor lets
M2c develop and test the QP without depending on an external tet
mesher — the mesher backend lands separately so a license or
install-path issue with the mesher can't block algorithm work.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TetMesh:
    """A 3D tetrahedral mesh: vertex coordinates and tet index quadruples."""

    vertices: np.ndarray  # shape (N, 3)
    tets: np.ndarray  # shape (M, 4), int

    def __post_init__(self) -> None:
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise ValueError(f"vertices must be shape (N, 3), got {self.vertices.shape}")
        if self.tets.ndim != 2 or self.tets.shape[1] != 4:
            raise ValueError(f"tets must be shape (M, 4), got {self.tets.shape}")
        if self.tets.max() >= len(self.vertices):
            raise ValueError("tet index out of range")

    @property
    def n_vertices(self) -> int:
        return int(self.vertices.shape[0])

    @property
    def n_tets(self) -> int:
        return int(self.tets.shape[0])

    def displaced(self, dz: np.ndarray) -> TetMesh:
        """Return a copy with each vertex shifted vertically (z) by ``dz[v]``."""
        if dz.shape != (self.n_vertices,):
            raise ValueError(f"dz must be shape ({self.n_vertices},), got {dz.shape}")
        new_vertices = self.vertices.copy()
        new_vertices[:, 2] += dz
        return TetMesh(vertices=new_vertices, tets=self.tets)


def tet_gradient(
    p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray
) -> np.ndarray:
    """Return the 3×4 gradient operator ``G`` for a 3D tetrahedron.

    For any linear scalar field on the tet with vertex values
    ``(h0, h1, h2, h3)``, the (constant) gradient is
    ``G · [h0, h1, h2, h3]``. Columns of ``G`` are
    ``∇λ_0, ∇λ_1, ∇λ_2, ∇λ_3`` where λ_i are the barycentric coordinates.
    The tet must be non-degenerate.
    """
    m = np.column_stack([p1 - p0, p2 - p0, p3 - p0]).astype(float)
    det = float(np.linalg.det(m))
    if abs(det) < 1e-15:
        raise ValueError("degenerate tet: zero volume")
    m_inv = np.linalg.inv(m)
    # Rows of m_inv are ∇λ_1, ∇λ_2, ∇λ_3.
    g1, g2, g3 = m_inv[0], m_inv[1], m_inv[2]
    g0 = -(g1 + g2 + g3)
    return np.column_stack([g0, g1, g2, g3])


def tet_volume(
    p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray
) -> float:
    """Unsigned volume of a tetrahedron."""
    m = np.column_stack([p1 - p0, p2 - p0, p3 - p0]).astype(float)
    return abs(float(np.linalg.det(m))) / 6.0


def cube_tet_mesh(
    extent: float = 1.0, subdivisions: int = 1, origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> TetMesh:
    """Tetrahedralise an axis-aligned cube ``[0, extent]³`` into 6·N³ tets.

    Each axis is subdivided into ``subdivisions`` equal cells; each unit
    cell is split into six tetrahedra sharing the cell's main diagonal.
    Useful as a synthetic test volume that doesn't require an external
    tet mesher to be installed.

    Vertex indices follow standard binary ordering within each cell:
    bit 0 = +x, bit 1 = +y, bit 2 = +z. Within the whole grid, vertex
    at integer coordinate ``(i, j, k)`` (each in ``0..subdivisions``)
    has linear index ``k·(s+1)² + j·(s+1) + i`` where ``s = subdivisions``.
    """
    if subdivisions < 1:
        raise ValueError("subdivisions must be >= 1")
    s = subdivisions
    n = s + 1
    step = extent / s

    # Vertices on a regular grid.
    vertices = np.zeros((n * n * n, 3))
    for k in range(n):
        for j in range(n):
            for i in range(n):
                vertices[k * n * n + j * n + i] = (
                    origin[0] + i * step,
                    origin[1] + j * step,
                    origin[2] + k * step,
                )

    # Within each cell, the eight corners in binary-ordered (x,y,z).
    # Splitting into six tets along the diagonal (0,0,0) -> (1,1,1):
    # the standard "Kuhn triangulation" of the cube.
    cell_tets = np.array(
        [
            [0, 1, 3, 7],
            [0, 3, 2, 7],
            [0, 2, 6, 7],
            [0, 6, 4, 7],
            [0, 4, 5, 7],
            [0, 5, 1, 7],
        ],
        dtype=int,
    )

    tets = np.zeros((s * s * s * 6, 4), dtype=int)
    t_out = 0
    for k in range(s):
        for j in range(s):
            for i in range(s):
                # Index of the cell's eight corners in the global vertex array.
                corner_idx = np.array(
                    [
                        (k + ((b >> 2) & 1)) * n * n
                        + (j + ((b >> 1) & 1)) * n
                        + (i + (b & 1))
                        for b in range(8)
                    ],
                    dtype=int,
                )
                for local in cell_tets:
                    tets[t_out] = corner_idx[local]
                    t_out += 1

    return TetMesh(vertices=vertices, tets=tets)


def grid_vertex_index(i: int, j: int, k: int, subdivisions: int) -> int:
    """Linear index of grid vertex ``(i, j, k)`` for ``cube_tet_mesh``."""
    n = subdivisions + 1
    return k * n * n + j * n + i


def top_face_indices(subdivisions: int) -> np.ndarray:
    """Vertex indices of the +z face of a ``cube_tet_mesh``."""
    n = subdivisions + 1
    return np.array(
        [grid_vertex_index(i, j, subdivisions, subdivisions) for j in range(n) for i in range(n)],
        dtype=int,
    )


def bottom_face_indices(subdivisions: int) -> np.ndarray:
    """Vertex indices of the -z face of a ``cube_tet_mesh``."""
    n = subdivisions + 1
    return np.array(
        [grid_vertex_index(i, j, 0, subdivisions) for j in range(n) for i in range(n)],
        dtype=int,
    )
