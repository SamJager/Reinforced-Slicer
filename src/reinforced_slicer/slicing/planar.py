"""Minimal 3-axis planar slicer.

This is the M0 baseline — proves that mesh I/O, slicing, and path generation
hang together. It is *not* a production slicer: no perimeters, no supports,
no temperature/cooling logic, no retraction tuning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import trimesh
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from reinforced_slicer.pathing.zigzag import zigzag_fill


@dataclass(frozen=True)
class SliceLayer:
    """A single planar slice at constant Z, filled with zigzag paths."""

    z: float
    polygons: list[Polygon]
    paths: list[np.ndarray]  # each (N, 2) XY polyline


@dataclass(frozen=True)
class PlanarSliceConfig:
    layer_height: float = 0.2
    infill_spacing: float = 0.4
    infill_angle_deg: float = 45.0
    alternate_angle: bool = True  # rotate 90 deg every other layer


@dataclass
class SlicedPart:
    layers: list[SliceLayer] = field(default_factory=list)
    config: PlanarSliceConfig = field(default_factory=PlanarSliceConfig)


def slice_planar(mesh: trimesh.Trimesh, config: PlanarSliceConfig | None = None) -> SlicedPart:
    """Slice a watertight triangle mesh into horizontal layers with zigzag infill."""
    cfg = config or PlanarSliceConfig()

    z_min, z_max = float(mesh.bounds[0, 2]), float(mesh.bounds[1, 2])
    z_start = z_min + cfg.layer_height / 2.0
    n_layers = max(1, int(np.floor((z_max - z_start) / cfg.layer_height)) + 1)
    z_values = z_start + np.arange(n_layers) * cfg.layer_height

    sections = mesh.section_multiplane(
        plane_origin=[0.0, 0.0, 0.0],
        plane_normal=[0.0, 0.0, 1.0],
        heights=z_values.tolist(),
    )

    part = SlicedPart(config=cfg)
    for i, (z, section) in enumerate(zip(z_values, sections, strict=True)):
        if section is None:
            continue
        polygons = _polygons_from_path2d(section)
        if not polygons:
            continue

        angle = cfg.infill_angle_deg + (90.0 if cfg.alternate_angle and i % 2 else 0.0)
        paths: list[np.ndarray] = []
        for poly in polygons:
            paths.extend(zigzag_fill(poly, spacing=cfg.infill_spacing, angle_deg=angle))

        part.layers.append(SliceLayer(z=float(z), polygons=polygons, paths=paths))

    return part


def _polygons_from_path2d(section: trimesh.path.Path2D) -> list[Polygon]:
    """Convert a trimesh Path2D cross-section into shapely polygons.

    trimesh's polygons_full handles outer/hole pairing for us.
    """
    polygons: list[Polygon] = []
    for poly in section.polygons_full:
        if poly is None or poly.is_empty:
            continue
        polygons.append(poly)
    if not polygons:
        return []

    # Defensive union — collapses any degenerate overlaps.
    merged = unary_union(polygons)
    if isinstance(merged, Polygon):
        return [merged]
    if isinstance(merged, MultiPolygon):
        return list(merged.geoms)
    return polygons
