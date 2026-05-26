"""2D triangle mesh primitives.

This is intentionally minimal — just what the M2a CurviSlicer toy needs.
A ``TriangleMesh2D`` stores vertices and triangle index triples; the
free functions compute the constant-per-triangle gradient operator and
triangle areas that the QP assembly needs.

For 3D tet meshes (M2b/M2c) we'll wrap an external tet mesher; this
file stays small and dependency-free.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TriangleMesh2D:
    """A 2D triangle mesh: vertex coordinates and triangle index triples."""

    vertices: np.ndarray  # shape (N, 2)
    triangles: np.ndarray  # shape (M, 3), int

    def __post_init__(self) -> None:
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 2:
            raise ValueError(f"vertices must be shape (N, 2), got {self.vertices.shape}")
        if self.triangles.ndim != 2 or self.triangles.shape[1] != 3:
            raise ValueError(f"triangles must be shape (M, 3), got {self.triangles.shape}")
        if self.triangles.max() >= len(self.vertices):
            raise ValueError("triangle index out of range")

    @property
    def n_vertices(self) -> int:
        return int(self.vertices.shape[0])

    @property
    def n_triangles(self) -> int:
        return int(self.triangles.shape[0])

    def displaced(self, dy: np.ndarray) -> TriangleMesh2D:
        """Return a copy with each vertex shifted vertically by ``dy[v]``."""
        if dy.shape != (self.n_vertices,):
            raise ValueError(f"dy must be shape ({self.n_vertices},), got {dy.shape}")
        new_vertices = self.vertices.copy()
        new_vertices[:, 1] += dy
        return TriangleMesh2D(vertices=new_vertices, triangles=self.triangles)


def triangle_gradient(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    """Return the 2×3 gradient operator ``G`` for a 2D triangle.

    For any linear scalar field on the triangle with vertex values
    ``(h0, h1, h2)``, the (constant) gradient is ``G · [h0, h1, h2]``.
    Columns of ``G`` are ``∇λ_0, ∇λ_1, ∇λ_2`` where λ_i are the barycentric
    coordinates. The triangle must be non-degenerate.
    """
    m = np.array(
        [[p1[0] - p0[0], p2[0] - p0[0]], [p1[1] - p0[1], p2[1] - p0[1]]],
        dtype=float,
    )
    det = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
    if abs(det) < 1e-15:
        raise ValueError("degenerate triangle: zero area")
    m_inv = np.array([[m[1, 1], -m[0, 1]], [-m[1, 0], m[0, 0]]]) / det
    g1 = m_inv[0]
    g2 = m_inv[1]
    g0 = -g1 - g2
    return np.column_stack([g0, g1, g2])


def triangle_area(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> float:
    """Unsigned triangle area in 2D."""
    return 0.5 * abs(
        (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1])
    )


def grid_mesh(
    x_count: int,
    y_count: int,
    width: float,
    height_fn: object,
) -> TriangleMesh2D:
    """Build a structured triangle mesh on a rectangle ``[0, width] × [0, H(x)]``.

    ``height_fn(x) -> H`` defines the (possibly curved) top edge. The mesh
    has ``x_count`` columns and ``y_count`` rows of vertices; each cell
    is split into two triangles. The bottom row sits at y = 0, the top
    row at y = H(x_col); intermediate rows interpolate linearly.

    Used to construct test inputs for the M2a CurviSlicer.
    """
    xs = np.linspace(0.0, width, x_count)
    vertices = np.zeros((x_count * y_count, 2))
    for i, x in enumerate(xs):
        h_top = float(height_fn(x))
        ys = np.linspace(0.0, h_top, y_count)
        for j, y in enumerate(ys):
            vertices[i * y_count + j] = (x, y)

    triangles: list[tuple[int, int, int]] = []
    for i in range(x_count - 1):
        for j in range(y_count - 1):
            v00 = i * y_count + j
            v10 = (i + 1) * y_count + j
            v01 = i * y_count + (j + 1)
            v11 = (i + 1) * y_count + (j + 1)
            triangles.append((v00, v10, v11))
            triangles.append((v00, v11, v01))
    return TriangleMesh2D(vertices=vertices, triangles=np.array(triangles, dtype=int))


def top_row_indices(mesh: TriangleMesh2D, x_count: int, y_count: int) -> np.ndarray:
    """Vertex indices of the top row of a ``grid_mesh``."""
    return np.array(
        [i * y_count + (y_count - 1) for i in range(x_count)], dtype=int
    )


def bottom_row_indices(mesh: TriangleMesh2D, x_count: int, y_count: int) -> np.ndarray:
    """Vertex indices of the bottom row of a ``grid_mesh``."""
    return np.array([i * y_count for i in range(x_count)], dtype=int)
