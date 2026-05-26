"""Per-vertex direction fields on a 3D triangle mesh.

A direction field assigns a unit tangent vector to each vertex of an
``IsoSurface`` (or any triangle mesh with per-vertex normals). For
fiber-aligned path planning we treat the field as **2-RoSy** — i.e. the
direction and its opposite are equivalent — so the path planner sees
"the fibers run along this line" without caring which way the line
points.

For M4.1 the field is constructed by projecting a single target XY
direction onto every vertex's tangent plane. Stress-aligned fields
(eigenvectors of the Cauchy stress tensor from FEA) come in M5; the
infrastructure here can absorb them by swapping the constructor.

Internally we store the field as a (N, 3) array of unit 3D vectors,
each approximately lying in its vertex's tangent plane. 2-RoSy is
handled at the consumers — when two neighbouring fields need to be
compared, the consumer flips the sign of one if their dot product is
negative.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reinforced_slicer.mesh.isosurface import IsoSurface


@dataclass(frozen=True)
class DirectionField:
    """A per-vertex unit tangent direction on a triangle mesh."""

    surface: IsoSurface
    vectors: np.ndarray  # (N, 3), each row a unit vector roughly in vertex normal's tangent plane

    def __post_init__(self) -> None:
        if self.vectors.shape != (self.surface.n_vertices, 3):
            raise ValueError(
                f"vectors must be shape ({self.surface.n_vertices}, 3), got {self.vectors.shape}"
            )

    def perpendicular_in_tangent_plane(self) -> np.ndarray:
        """Return ``n × v`` per vertex — the 90° rotated direction in the tangent plane.

        Used when going from a "stripe alignment direction" (paths along V)
        to the "stripe-perpendicular direction" (∇φ ⊥ stripes, ∥ V_perp).
        """
        out = np.cross(self.surface.normals, self.vectors)
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1.0
        return out / norms


def project_target_direction(
    surface: IsoSurface, target: np.ndarray
) -> DirectionField:
    """Project a single target 3D direction onto each vertex's tangent plane.

    The result is a smooth direction field whenever the surface itself is
    smooth — fine for tilted-cube test cases and for the M4.1 path planner.
    Stress alignment lands in M5 with a different constructor.

    ``target`` is normalised internally; you can pass any non-zero vector.
    """
    if surface.n_vertices == 0:
        return DirectionField(surface=surface, vectors=np.zeros((0, 3)))
    target = np.asarray(target, dtype=float).reshape(3)
    norm = float(np.linalg.norm(target))
    if norm < 1e-12:
        raise ValueError("target direction must be non-zero")
    target = target / norm

    # Project target onto each vertex's tangent plane: T_i = target - (target · n_i) n_i
    dots = surface.normals @ target  # (N,)
    projected = target[None, :] - dots[:, None] * surface.normals
    # If the projection is degenerate (target ∥ normal), fall back to an
    # arbitrary tangent — cross with the world Z if possible, else world X.
    bad = np.linalg.norm(projected, axis=1) < 1e-9
    if np.any(bad):
        fallback = np.cross(surface.normals[bad], np.array([0.0, 0.0, 1.0]))
        f_norms = np.linalg.norm(fallback, axis=1, keepdims=True)
        too_small = f_norms.squeeze() < 1e-9
        if np.any(too_small):
            alt = np.cross(surface.normals[bad][too_small], np.array([1.0, 0.0, 0.0]))
            fallback[too_small] = alt
            f_norms[too_small] = np.linalg.norm(alt, axis=1, keepdims=True)
        projected[bad] = fallback / np.maximum(f_norms, 1e-12)

    norms = np.linalg.norm(projected, axis=1, keepdims=True)
    norms[norms < 1e-12] = 1.0
    vectors = projected / norms
    return DirectionField(surface=surface, vectors=vectors)


def direction_field_from_xy_angle(
    surface: IsoSurface, angle_deg: float
) -> DirectionField:
    """Build a field whose target direction is in the XY plane at ``angle_deg``."""
    theta = np.deg2rad(angle_deg)
    target = np.array([np.cos(theta), np.sin(theta), 0.0])
    return project_target_direction(surface, target)
