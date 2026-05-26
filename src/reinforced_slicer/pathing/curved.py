"""Path generation on a curved iso-surface.

The algorithm in three steps:

1. **2D footprint** — project the iso-surface's XY positions to a
   2D polygon (convex hull for now; sufficient for the cube test
   geometries that drive M2c.4).
2. **2D zigzag** — fill the footprint with the existing planar
   ``zigzag_fill`` helper.
3. **Lift back to the surface** — for every 2D path point, find the
   iso-surface triangle whose XY projection contains it and barycentric-
   interpolate the z value and surface normal from the triangle's three
   vertices. The normal becomes the tool axis; the lifted (x, y, z)
   becomes the cutter position.

This is deliberately simple — no UV unwrapping, no surface-intrinsic
parameterisation, no geodesic-distance hatching. A 4-RoSy / stripe-
pattern path planner lands at M4 when the field-based fiber work
starts; until then, an XY-projected zigzag lifted onto the curved
layer is enough to validate the end-to-end pipeline.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import MultiPolygon, Polygon

from reinforced_slicer.kinematics import CutterPose
from reinforced_slicer.mesh.isosurface import IsoSurface
from reinforced_slicer.pathing.zigzag import zigzag_fill


def plan_path_on_surface(
    iso: IsoSurface,
    spacing: float = 0.4,
    angle_deg: float = 0.0,
    footprint: Polygon | MultiPolygon | None = None,
) -> list[list[CutterPose]]:
    """Generate zigzag paths covering the iso-surface, with per-point tool axes.

    Returns a list of paths (one per connected zigzag stroke). Each path
    is a list of ``CutterPose``; the position lies on the curved surface
    and the tool axis is the interpolated surface normal.

    ``footprint`` overrides the auto-computed XY projection — pass the
    part's true 2D outline when known (e.g. from the original mesh) for
    a tighter fill.
    """
    if iso.is_empty():
        return []
    if footprint is None:
        footprint = _xy_convex_hull(iso)
    if footprint.is_empty:
        return []

    polylines_2d = zigzag_fill(footprint, spacing=spacing, angle_deg=angle_deg)
    if not polylines_2d:
        return []

    paths: list[list[CutterPose]] = []
    for polyline in polylines_2d:
        poses = _lift_polyline(iso, polyline)
        if len(poses) >= 2:
            paths.append(poses)
    return paths


def _lift_polyline(iso: IsoSurface, polyline_2d: np.ndarray) -> list[CutterPose]:
    poses: list[CutterPose] = []
    for xy in polyline_2d:
        sample = _lift_point(iso, xy)
        if sample is None:
            continue
        position, normal = sample
        poses.append(CutterPose(position=position, tool_axis=normal))
    return poses


def _lift_point(iso: IsoSurface, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    """Find a triangle whose XY projection contains ``xy`` and interpolate.

    Returns the 3D position on the surface and the unit interpolated
    normal, or ``None`` if no triangle contains the point (e.g. the
    query lies outside the surface's footprint).
    """
    for tri in iso.triangles:
        a, b, c = iso.vertices[tri[0]], iso.vertices[tri[1]], iso.vertices[tri[2]]
        bary = _barycentric_2d(xy, a[:2], b[:2], c[:2])
        if bary is None:
            continue
        l0, l1, l2 = bary
        position = l0 * a + l1 * b + l2 * c
        normal = l0 * iso.normals[tri[0]] + l1 * iso.normals[tri[1]] + l2 * iso.normals[tri[2]]
        norm = float(np.linalg.norm(normal))
        if norm < 1e-12:
            normal = np.array([0.0, 0.0, 1.0])
        else:
            normal = normal / norm
        return position, normal
    return None


def _barycentric_2d(
    p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray
) -> tuple[float, float, float] | None:
    """Return barycentric coords of ``p`` in triangle ``(a, b, c)`` in 2D.

    Returns ``None`` if the triangle is degenerate or ``p`` is outside it.
    A small negative tolerance is applied so points on the boundary are
    accepted.
    """
    v0 = b - a
    v1 = c - a
    v2 = p - a
    d00 = float(v0 @ v0)
    d01 = float(v0 @ v1)
    d11 = float(v1 @ v1)
    d20 = float(v2 @ v0)
    d21 = float(v2 @ v1)
    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-18:
        return None
    l1 = (d11 * d20 - d01 * d21) / denom
    l2 = (d00 * d21 - d01 * d20) / denom
    l0 = 1.0 - l1 - l2
    tol = -1e-9
    if l0 >= tol and l1 >= tol and l2 >= tol:
        return (l0, l1, l2)
    return None


def _xy_convex_hull(iso: IsoSurface) -> Polygon:
    """Convex hull of ``iso``'s vertices in the XY plane as a shapely Polygon.

    Adequate for cube-shaped test geometries; a non-convex part outline
    needs a real footprint passed via the ``footprint`` argument.
    """
    points = iso.vertices[:, :2]
    if len(points) < 3:
        return Polygon()
    try:
        hull = ConvexHull(points)
    except Exception:
        return Polygon()
    return Polygon(points[hull.vertices])
