"""Naive G-code writer for the M0 planar slicer.

Targets a generic 3-axis FFF printer dialect (Marlin-like). Extrusion is
computed from the deposited bead's nominal cross-section so a slice can
actually be printed by hobby firmware for sanity checking.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from math import pi
from pathlib import Path

import numpy as np

from reinforced_slicer.slicing.planar import SlicedPart


@dataclass(frozen=True)
class GcodeConfig:
    nozzle_diameter: float = 0.4
    filament_diameter: float = 1.75
    print_speed_mm_min: float = 1800.0       # 30 mm/s
    travel_speed_mm_min: float = 4800.0      # 80 mm/s
    nozzle_temp_c: int = 210
    bed_temp_c: int = 60
    retract_mm: float = 1.0
    retract_speed_mm_min: float = 2400.0


def write_gcode(part: SlicedPart, path: str | Path, config: GcodeConfig | None = None) -> Path:
    """Write the sliced part to a .gcode file. Returns the path written to."""
    cfg = config or GcodeConfig()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_format_gcode(part, cfg))
    return out


def _format_gcode(part: SlicedPart, cfg: GcodeConfig) -> str:
    buf = StringIO()
    layer_height = part.config.layer_height
    extrusion_per_mm = _extrusion_per_mm(
        layer_height=layer_height,
        line_width=cfg.nozzle_diameter,
        filament_diameter=cfg.filament_diameter,
    )

    _write_header(buf, cfg)
    e_pos = 0.0
    for layer_index, layer in enumerate(part.layers):
        buf.write(f"; LAYER {layer_index} Z={layer.z:.3f}\n")
        buf.write(f"G0 Z{layer.z:.3f} F{cfg.travel_speed_mm_min:.0f}\n")
        for poly in layer.paths:
            if len(poly) < 2:
                continue
            e_pos = _write_polyline(buf, poly, e_pos, extrusion_per_mm, cfg)
    _write_footer(buf, cfg)
    return buf.getvalue()


def _write_header(buf: StringIO, cfg: GcodeConfig) -> None:
    buf.write("; reinforced-slicer M0 planar baseline\n")
    buf.write("G21 ; mm\n")
    buf.write("G90 ; absolute positioning\n")
    buf.write("M82 ; absolute extrusion\n")
    buf.write(f"M140 S{cfg.bed_temp_c}\n")
    buf.write(f"M104 S{cfg.nozzle_temp_c}\n")
    buf.write(f"M190 S{cfg.bed_temp_c}\n")
    buf.write(f"M109 S{cfg.nozzle_temp_c}\n")
    buf.write("G28 ; home\n")
    buf.write("G92 E0 ; reset extruder\n")


def _write_footer(buf: StringIO, cfg: GcodeConfig) -> None:
    buf.write("M104 S0\n")
    buf.write("M140 S0\n")
    buf.write("M84 ; disable steppers\n")


def _write_polyline(
    buf: StringIO,
    polyline: np.ndarray,
    e_pos: float,
    extrusion_per_mm: float,
    cfg: GcodeConfig,
) -> float:
    start = polyline[0]
    # Travel to start, retract.
    buf.write(f"G1 E{e_pos - cfg.retract_mm:.4f} F{cfg.retract_speed_mm_min:.0f}\n")
    buf.write(f"G0 X{start[0]:.3f} Y{start[1]:.3f} F{cfg.travel_speed_mm_min:.0f}\n")
    buf.write(f"G1 E{e_pos:.4f} F{cfg.retract_speed_mm_min:.0f}\n")
    buf.write(f"G1 F{cfg.print_speed_mm_min:.0f}\n")

    prev = start
    for point in polyline[1:]:
        dx = float(point[0] - prev[0])
        dy = float(point[1] - prev[1])
        dist = float(np.hypot(dx, dy))
        if dist < 1e-9:
            continue
        e_pos += dist * extrusion_per_mm
        buf.write(f"G1 X{point[0]:.3f} Y{point[1]:.3f} E{e_pos:.4f}\n")
        prev = point
    return e_pos


def _extrusion_per_mm(layer_height: float, line_width: float, filament_diameter: float) -> float:
    """Compute extruded filament length per mm of travel.

    Approximates the deposited bead as a rectangle of (line_width x layer_height).
    """
    bead_cross_section = line_width * layer_height
    filament_cross_section = pi * (filament_diameter / 2.0) ** 2
    return bead_cross_section / filament_cross_section
