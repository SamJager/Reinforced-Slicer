"""Stripe-pattern scalar field for fiber-aligned path planning.

Given a per-vertex direction field ``V`` (the fiber direction), we want
a scalar field ``φ`` on the surface whose iso-lines are stripes parallel
to ``V``. The iso-lines of ``φ`` are perpendicular to ``∇φ``, so we
solve for ``φ`` with ``∇φ ≈ V_perp`` — the 90° rotation of ``V`` in
each vertex's tangent plane. This is the Li 2025 §3.4 approach.

Discretisation, briefly:

* Per triangle ``t`` we have a 3D linear gradient operator built from
  the barycentric basis. Given the three target vertex φ values,
  ``∇φ_t = Σ_i φ_i ∇λ_i^t`` lies in the triangle's plane.
* The energy ``∫ |∇φ - V_perp|² dA`` is quadratic in φ. Minimising
  gives a sparse linear system ``L φ = b`` where ``L`` is the cotan
  Laplacian (assembled here directly from ``∇λ_i · ∇λ_j`` per
  triangle) and ``b`` carries the target-gradient inner products.
* ``L`` has a 1D nullspace (adding a constant to φ doesn't change
  anything) so we pin one vertex to remove the singularity.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve

from reinforced_slicer.mesh.isosurface import IsoSurface
from reinforced_slicer.pathing.direction_field import DirectionField


def stripe_scalar_field(field: DirectionField) -> np.ndarray:
    """Solve for ``φ`` such that ``∇φ ≈ V_perp`` on the surface.

    Returns a per-vertex array. Iso-lines of ``φ`` at uniform spacing are
    stripes parallel to the original direction field.
    """
    surface = field.surface
    v_perp = field.perpendicular_in_tangent_plane()
    n_v = surface.n_vertices

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    b = np.zeros(n_v)

    for tri in surface.triangles:
        i, j, k = int(tri[0]), int(tri[1]), int(tri[2])
        p_i = surface.vertices[i]
        p_j = surface.vertices[j]
        p_k = surface.vertices[k]

        cross = np.cross(p_j - p_i, p_k - p_i)
        area2 = float(np.linalg.norm(cross))  # 2·area
        if area2 < 1e-15:
            continue
        area = 0.5 * area2
        normal = cross / area2

        # Per-vertex gradient of the barycentric coords. The edge opposite
        # vertex n is e_n; ∇λ_n = (n × e_n) / (2·area).
        e_i = p_k - p_j
        e_j = p_i - p_k
        e_k = p_j - p_i
        grad_lam = [
            np.cross(normal, e_i) / area2,
            np.cross(normal, e_j) / area2,
            np.cross(normal, e_k) / area2,
        ]
        verts = (i, j, k)

        # Target per-triangle gradient = mean of vertex V_perp, projected
        # back onto the triangle plane. Averaging is a standard piecewise-
        # linear interpolation choice for FE assembly.
        target = (v_perp[i] + v_perp[j] + v_perp[k]) / 3.0
        target = target - (target @ normal) * normal

        for a in range(3):
            b[verts[a]] += float(grad_lam[a] @ target) * area
            for c in range(3):
                rows.append(verts[a])
                cols.append(verts[c])
                data.append(float(grad_lam[a] @ grad_lam[c]) * area)

    laplacian = sp.coo_matrix((data, (rows, cols)), shape=(n_v, n_v)).tocsr()

    # Pin vertex 0 to φ=0: zero out its row, set diagonal to 1, set b[0]=0.
    # Loses symmetry but keeps the system well-conditioned.
    laplacian = laplacian.tolil()
    laplacian[0, :] = 0
    laplacian[0, 0] = 1.0
    b[0] = 0.0

    phi = spsolve(laplacian.tocsr(), b)
    return np.asarray(phi, dtype=float)


def estimate_field_spacing(field: DirectionField, phi: np.ndarray) -> float:
    """Estimate the characteristic ``φ`` increment per mm along the stripe-normal.

    Useful when picking iso-spacing: ``iso_spacing_phi = spacing_mm /
    estimate_field_spacing(field, phi)`` gives a φ-domain spacing that
    produces ~``spacing_mm`` apart stripes in world coordinates.
    """
    n_v = field.surface.n_vertices
    if n_v < 2:
        return 1.0
    # Take the mean |∇φ| over all triangles; equivalent to "rate of change
    # of φ per mm in the stripe-normal direction".
    surface = field.surface
    grads: list[float] = []
    for tri in surface.triangles:
        i, j, k = int(tri[0]), int(tri[1]), int(tri[2])
        p_i = surface.vertices[i]
        p_j = surface.vertices[j]
        p_k = surface.vertices[k]
        cross = np.cross(p_j - p_i, p_k - p_i)
        area2 = float(np.linalg.norm(cross))
        if area2 < 1e-15:
            continue
        normal = cross / area2
        e_i = p_k - p_j
        e_j = p_i - p_k
        e_k = p_j - p_i
        g = (
            phi[i] * np.cross(normal, e_i)
            + phi[j] * np.cross(normal, e_j)
            + phi[k] * np.cross(normal, e_k)
        ) / area2
        grads.append(float(np.linalg.norm(g)))
    if not grads:
        return 1.0
    mean = float(np.mean(grads))
    return mean if mean > 1e-12 else 1.0
