"""AC-table 5-axis machine: XYZ gantry + A-rotary + C-rotary table.

This is the configuration in KNOWLEDGE.md §5.1 (GLT 2015 / Sørby): three
linear axes (X, Y, Z) move the print head; the part is mounted on a
2-axis table where the A axis tilts about world X and the C axis spins
about its own (post-A-tilt) Z. It is one of the most common 5-axis
configurations in both CNC and AM hardware (Open5x, WPI thesis,
Murtezaoglu 2018, many commercial mills).

Convention used here
--------------------

Let the part frame be attached to the C-table. The rotation taking a
vector expressed in the part frame to the machine frame is

    R(A, C) = Rx(A) · Rz(-C)

so that the **tool axis** (which is fixed at ``(0, 0, 1)`` in the machine
frame) expressed in the part frame is

    (i, j, k) = R(A, C)^T · (0, 0, 1) = (-sin(C)·sin(A),
                                           cos(C)·sin(A),
                                           cos(A))

This differs from the KNOWLEDGE.md §5.1 formula by a sign convention on
the rotary axes — both are internally consistent and FK/IK round-trip
either way. The **singularity** is at
``i = j = 0`` (equivalently ``sin(A) = 0``, ``A ∈ {0, π}``), where the
tool axis aligns with the C-rotation axis and C becomes indeterminate.

The IK has two analytical branches, ``A = ±arccos(k)``. Along a path,
pick the branch that keeps the joint trajectory continuous; see
``solve_path``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, pi

import numpy as np

from reinforced_slicer.kinematics.machine import (
    CutterPose,
    JointLimits,
    JointState,
    Machine,
    rot_x,
    rot_z,
)


@dataclass(frozen=True)
class AcTableConfig:
    """Geometry and limits for an AC-table machine."""

    table_origin: np.ndarray = field(
        default_factory=lambda: np.zeros(3)
    )  # offset of table rotation centre in machine frame, mm
    linear_min: np.ndarray = field(default_factory=lambda: np.array([-200.0, -200.0, 0.0]))
    linear_max: np.ndarray = field(default_factory=lambda: np.array([200.0, 200.0, 300.0]))
    # A typically tilts ~±120°; C usually rotates without limit but we cap at ±2 turns
    # so optimisation has a finite domain.
    a_min: float = -2.0 * pi / 3.0
    a_max: float = 2.0 * pi / 3.0
    c_min: float = -4.0 * pi
    c_max: float = 4.0 * pi
    velocity_max: np.ndarray | None = None
    acceleration_max: np.ndarray | None = None
    jerk_max: np.ndarray | None = None


class AcTableMachine(Machine):
    """XYZ gantry + AC rotary table."""

    name = "ac_table"
    n_linear = 3
    n_rotary = 2

    def __init__(self, config: AcTableConfig | None = None) -> None:
        self.config = config or AcTableConfig()

    # --- Pose <-> joints ------------------------------------------------

    def fk(self, joints: JointState) -> CutterPose:
        if joints.linear.shape != (3,) or joints.rotary.shape != (2,):
            raise ValueError("AC-table joints must be linear[3] + rotary[2]")
        x, y, z = joints.linear
        a, c = joints.rotary

        rotation = _rotation(a, c)
        machine_pos = np.array([x, y, z]) - self.config.table_origin
        part_pos = rotation.T @ machine_pos
        tool_axis_part = rotation.T @ np.array([0.0, 0.0, 1.0])
        return CutterPose(position=part_pos, tool_axis=tool_axis_part)

    def ik(self, pose: CutterPose) -> list[JointState]:
        i, j, k = pose.tool_axis
        k_clipped = float(np.clip(k, -1.0, 1.0))
        sin_a_sq = max(0.0, 1.0 - k_clipped * k_clipped)
        sin_a = float(np.sqrt(sin_a_sq))

        if sin_a < _SINGULAR_EPS:
            # Tool axis aligned with C axis; C is indeterminate. Return a single
            # solution with C = 0 (planner can re-bias from the previous pose).
            a = 0.0 if k_clipped > 0 else pi
            solutions_ac: list[tuple[float, float]] = [(a, 0.0)]
        else:
            a_plus = float(np.arccos(k_clipped))            # in [0, π]
            a_minus = -a_plus
            # i = -sinC·sinA, j = cosC·sinA  =>  for +sinA: C = atan2(-i, j)
            c_plus = atan2(-i, j)
            c_minus = atan2(i, -j)
            solutions_ac = [(a_plus, c_plus), (a_minus, c_minus)]

        solutions: list[JointState] = []
        for a, c in solutions_ac:
            if not self._rotary_in_range(a, c):
                continue
            rotation = _rotation(a, c)
            machine_pos = rotation @ pose.position + self.config.table_origin
            if not self._linear_in_range(machine_pos):
                continue
            solutions.append(
                JointState(linear=machine_pos, rotary=np.array([a, c]))
            )
        return solutions

    def singularity_distance(self, pose: CutterPose) -> float:
        # Distance is ``sin(A)``, which equals √(i² + j²) — zero exactly at the
        # singularity, 1 at the equator of the orientation sphere.
        i, j, _ = pose.tool_axis
        return float(np.hypot(i, j))

    @property
    def limits(self) -> JointLimits:
        cfg = self.config
        pos_min = np.concatenate([cfg.linear_min, np.array([cfg.a_min, cfg.c_min])])
        pos_max = np.concatenate([cfg.linear_max, np.array([cfg.a_max, cfg.c_max])])
        return JointLimits(
            position_min=pos_min,
            position_max=pos_max,
            velocity_max=cfg.velocity_max,
            acceleration_max=cfg.acceleration_max,
            jerk_max=cfg.jerk_max,
        )

    # --- Range checks ---------------------------------------------------

    def _rotary_in_range(self, a: float, c: float) -> bool:
        cfg = self.config
        return cfg.a_min <= a <= cfg.a_max and cfg.c_min <= c <= cfg.c_max

    def _linear_in_range(self, machine_pos: np.ndarray) -> bool:
        cfg = self.config
        return bool(
            np.all(machine_pos >= cfg.linear_min - 1e-9)
            and np.all(machine_pos <= cfg.linear_max + 1e-9)
        )

    # --- Path-level branch selection -----------------------------------

    def solve_path(
        self,
        poses: list[CutterPose],
        seed: JointState | None = None,
    ) -> list[JointState]:
        """Solve IK along a path with continuity-aware branch selection.

        At every pose we evaluate all IK branches, unwrap their C values
        against the previous joint state, and pick whichever solution lies
        closest in weighted joint space. The continuity term dominates so
        the planner rarely flips branches mid-path; when it does, it's
        because the alternative branch is geometrically closer.
        """
        if not poses:
            return []

        previous: JointState | None = seed
        out: list[JointState] = []
        for pose in poses:
            candidates = self.ik(pose)
            if not candidates:
                raise ValueError(
                    f"No IK solution for pose at {pose.position.tolist()}"
                )
            if previous is None:
                # Cold start — prefer the solution with positive A so the
                # rest of the path has a definite starting branch.
                candidates.sort(key=lambda js: (-js.rotary[0], abs(js.rotary[1])))
                chosen = candidates[0]
            else:
                chosen = _closest_solution(candidates, previous)
            out.append(chosen)
            previous = chosen
        return out


# --- internals -------------------------------------------------------------

_SINGULAR_EPS = 1e-6


def _rotation(a: float, c: float) -> np.ndarray:
    """R(A, C) = Rx(A) · Rz(-C)."""
    return rot_x(a) @ rot_z(-c)


def _closest_solution(
    candidates: list[JointState],
    previous: JointState,
) -> JointState:
    best_idx = 0
    best_cost = float("inf")
    for idx, candidate in enumerate(candidates):
        unwrapped = _unwrap_rotary(candidate, previous)
        cost = _trajectory_cost(unwrapped, previous)
        if cost < best_cost:
            best_cost = cost
            best_idx = idx
    chosen = candidates[best_idx]
    return _unwrap_rotary(chosen, previous)


def _unwrap_rotary(candidate: JointState, previous: JointState) -> JointState:
    """Add/subtract 2π·k to C so it lies in the same revolution as previous.C."""
    new_rotary = candidate.rotary.copy()
    prev_c = previous.rotary[1]
    delta = new_rotary[1] - prev_c
    if abs(delta) > pi:
        k = round(delta / (2.0 * pi))
        new_rotary[1] -= 2.0 * pi * k
    return JointState(linear=candidate.linear, rotary=new_rotary)


def _trajectory_cost(candidate: JointState, previous: JointState) -> float:
    """Weighted joint-space distance; rotary axes weighted by ~100 mm/rad
    so a 10° rotary jump is comparable to a ~17 mm linear jump."""
    linear_diff = candidate.linear - previous.linear
    rotary_diff = candidate.rotary - previous.rotary
    rotary_weight = 100.0  # mm per radian
    return float(np.hypot(np.linalg.norm(linear_diff), rotary_weight * np.linalg.norm(rotary_diff)))
