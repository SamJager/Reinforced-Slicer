"""M0 smoke tests: a 10 mm cube must slice and produce valid G-code."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import trimesh

from reinforced_slicer.postproc.gcode import GcodeConfig, write_gcode
from reinforced_slicer.slicing.planar import PlanarSliceConfig, slice_planar


def _cube(side: float = 10.0) -> trimesh.Trimesh:
    cube = trimesh.creation.box(extents=(side, side, side))
    cube.apply_translation([side / 2.0, side / 2.0, side / 2.0])
    return cube


def test_cube_layer_count_matches_layer_height() -> None:
    cube = _cube(10.0)
    cfg = PlanarSliceConfig(layer_height=0.2, infill_spacing=0.4)
    part = slice_planar(cube, cfg)
    # 10 mm height with 0.2 mm layers and centred z_start -> 50 layers.
    assert len(part.layers) == 50


def test_cube_layer_paths_cover_interior() -> None:
    cube = _cube(10.0)
    part = slice_planar(cube, PlanarSliceConfig(layer_height=0.2, infill_spacing=0.4))
    first = part.layers[0]
    assert first.polygons, "expected at least one polygon per slice"
    assert first.paths, "expected at least one infill polyline per slice"
    pts = np.vstack(first.paths)
    # Every path point should lie inside the cube's XY footprint (with tolerance).
    assert pts[:, 0].min() >= -1e-6
    assert pts[:, 0].max() <= 10.0 + 1e-6
    assert pts[:, 1].min() >= -1e-6
    assert pts[:, 1].max() <= 10.0 + 1e-6


def test_gcode_has_layers_and_motion(tmp_path: Path) -> None:
    cube = _cube(10.0)
    part = slice_planar(cube, PlanarSliceConfig(layer_height=0.5, infill_spacing=0.4))
    out = write_gcode(part, tmp_path / "cube.gcode", GcodeConfig())
    text = out.read_text()
    assert text.startswith("; reinforced-slicer M0")
    layer_comments = re.findall(r"^; LAYER \d+", text, re.MULTILINE)
    assert len(layer_comments) == len(part.layers) == 20
    # At least one extruding move per layer.
    moves = re.findall(r"^G1 X[-\d.]+ Y[-\d.]+ E[-\d.]+", text, re.MULTILINE)
    assert len(moves) >= len(part.layers)
