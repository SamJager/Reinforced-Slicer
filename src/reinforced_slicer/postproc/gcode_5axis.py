"""5-axis G-code writer.

Bridges the slicer output (planar or curved layers with per-point cutter
poses) and the kinematics layer (any concrete ``Machine``). The slicer
hands over a sequence of ``CutterPose`` per path; this module runs them
through ``machine.solve_path`` to get joint trajectories with continuous
branch selection, then formats each joint state as a G-code line with
extra rotary-axis words.

Two emission targets are supported:

* ``write_gcode_5axis(part, machine, ...)`` — takes a ``SlicedPart`` from
  the planar slicer and lifts every path point to a ``CutterPose`` with
  the tool axis fixed at ``(0, 0, 1)``. This is the "5-axis kinematics
  for free" case: useful for validating the kinematics-to-G-code seam
  on output we already trust to be correct.
* ``write_oriented_paths_5axis(layers, machine, ...)`` — takes layers of
  oriented paths (lists of ``CutterPose``) directly. This is what later
  curved-layer / fiber-aware slicers will call.

Both write the same dialect: ``G1 X.. Y.. Z.. A.. C.. E..`` with A and C
in degrees (the convention RepRapFirmware, Marlin extensions, and most
controller firmwares expect for rotary axes).
"""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from math import degrees, pi
from pathlib import Path

import numpy as np

from reinforced_slicer.kinematics import (
    AcTableMachine,
    CutterPose,
    JointState,
    Machine,
)
from reinforced_slicer.postproc.gcode import GcodeConfig, _extrusion_per_mm
from reinforced_slicer.slicing.planar import SlicedPart

# A "layer" of oriented paths, as the curved-layer slicer will produce.
OrientedPath = list[CutterPose]
OrientedLayer = list[OrientedPath]


@dataclass(frozen=True)
class Gcode5AxisConfig:
    """Per-axis names and conversion choices for the 5-axis dialect."""

    rotary_letters: tuple[str, str] = ("A", "C")
    rotary_in_degrees: bool = True
    initialize_rotary_origin: bool = True  # emit "G92 A0 C0" after homing


def write_gcode_5axis(
    part: SlicedPart,
    machine: Machine,
    gcode_config: GcodeConfig | None = None,
    five_axis_config: Gcode5AxisConfig | None = None,
    path: str | Path | None = None,
) -> str:
    """Emit 5-axis G-code from a planar ``SlicedPart``.

    Every path point is lifted to a ``CutterPose`` with vertical tool
    axis. With an ``AcTableMachine`` this collapses to ``A = C = 0``
    throughout, so the X/Y/Z trajectory matches the planar 3-axis
    output exactly — the only difference is the extra A/C words. Useful
    as a seam validator before any curved-layer code is added.
    """
    layers = [_lift_planar_layer(layer.paths, layer.z) for layer in part.layers]
    return write_oriented_paths_5axis(
        layers,
        machine,
        gcode_config=gcode_config,
        five_axis_config=five_axis_config,
        path=path,
        layer_z=[layer.z for layer in part.layers],
        layer_height=part.config.layer_height,
        nozzle_diameter=(gcode_config or GcodeConfig()).nozzle_diameter,
    )


def write_oriented_paths_5axis(
    layers: list[OrientedLayer],
    machine: Machine,
    gcode_config: GcodeConfig | None = None,
    five_axis_config: Gcode5AxisConfig | None = None,
    path: str | Path | None = None,
    layer_z: list[float] | None = None,
    layer_height: float = 0.2,
    nozzle_diameter: float | None = None,
) -> str:
    """Emit 5-axis G-code from layers of oriented paths.

    ``layers`` is the curved-layer output format: one ``OrientedPath``
    per slice region, each path a list of ``CutterPose`` in print order.
    ``layer_z`` and ``layer_height`` are only used for the bead-volume
    extrusion calculation and for layer-comment annotations; they can
    be omitted for purely diagnostic G-code.
    """
    cfg_g = gcode_config or GcodeConfig()
    cfg_5 = five_axis_config or Gcode5AxisConfig()
    nozzle = nozzle_diameter if nozzle_diameter is not None else cfg_g.nozzle_diameter
    extrusion_per_mm = _extrusion_per_mm(
        layer_height=layer_height,
        line_width=nozzle,
        filament_diameter=cfg_g.filament_diameter,
    )

    buf = StringIO()
    _write_header(buf, cfg_g, cfg_5)

    seed: JointState | None = None
    e_pos = 0.0
    for layer_idx, oriented_paths in enumerate(layers):
        z_label = "" if layer_z is None else f" Z={layer_z[layer_idx]:.3f}"
        buf.write(f"; LAYER {layer_idx}{z_label}\n")
        for poses in oriented_paths:
            if len(poses) < 2:
                continue
            joints = machine.solve_path(poses, seed=seed)
            seed = joints[-1]
            e_pos = _emit_polyline(buf, joints, e_pos, extrusion_per_mm, cfg_g, cfg_5)

    _write_footer(buf, cfg_g)

    text = buf.getvalue()
    if path is not None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    return text


# --- internals -----------------------------------------------------------


def _lift_planar_layer(paths_2d: list[np.ndarray], z: float) -> OrientedLayer:
    """Wrap 2D polylines as poses with vertical tool axis."""
    up = np.array([0.0, 0.0, 1.0])
    out: OrientedLayer = []
    for path in paths_2d:
        out.append(
            [
                CutterPose(position=np.array([float(p[0]), float(p[1]), z]), tool_axis=up)
                for p in path
            ]
        )
    return out


def _write_header(buf: StringIO, cfg: GcodeConfig, cfg_5: Gcode5AxisConfig) -> None:
    a_letter, c_letter = cfg_5.rotary_letters
    buf.write("; reinforced-slicer M1 5-axis emitter\n")
    buf.write("G21 ; mm\n")
    buf.write("G90 ; absolute positioning\n")
    buf.write("M82 ; absolute extrusion\n")
    buf.write(f"M140 S{cfg.bed_temp_c}\n")
    buf.write(f"M104 S{cfg.nozzle_temp_c}\n")
    buf.write(f"M190 S{cfg.bed_temp_c}\n")
    buf.write(f"M109 S{cfg.nozzle_temp_c}\n")
    buf.write("G28 ; home\n")
    if cfg_5.initialize_rotary_origin:
        buf.write(f"G92 E0 {a_letter}0 {c_letter}0 ; reset extruder and rotaries\n")
    else:
        buf.write("G92 E0\n")


def _write_footer(buf: StringIO, cfg: GcodeConfig) -> None:
    buf.write("M104 S0\n")
    buf.write("M140 S0\n")
    buf.write("M84 ; disable steppers\n")


def _emit_polyline(
    buf: StringIO,
    joints: list[JointState],
    e_pos: float,
    extrusion_per_mm: float,
    cfg: GcodeConfig,
    cfg_5: Gcode5AxisConfig,
) -> float:
    if not joints:
        return e_pos
    a_letter, c_letter = cfg_5.rotary_letters
    scale = (180.0 / pi) if cfg_5.rotary_in_degrees else 1.0

    first = joints[0]
    x0, y0, z0 = first.linear
    a0, c0 = first.rotary * scale
    # Retract, travel to start (including rotary repositioning), unretract.
    buf.write(f"G1 E{e_pos - cfg.retract_mm:.4f} F{cfg.retract_speed_mm_min:.0f}\n")
    buf.write(
        f"G0 X{x0:.3f} Y{y0:.3f} Z{z0:.3f} "
        f"{a_letter}{a0:.3f} {c_letter}{c0:.3f} "
        f"F{cfg.travel_speed_mm_min:.0f}\n"
    )
    buf.write(f"G1 E{e_pos:.4f} F{cfg.retract_speed_mm_min:.0f}\n")
    buf.write(f"G1 F{cfg.print_speed_mm_min:.0f}\n")

    prev = first.linear
    for joint in joints[1:]:
        x, y, z = joint.linear
        a, c = joint.rotary * scale
        dist = float(np.linalg.norm(joint.linear - prev))
        if dist < 1e-9:
            continue
        e_pos += dist * extrusion_per_mm
        buf.write(
            f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} "
            f"{a_letter}{a:.3f} {c_letter}{c:.3f} E{e_pos:.4f}\n"
        )
        prev = joint.linear
    return e_pos


def default_ac_machine() -> AcTableMachine:
    """Convenience: an AcTableMachine with default config for CLI use."""
    return AcTableMachine()
