"""End-to-end fiber-aligned path planner on a curved iso-surface.

Wraps the M4.1–4.3 pieces:

1. **Direction field** — a per-vertex tangent direction chosen from the
   user's "fiber direction" preference (XY angle for now; FEA stress
   tensor in M5).
2. **Stripe scalar field** — solve a Poisson equation so that ``∇φ``
   is the 90°-rotated direction field.
3. **Iso-curves of φ** at uniform spacing — those are stripe lines
   parallel to the fiber direction.
4. Convert each curve to an ``OrientedPath`` with the surface normal
   as tool axis at every point.

Drop-in replacement for ``plan_path_on_surface`` (the XY-zigzag-on-
surface planner from M2c.3) when the caller wants fiber-aligned paths
instead of a simple raster.
"""

from __future__ import annotations

import numpy as np

from reinforced_slicer.kinematics import CutterPose
from reinforced_slicer.mesh.isosurface import IsoSurface
from reinforced_slicer.pathing.direction_field import direction_field_from_xy_angle
from reinforced_slicer.pathing.iso_curves import extract_iso_curves
from reinforced_slicer.pathing.stripe_field import (
    estimate_field_spacing,
    stripe_scalar_field,
)


def plan_fiber_path_on_surface(
    iso: IsoSurface,
    spacing: float = 0.4,
    fiber_angle_deg: float = 0.0,
    pad_fraction: float = 0.05,
    min_path_points: int = 2,
) -> list[list[CutterPose]]:
    """Generate fiber-aligned paths covering the iso-surface.

    ``fiber_angle_deg`` picks the desired fiber direction in the XY
    plane (0° = +X, 90° = +Y). Each vertex's tangent direction is
    obtained by projecting that target onto its tangent plane.

    Returns ``list[OrientedPath]`` — one path per iso-curve. Open
    polylines come first; closed loops follow.
    """
    if iso.is_empty():
        return []

    field = direction_field_from_xy_angle(iso, fiber_angle_deg)
    phi = stripe_scalar_field(field)
    rate_per_mm = estimate_field_spacing(field, phi)
    if rate_per_mm < 1e-12:
        return []
    phi_spacing = spacing * rate_per_mm

    # Pad the φ range so iso-lines don't pile up at the boundary where
    # the field's solution is least faithful.
    phi_min, phi_max = float(phi.min()), float(phi.max())
    span = phi_max - phi_min
    pad = pad_fraction * span
    start = phi_min + pad + phi_spacing / 2.0
    n_levels = max(1, int(np.floor((phi_max - pad - start) / phi_spacing)) + 1)
    levels = start + np.arange(n_levels) * phi_spacing

    paths: list[list[CutterPose]] = []
    for level in levels:
        for curve in extract_iso_curves(iso, phi, float(level)):
            if len(curve) < min_path_points:
                continue
            poses = [
                CutterPose(position=p, tool_axis=n)
                for p, n in zip(curve.points, curve.normals, strict=True)
            ]
            paths.append(poses)
    return paths
