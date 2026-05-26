"""Abstract machine model for multi-axis additive manufacturing.

Conventions used throughout the kinematics package
--------------------------------------------------

* **Part frame** is the frame attached to the printed object. The slicer
  reasons about cutter locations (where the nozzle should deposit) and tool
  axes (which way the nozzle should point) entirely in this frame.
* **Machine frame** is fixed to the machine's base. Linear axes report
  positions in this frame; rotary axes carry either the tool or the part.
* A **CutterPose** is the slicer-side description of one path point: a
  cutter contact point in part coordinates plus a unit tool-axis vector
  (also expressed in part coordinates) telling the machine which way the
  nozzle should point when it touches that point.
* A **JointState** is the machine-side description of the same point:
  linear axis positions plus rotary axis values (radians).

A concrete ``Machine`` implements forward kinematics ``fk(joints) -> pose``
and inverse kinematics ``ik(pose) -> [joints, ...]``. IK can return more
than one solution; selecting a kinematic branch that keeps the trajectory
continuous is the planner's job (see ``ac_table.solve_path``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class CutterPose:
    """A point on the toolpath, expressed in the part frame.

    ``position`` is the cutter contact point in millimetres. ``tool_axis``
    is the unit direction the nozzle should point along — pointing *away*
    from the part surface, i.e. roughly the outward normal of the curved
    layer in fiber-aware slicing.
    """

    position: np.ndarray  # shape (3,), millimetres
    tool_axis: np.ndarray  # shape (3,), unit vector

    def __post_init__(self) -> None:
        if self.position.shape != (3,):
            raise ValueError(f"position must be shape (3,), got {self.position.shape}")
        if self.tool_axis.shape != (3,):
            raise ValueError(f"tool_axis must be shape (3,), got {self.tool_axis.shape}")
        norm = float(np.linalg.norm(self.tool_axis))
        if not np.isfinite(norm) or abs(norm - 1.0) > 1e-6:
            raise ValueError(f"tool_axis must be a unit vector, norm={norm}")


@dataclass(frozen=True)
class JointState:
    """Machine-frame joint values.

    ``linear`` carries the linear-axis positions in millimetres in the
    order the machine reports them (typically X, Y, Z). ``rotary`` carries
    rotary-axis positions in radians in axis order (e.g. A then C for an
    AC-table configuration).
    """

    linear: np.ndarray  # shape (n_linear,), mm
    rotary: np.ndarray  # shape (n_rotary,), radians

    def as_vector(self) -> np.ndarray:
        return np.concatenate([self.linear, self.rotary])


@dataclass(frozen=True)
class JointLimits:
    """Per-axis position, velocity, acceleration and jerk envelope.

    Vectors are concatenated in ``(linear..., rotary...)`` order matching
    ``JointState.as_vector()``. Velocity/accel/jerk are absolute caps
    (the same number is applied in both directions). ``None`` for a limit
    means unconstrained.
    """

    position_min: np.ndarray
    position_max: np.ndarray
    velocity_max: np.ndarray | None = None
    acceleration_max: np.ndarray | None = None
    jerk_max: np.ndarray | None = None


class Machine(ABC):
    """Abstract base for a multi-axis machine kinematic model."""

    name: str = "abstract"
    n_linear: int = 3
    n_rotary: int = 2

    @abstractmethod
    def fk(self, joints: JointState) -> CutterPose:
        """Forward kinematics: joint values -> cutter pose in part frame."""

    @abstractmethod
    def ik(self, pose: CutterPose) -> list[JointState]:
        """Inverse kinematics: cutter pose -> all valid joint solutions.

        Multiple solutions correspond to distinct kinematic branches
        (for a 5-axis machine, typically two). The planner picks a branch
        that yields a continuous joint trajectory along the path.
        """

    @abstractmethod
    def singularity_distance(self, pose: CutterPose) -> float:
        """Return a non-negative scalar that is zero at a singular pose.

        Larger values mean the pose is further from the singularity. The
        exact units are machine-specific; only comparisons across nearby
        poses on the same machine are meaningful.
        """

    @property
    @abstractmethod
    def limits(self) -> JointLimits:
        """Joint-space limits used by trajectory smoothing and validation."""


# --- Helper rotations ---------------------------------------------------


def rot_x(angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rot_y(angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rot_z(angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
