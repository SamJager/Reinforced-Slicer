"""Iso-curve extraction on a 3D triangle mesh.

Given an ``IsoSurface`` (vertices + triangles + per-vertex normals) and
a per-vertex scalar field, extract polylines along the iso-contours at
specified levels. This is the marching-triangles step that converts a
stripe scalar field (from ``stripe_field``) into stripe paths.

The output is a list of polylines per level — each polyline has ordered
3D points and unit normals interpolated from the surface vertex normals
(those normals become tool axes in the slicer pipeline).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reinforced_slicer.mesh.isosurface import IsoSurface

_SNAP_TOL = 1e-9


@dataclass(frozen=True)
class IsoCurve:
    """A single iso-contour as an ordered polyline on a 3D surface."""

    points: np.ndarray  # (N, 3)
    normals: np.ndarray  # (N, 3), unit
    closed: bool

    def __len__(self) -> int:
        return int(self.points.shape[0])


def extract_iso_curves(
    surface: IsoSurface, field: np.ndarray, level: float
) -> list[IsoCurve]:
    """Extract iso-contours of ``field`` at ``level`` on a 3D surface.

    Returns a list of ``IsoCurve``; each is one connected polyline.
    Returns an empty list when the level doesn't intersect the field.
    """
    if field.shape != (surface.n_vertices,):
        raise ValueError(f"field must be shape ({surface.n_vertices},)")

    points: list[np.ndarray] = []
    normals: list[np.ndarray] = []
    edge_cache: dict[tuple[int, int], int] = {}
    vertex_cache: dict[int, int] = {}

    def ensure_vertex_point(v: int) -> int:
        if v in vertex_cache:
            return vertex_cache[v]
        idx = len(points)
        points.append(surface.vertices[v].copy())
        normals.append(surface.normals[v].copy())
        vertex_cache[v] = idx
        return idx

    def ensure_iso_point(a: int, b: int) -> int:
        """Interpolate the iso-crossing on edge (a, b), with snapping."""
        f_a, f_b = float(field[a]), float(field[b])
        denom = f_b - f_a
        if abs(denom) < 1e-15:
            return ensure_vertex_point(a)
        t = (level - f_a) / denom
        if t <= _SNAP_TOL:
            return ensure_vertex_point(a)
        if t >= 1.0 - _SNAP_TOL:
            return ensure_vertex_point(b)
        key = (min(a, b), max(a, b))
        cached = edge_cache.get(key)
        if cached is not None:
            return cached
        p = surface.vertices[a] + t * (surface.vertices[b] - surface.vertices[a])
        n_raw = surface.normals[a] + t * (surface.normals[b] - surface.normals[a])
        norm = float(np.linalg.norm(n_raw))
        n = n_raw / norm if norm > 1e-12 else np.array([0.0, 0.0, 1.0])
        idx = len(points)
        points.append(p)
        normals.append(n)
        edge_cache[key] = idx
        return idx

    # Per-triangle: collect line segments.
    segments: list[tuple[int, int]] = []
    for tri in surface.triangles:
        v = [int(tri[0]), int(tri[1]), int(tri[2])]
        f = [float(field[v[k]]) - level for k in range(3)]
        # Classify edges that cross the iso-value.
        edges = ((0, 1), (1, 2), (2, 0))
        crossings: list[int] = []
        for ea, eb in edges:
            # An edge crosses if its endpoints' field deltas have opposite
            # signs, or if exactly one endpoint sits on the iso.
            fa, fb = f[ea], f[eb]
            same_sign = (fa > _SNAP_TOL and fb > _SNAP_TOL) or (
                fa < -_SNAP_TOL and fb < -_SNAP_TOL
            )
            if same_sign:
                continue
            both_on_iso = abs(fa) <= _SNAP_TOL and abs(fb) <= _SNAP_TOL
            if both_on_iso:
                # Whole edge sits on the iso — emit a segment for it later.
                continue
            crossings.append(ensure_iso_point(v[ea], v[eb]))

        # Dedup: when the iso passes through a vertex, two of the
        # "crossings" snap to the same mesh vertex.
        unique = list(dict.fromkeys(crossings))
        if len(unique) == 2:
            segments.append((unique[0], unique[1]))

    if not segments:
        return []

    return _chain_segments(segments, np.asarray(points), np.asarray(normals))


def extract_iso_curves_uniform(
    surface: IsoSurface,
    field: np.ndarray,
    spacing: float,
    pad_fraction: float = 0.05,
) -> list[list[IsoCurve]]:
    """Convenience: extract iso-curves at uniform levels spanning ``field``.

    ``pad_fraction`` shrinks the range at both ends so iso-lines don't
    sit on the boundary where the field's gradient is unreliable.
    Returns a list of per-level lists of curves.
    """
    f_min, f_max = float(field.min()), float(field.max())
    span = f_max - f_min
    pad = pad_fraction * span
    start = f_min + pad + spacing / 2.0
    n = max(1, int(np.floor((f_max - pad - start) / spacing)) + 1)
    levels = start + np.arange(n) * spacing
    return [extract_iso_curves(surface, field, float(c)) for c in levels]


# --- chaining ------------------------------------------------------------


def _chain_segments(
    segments: list[tuple[int, int]],
    points: np.ndarray,
    normals: np.ndarray,
) -> list[IsoCurve]:
    """Link segments sharing an endpoint into ordered polylines."""
    # adjacency[point_idx] = [(other_point_idx, segment_idx), ...]
    adjacency: dict[int, list[tuple[int, int]]] = {}
    for s_idx, (a, b) in enumerate(segments):
        adjacency.setdefault(a, []).append((b, s_idx))
        adjacency.setdefault(b, []).append((a, s_idx))

    used = [False] * len(segments)
    polylines: list[IsoCurve] = []

    def walk(start: int) -> list[int]:
        """Walk a chain starting from ``start``, returning point-index sequence."""
        chain = [start]
        prev = start
        while True:
            options = [
                (nbr, s_idx) for nbr, s_idx in adjacency.get(prev, []) if not used[s_idx]
            ]
            if not options:
                break
            nbr, s_idx = options[0]
            used[s_idx] = True
            chain.append(nbr)
            prev = nbr
            if prev == start:
                break
        return chain

    # Pass 1: chains that have an open end (degree-1 endpoint).
    open_endpoints = [pt for pt, nbrs in adjacency.items() if len(nbrs) == 1]
    for start in open_endpoints:
        # An endpoint may have been used as the end of another chain already.
        if any(not used[s_idx] for _, s_idx in adjacency.get(start, [])):
            chain = walk(start)
            if len(chain) >= 2:
                closed = chain[0] == chain[-1]
                polylines.append(_polyline_from_chain(chain, points, normals, closed=closed))

    # Pass 2: remaining segments are part of closed loops; pick any unused
    # segment and walk it.
    for s_idx, (a, _) in enumerate(segments):
        if used[s_idx]:
            continue
        chain = walk(a)
        if len(chain) >= 2:
            closed = chain[0] == chain[-1]
            polylines.append(_polyline_from_chain(chain, points, normals, closed=closed))

    return polylines


def _polyline_from_chain(
    chain: list[int],
    points: np.ndarray,
    normals: np.ndarray,
    closed: bool,
) -> IsoCurve:
    pts = points[chain]
    nrms = normals[chain]
    return IsoCurve(points=pts, normals=nrms, closed=closed)
