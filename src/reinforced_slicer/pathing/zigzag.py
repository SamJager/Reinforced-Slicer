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

    # Convention: row vectors, ``v_local = v_world @ rot``. ``rot`` is the
    # rotation matrix for column vectors; right-multiplying a row vector
    # by ``rot`` rotates the polygon by **-angle** into a frame where the
    # zigzag scan lines are horizontal. The inverse mapping back to world
    # coordinates is right-multiplication by ``rot.T``.
    theta = np.deg2rad(angle_deg)
    c, s = np.cos(theta), np.sin(theta)
    rot = np.array([[c, -s], [s, c]])

    paths: list[np.ndarray] = []
    for component in components:
        component_local = _rotate_polygon(component, rot)
        x_min, y_min, x_max, y_max = component_local.bounds
        pad = max(1.0, (x_max - x_min) * 0.05)
        n_lines = max(1, int(np.ceil((y_max - y_min) / spacing)))

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

        polyline_local = np.vstack(segments)
        polyline_world = polyline_local @ rot.T
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
