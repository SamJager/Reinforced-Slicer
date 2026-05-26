"""3D CurviSlicer — the QP from M2a, ported to tet meshes.

Same Etienne 2019 deformation-based formulation: solve for a vertical
displacement field ``h: V -> R`` on a tetrahedral mesh that flattens
the top face toward a target z plane, regularised by per-tet gradient
smoothness, subject to per-tet z-stretch bounds and an equality pin on
the bottom face. The 2D version (``curvi_2d``) develops the same QP on
triangles and is the easier place to inspect the algorithm; this file
adds the 3D-specific glue (3×4 gradients, tet volumes, target plane in
place of target line) and reuses OSQP for the solve.

The output displacement field is consumed by ``curvi_3d_isosurface``
(M2c.2, lands next) to extract curved layers as iso-surfaces of
``f(p) = z_p + h_p`` in the original mesh — that step is where the
"curved" in curved-layer slicing actually shows up.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import osqp
import scipy.sparse as sp

from reinforced_slicer.mesh.tet import TetMesh, tet_gradient, tet_volume


@dataclass(frozen=True)
class CurviSlicer3DConfig:
    """Weights and stretch bounds for the 3D CurviSlicer QP."""

    tau_min: float = 0.5
    tau_max: float = 2.0
    flatness_weight: float = 1.0
    smoothness_weight: float = 1e-3
    z_target: float | None = None  # default: mean of top-vertex z values
    osqp_eps_abs: float = 1e-7
    osqp_eps_rel: float = 1e-7
    osqp_max_iter: int = 20_000


@dataclass(frozen=True)
class CurviSlicer3DResult:
    displacement: np.ndarray  # shape (n_vertices,)
    deformed_mesh: TetMesh
    z_target: float
    osqp_status: str


def solve_displacement_3d(
    mesh: TetMesh,
    top_indices: np.ndarray,
    pinned_indices: np.ndarray,
    config: CurviSlicer3DConfig | None = None,
) -> CurviSlicer3DResult:
    """Solve the 3D CurviSlicer QP. Mirrors ``curvi_2d.solve_displacement``."""
    cfg = config or CurviSlicer3DConfig()
    if cfg.tau_min <= 0 or cfg.tau_max <= cfg.tau_min:
        raise ValueError(f"need 0 < tau_min < tau_max, got {cfg.tau_min}, {cfg.tau_max}")
    if np.intersect1d(top_indices, pinned_indices).size > 0:
        raise ValueError("top_indices and pinned_indices must be disjoint")

    n = mesh.n_vertices
    m = mesh.n_tets
    gradients = np.zeros((m, 3, 4))
    volumes = np.zeros(m)
    for t in range(m):
        tet = mesh.tets[t]
        pts = mesh.vertices[tet]
        gradients[t] = tet_gradient(pts[0], pts[1], pts[2], pts[3])
        volumes[t] = tet_volume(pts[0], pts[1], pts[2], pts[3])

    z_target = (
        cfg.z_target if cfg.z_target is not None else float(mesh.vertices[top_indices, 2].mean())
    )

    p_matrix, q = _assemble_objective(
        n=n,
        mesh=mesh,
        top_indices=top_indices,
        gradients=gradients,
        volumes=volumes,
        z_target=z_target,
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
    return CurviSlicer3DResult(
        displacement=h,
        deformed_mesh=mesh.displaced(h),
        z_target=z_target,
        osqp_status=status,
    )


def vertical_stretch_3d(mesh: TetMesh, displacement: np.ndarray) -> np.ndarray:
    """Per-tet 1 + ∂h/∂z. Equals τ_min..τ_max for a valid solution."""
    stretches = np.zeros(mesh.n_tets)
    for t in range(mesh.n_tets):
        tet = mesh.tets[t]
        pts = mesh.vertices[tet]
        grad = tet_gradient(pts[0], pts[1], pts[2], pts[3])
        stretches[t] = 1.0 + grad[2] @ displacement[tet]
    return stretches


# --- assembly ------------------------------------------------------------


def _assemble_objective(
    n: int,
    mesh: TetMesh,
    top_indices: np.ndarray,
    gradients: np.ndarray,
    volumes: np.ndarray,
    z_target: float,
    cfg: CurviSlicer3DConfig,
) -> tuple[sp.spmatrix, np.ndarray]:
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    q = np.zeros(n)

    # Flatness: w * (z_v + h_v - z_target)^2 for v in top
    for v in top_indices:
        rows.append(int(v))
        cols.append(int(v))
        data.append(2.0 * cfg.flatness_weight)
        q[v] += 2.0 * cfg.flatness_weight * (mesh.vertices[v, 2] - z_target)

    # Smoothness: w * vol(t) * |∇h|^2 = h_t^T (G_t^T G_t) h_t per tet
    for t in range(mesh.n_tets):
        tet = mesh.tets[t]
        grad = gradients[t]  # shape (3, 4)
        k_local = 2.0 * cfg.smoothness_weight * volumes[t] * (grad.T @ grad)
        for i in range(4):
            for j in range(4):
                rows.append(int(tet[i]))
                cols.append(int(tet[j]))
                data.append(float(k_local[i, j]))

    p_matrix = sp.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    return p_matrix, q


def _assemble_constraints(
    n: int,
    mesh: TetMesh,
    gradients: np.ndarray,
    pinned_indices: np.ndarray,
    cfg: CurviSlicer3DConfig,
) -> tuple[sp.spmatrix, np.ndarray, np.ndarray]:
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    lower: list[float] = []
    upper: list[float] = []

    # Per-tet stretch: τ_min - 1 ≤ (∂h/∂z)_t ≤ τ_max - 1
    for t in range(mesh.n_tets):
        tet = mesh.tets[t]
        c_row = gradients[t, 2]  # z-component of gradient
        row_idx = len(lower)
        for i in range(4):
            rows.append(row_idx)
            cols.append(int(tet[i]))
            data.append(float(c_row[i]))
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
