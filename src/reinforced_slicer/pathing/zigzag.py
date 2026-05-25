"""Zigzag (raster) infill for a 2D polygon."""

from __future__ import annotations

import numpy as np
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon


def zigzag_fill(polygon: Polygon | MultiPolygon, spacing: float, angle_deg: float = 0.0) -> list[np.ndarray]:
    """Generate a zigzag raster covering ``polygon``.

    Returns a list of polylines; each polyline is an (N, 2) array of XY points
    in print order. Adjacent rasters are joined end-to-end so the result is a
    single connected path per polygon component, with one polyline per component.
    """
    if polygon.is_empty:
        return []

    components: list[Polygon] = (
        list(polygon.geoms) if isinstance(polygon, MultiPolygon) else [polygon]
    )

    theta = np.deg2rad(angle_deg)
    c, s = np.cos(theta), np.sin(theta)
    rot = np.array([[c, -s], [s, c]])
    inv_rot = rot.T

    paths: list[np.ndarray] = []
    for component in components:
        coords = np.asarray(component.exterior.coords)
        local = coords @ rot
        y_min, y_max = local[:, 1].min(), local[:, 1].max()

        n_lines = max(1, int(np.ceil((y_max - y_min) / spacing)))
        # Rotate the component into local frame for line generation.
        component_local = _rotate_polygon(component, inv_rot)
        x_min, _, x_max, _ = component_local.bounds
        pad = max(1.0, (x_max - x_min) * 0.05)

        segments: list[np.ndarray] = []
        for i in range(n_lines + 1):
            y = y_min + i * spacing
            scan = LineString([(x_min - pad, y), (x_max + pad, y)])
            clipped = component_local.intersection(scan)
            for seg in _iter_linestrings(clipped):
                pts = np.asarray(seg.coords)
                if len(pts) < 2:
                    continue
                if i % 2 == 1:
                    pts = pts[::-1]
                segments.append(pts)

        if not segments:
            continue

        # Stitch segments into a single connected polyline by inserting jumps.
        stitched = [segments[0]]
        for seg in segments[1:]:
            stitched.append(seg)
        polyline_local = np.vstack(stitched)
        polyline_world = polyline_local @ inv_rot.T
        paths.append(polyline_world)

    return paths


def _rotate_polygon(poly: Polygon, mat: np.ndarray) -> Polygon:
    exterior = np.asarray(poly.exterior.coords) @ mat
    interiors = [np.asarray(ring.coords) @ mat for ring in poly.interiors]
    return Polygon(exterior, holes=interiors)


def _iter_linestrings(geom: object) -> list[LineString]:
    if isinstance(geom, LineString):
        return [geom] if not geom.is_empty else []
    if isinstance(geom, MultiLineString):
        return [ls for ls in geom.geoms if not ls.is_empty]
    if hasattr(geom, "geoms"):
        out: list[LineString] = []
        for g in geom.geoms:  # type: ignore[attr-defined]
            out.extend(_iter_linestrings(g))
        return out
    return []
