"""2D CurviSlicer — a toy reimplementation of the Etienne 2019 algorithm.

This file is M2a: the deformation-based slicing idea ported to 2D so the
QP wiring (OSQP, sparse assembly, stretch constraints, soft flatness)
can be tested on a problem that's easy to reason about and plot. The
3D version (M2c) reuses the same formulation with tet gradients and a
target plane instead of a target line.

The QP, expressed informally
----------------------------

We solve for a vertical displacement field ``h: V -> R`` over a 2D
triangle mesh. The deformed mesh has vertex i at ``(x_i, y_i + h_i)``.
The objective is

    minimise  w_flat   · Σ_{v ∈ top}        (y_v + h_v - y_target)²
            + w_smooth · Σ_{t ∈ triangles}  area(t) · |∇h_t|²

subject to per-triangle vertical-stretch bounds

    τ_min ≤ 1 + (∂h/∂y)_t ≤ τ_max     ∀ t

and an equality pin on the bottom row, ``h_v = 0 ∀ v ∈ pinned``, so the
build plate doesn't drift. The flatness objective drives the top edge
to a horizontal line; the stretch bounds prevent the printer being
asked for an impossible layer thickness; the smoothness term picks a
well-conditioned displacement in the nullspace of the other terms.

OSQP expects the upper triangle of the symmetric matrix P in standard
form ``minimise (1/2) x^T P x + q^T x  s.t.  l ≤ A x ≤ u``; we
assemble P and A in COO form for clarity and convert once at the end.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import osqp
import scipy.sparse as sp

from reinforced_slicer.mesh.triangle2d import (
    TriangleMesh2D,
    triangle_area,
    triangle_gradient,
)


@dataclass(frozen=True)
class CurviSlicer2DConfig:
    """Weights and stretch bounds for the 2D CurviSlicer QP."""

    tau_min: float = 0.5  # min vertical stretch a printer can achieve
    tau_max: float = 2.0  # max vertical stretch
    flatness_weight: float = 1.0
    smoothness_weight: float = 1e-3
    y_target: float | None = None  # if None, use the mean of top-vertex y values
    osqp_eps_abs: float = 1e-7
    osqp_eps_rel: float = 1e-7
    osqp_max_iter: int = 20_000


@dataclass(frozen=True)
class CurviSlicer2DResult:
    displacement: np.ndarray  # shape (n_vertices,)
    deformed_mesh: TriangleMesh2D
    y_target: float
    osqp_status: str


def solve_displacement(
    mesh: TriangleMesh2D,
    top_indices: np.ndarray,
    pinned_indices: np.ndarray,
    config: CurviSlicer2DConfig | None = None,
) -> CurviSlicer2DResult:
    """Run the 2D CurviSlicer QP and return the displacement field.

    ``top_indices`` are vertices the flatness objective acts on (the
    "top of part" set). ``pinned_indices`` are vertices held at h = 0
    (typically the bottom row sitting on the build plate). Top and
    pinned sets must be disjoint — pinning a top vertex would override
    the flatness objective.
    """
    cfg = config or CurviSlicer2DConfig()
    if cfg.tau_min <= 0 or cfg.tau_max <= cfg.tau_min:
        raise ValueError(f"need 0 < tau_min < tau_max, got {cfg.tau_min}, {cfg.tau_max}")
    if np.intersect1d(top_indices, pinned_indices).size > 0:
        raise ValueError("top_indices and pinned_indices must be disjoint")

    n = mesh.n_vertices
    m = mesh.n_triangles
    gradients = np.zeros((m, 2, 3))
    areas = np.zeros(m)
    for t in range(m):
        tri = mesh.triangles[t]
        p0, p1, p2 = mesh.vertices[tri]
        gradients[t] = triangle_gradient(p0, p1, p2)
        areas[t] = triangle_area(p0, p1, p2)

    y_target = (
        cfg.y_target if cfg.y_target is not None else float(mesh.vertices[top_indices, 1].mean())
    )

    p_matrix, q = _assemble_objective(
        n=n,
        mesh=mesh,
        top_indices=top_indices,
        gradients=gradients,
        areas=areas,
        y_target=y_target,
        cfg=cfg,
    )
    a_matrix, lower, upper = _assemble_constraints(
        n=n,
        mesh=mesh,
        gradients=gradients,
        pinned_indices=pinned_indices,
        cfg=cfg,
    )

    solver = osqp.OSQP()
    solver.setup(
        P=sp.triu(p_matrix).tocsc(),
        q=q,
        A=a_matrix.tocsc(),
        l=lower,
        u=upper,
        eps_abs=cfg.osqp_eps_abs,
        eps_rel=cfg.osqp_eps_rel,
        max_iter=cfg.osqp_max_iter,
        verbose=False,
        polishing=True,
    )
    result = solver.solve(raise_error=True)
    status = str(result.info.status)
    if status not in ("solved", "solved inaccurate"):
        raise RuntimeError(f"OSQP failed with status {status!r}")

    h = np.asarray(result.x, dtype=float)
    return CurviSlicer2DResult(
        displacement=h,
        deformed_mesh=mesh.displaced(h),
        y_target=y_target,
        osqp_status=status,
    )


def vertical_stretch(mesh: TriangleMesh2D, displacement: np.ndarray) -> np.ndarray:
    """Per-triangle 1 + ∂h/∂y. Equals τ_min..τ_max for a valid solution."""
    stretches = np.zeros(mesh.n_triangles)
    for t in range(mesh.n_triangles):
        tri = mesh.triangles[t]
        p0, p1, p2 = mesh.vertices[tri]
        grad = triangle_gradient(p0, p1, p2)
        stretches[t] = 1.0 + grad[1] @ displacement[tri]
    return stretches


# --- assembly ------------------------------------------------------------


def _assemble_objective(
    n: int,
    mesh: TriangleMesh2D,
    top_indices: np.ndarray,
    gradients: np.ndarray,
    areas: np.ndarray,
    y_target: float,
    cfg: CurviSlicer2DConfig,
) -> tuple[sp.spmatrix, np.ndarray]:
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    q = np.zeros(n)

    # Flatness: w * (y_v + h_v - y_target)^2
    for v in top_indices:
        rows.append(int(v))
        cols.append(int(v))
        data.append(2.0 * cfg.flatness_weight)
        q[v] += 2.0 * cfg.flatness_weight * (mesh.vertices[v, 1] - y_target)

    # Smoothness: w * area(t) * |∇h|^2 = h_t^T (G_t^T G_t) h_t per triangle
    for t in range(mesh.n_triangles):
        tri = mesh.triangles[t]
        grad = gradients[t]
        k_local = 2.0 * cfg.smoothness_weight * areas[t] * (grad.T @ grad)
        for i in range(3):
            for j in range(3):
                rows.append(int(tri[i]))
                cols.append(int(tri[j]))
                data.append(float(k_local[i, j]))

    p_matrix = sp.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    return p_matrix, q


def _assemble_constraints(
    n: int,
    mesh: TriangleMesh2D,
    gradients: np.ndarray,
    pinned_indices: np.ndarray,
    cfg: CurviSlicer2DConfig,
) -> tuple[sp.spmatrix, np.ndarray, np.ndarray]:
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    lower: list[float] = []
    upper: list[float] = []

    # Per-triangle stretch: τ_min - 1 ≤ (∂h/∂y)_t ≤ τ_max - 1
    for t in range(mesh.n_triangles):
        tri = mesh.triangles[t]
        b_row = gradients[t, 1]  # y-component of gradient
        row_idx = len(lower)
        for i in range(3):
            rows.append(row_idx)
            cols.append(int(tri[i]))
            data.append(float(b_row[i]))
        lower.append(cfg.tau_min - 1.0)
        upper.append(cfg.tau_max - 1.0)

    # Pinned vertices: h_v = 0
    for v in pinned_indices:
        row_idx = len(lower)
        rows.append(row_idx)
        cols.append(int(v))
        data.append(1.0)
        lower.append(0.0)
        upper.append(0.0)

    a_matrix = sp.coo_matrix(
        (data, (rows, cols)),
        shape=(len(lower), n),
    )
    return a_matrix, np.array(lower), np.array(upper)
