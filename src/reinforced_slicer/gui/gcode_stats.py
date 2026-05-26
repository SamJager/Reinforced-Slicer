"""Parse emitted G-code for print-time and material-use statistics.

Operates on the G-code text directly rather than re-deriving from the
``SlicedPart`` so the same parser handles 3-axis output, 5-axis output
with rotary words, and (eventually) any third-party G-code a user
wants to inspect. Knows enough about Marlin dialect to be useful and
ignores everything it doesn't recognise.

Limitations:
- Feedrate-based time estimates are kinematic only — no acceleration
  or jerk modelling, so they over-predict actual print times by a
  noticeable margin (typical: 10–30 %).
- A/C rotary words contribute to neither distance nor time totals —
  this would need a kinematic model to translate angular motion to
  controller-limited time. Good enough for relative comparisons.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

_COORD = re.compile(r"([XYZE])(-?\d+(?:\.\d+)?)")
_FEED = re.compile(r"F(-?\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class GcodeStats:
    print_distance_mm: float
    travel_distance_mm: float
    total_extrusion_mm: float
    print_time_s: float
    travel_time_s: float
    total_time_s: float
    n_print_moves: int
    n_travel_moves: int
    bounding_box_min_mm: tuple[float, float, float]
    bounding_box_max_mm: tuple[float, float, float]

    @property
    def print_time_min(self) -> float:
        return self.print_time_s / 60.0

    @property
    def total_time_min(self) -> float:
        return self.total_time_s / 60.0

    def to_dict(self) -> dict[str, object]:
        return {
            "total_time": _fmt_time(self.total_time_s),
            "print_time": _fmt_time(self.print_time_s),
            "travel_time": _fmt_time(self.travel_time_s),
            "print_distance_mm": round(self.print_distance_mm, 1),
            "travel_distance_mm": round(self.travel_distance_mm, 1),
            "filament_used_mm": round(self.total_extrusion_mm, 1),
            "filament_used_m": round(self.total_extrusion_mm / 1000.0, 3),
            "n_print_moves": self.n_print_moves,
            "n_travel_moves": self.n_travel_moves,
            "bbox_min_mm": [round(v, 2) for v in self.bounding_box_min_mm],
            "bbox_max_mm": [round(v, 2) for v in self.bounding_box_max_mm],
        }


def parse_gcode_stats(gcode: str, default_feed_mm_per_min: float = 1800.0) -> GcodeStats:
    """Walk through ``gcode`` and accumulate distance/time/material totals."""
    pos = np.zeros(3)
    feedrate_mm_per_min = float(default_feed_mm_per_min)
    abs_extrusion = True
    last_e = 0.0
    e_axis_seen = False

    print_distance = 0.0
    travel_distance = 0.0
    extrusion_total = 0.0
    print_time = 0.0
    travel_time = 0.0
    n_print = 0
    n_travel = 0

    bbox_min = np.full(3, np.inf)
    bbox_max = np.full(3, -np.inf)

    for raw_line in gcode.splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        cmd = line.split(None, 1)[0].upper()

        if cmd == "M82":
            abs_extrusion = True
            continue
        if cmd == "M83":
            abs_extrusion = False
            continue
        if cmd == "G92":
            for letter, value in _COORD.findall(line):
                value = float(value)
                if letter == "E":
                    last_e = value
                    e_axis_seen = True
                elif letter == "X":
                    pos[0] = value
                elif letter == "Y":
                    pos[1] = value
                elif letter == "Z":
                    pos[2] = value
            continue

        if cmd not in ("G0", "G1"):
            continue

        feed_match = _FEED.search(line)
        if feed_match is not None:
            new_feed = float(feed_match.group(1))
            if new_feed > 0:
                feedrate_mm_per_min = new_feed

        new_pos = pos.copy()
        e_delta = 0.0
        had_e = False
        for letter, value in _COORD.findall(line):
            value = float(value)
            if letter == "X":
                new_pos[0] = value
            elif letter == "Y":
                new_pos[1] = value
            elif letter == "Z":
                new_pos[2] = value
            elif letter == "E":
                had_e = True
                if abs_extrusion:
                    e_delta = value - last_e
                    last_e = value
                else:
                    e_delta = value
                    last_e += value
                e_axis_seen = True

        distance = float(np.linalg.norm(new_pos - pos))
        pos = new_pos
        bbox_min = np.minimum(bbox_min, pos)
        bbox_max = np.maximum(bbox_max, pos)

        # Time at the current feedrate (mm/min → mm/s).
        feedrate_s = max(feedrate_mm_per_min / 60.0, 1e-6)
        time_s = distance / feedrate_s

        # Classify as print or travel:
        # - Real motion (distance > eps) with positive extrusion ⇒ print.
        # - Real motion without extrusion ⇒ travel.
        # - Pure E moves (retract / restart) don't move the head, so they
        #   contribute neither time nor distance to the totals.
        if distance > 1e-9 and had_e and e_delta > 1e-9:
            print_distance += distance
            print_time += time_s
            n_print += 1
            extrusion_total += e_delta
        elif distance > 1e-9:
            travel_distance += distance
            travel_time += time_s
            n_travel += 1
        elif had_e and e_delta > 0:
            extrusion_total += e_delta

    # If the file never touched the head, leave bbox at zeros (not infinities).
    if not np.all(np.isfinite(bbox_min)):
        bbox_min = np.zeros(3)
        bbox_max = np.zeros(3)

    return GcodeStats(
        print_distance_mm=print_distance,
        travel_distance_mm=travel_distance,
        total_extrusion_mm=extrusion_total,
        print_time_s=print_time,
        travel_time_s=travel_time,
        total_time_s=print_time + travel_time,
        n_print_moves=n_print,
        n_travel_moves=n_travel,
        bounding_box_min_mm=tuple(bbox_min.tolist()),
        bounding_box_max_mm=tuple(bbox_max.tolist()),
    )


def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.1f} min"
    hours = int(minutes // 60)
    rem = minutes - hours * 60
    return f"{hours} h {rem:.1f} min"
