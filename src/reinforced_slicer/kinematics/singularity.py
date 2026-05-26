"""Singularity detection and trajectory smoothing.

When a 5-axis path crosses near the kinematic singularity (for an AC
table, when the tool axis aligns with the C-rotation axis), the IK
solution becomes ill-conditioned: small changes in the tool axis force
large rotary swings. This module:

1. Detects path segments where ``singularity_distance`` falls below a
   threshold ("near-singular zone").
2. Replaces the rotary trajectory in each such segment with a clamped
   cubic spline that passes smoothly through the segment endpoints —
   the GLT-2015 "pass-through" strategy from KNOWLEDGE.md §5.3.

The smoother does *not* claim to satisfy velocity/acceleration/jerk
limits exactly; it produces a C¹-continuous trajectory whose maximum
rotary jerk is bounded by the spline construction. A separate feedrate
scheduler (added in a later milestone) is responsible for enforcing
controller-level kinematic limits.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import CubicHermiteSpline

from reinforced_slicer.kinematics.machine import CutterPose, JointState, Machine


@dataclass(frozen=True)
class SingularSegment:
    """An inclusive index range ``[start, end]`` of a near-singular zone."""

    start: int
    end: int


def detect_singular_segments(
    machine: Machine,
    poses: list[CutterPose],
    threshold: float = 0.05,
    min_length: int = 2,
) -> list[SingularSegment]:
    """Return contiguous index ranges where ``singularity_distance < threshold``.

    ``threshold`` is in the same units as ``Machine.singularity_distance``.
    For ``AcTableMachine`` that is ``sin(A) = √(i² + j²)``; the default
    0.05 corresponds to tool axes within ~3° of the singular direction.

    Segments shorter than ``min_length`` points are dropped — isolated
    near-singular samples don't need smoothing.
    """
    in_zone = np.array(
        [machine.singularity_distance(pose) < threshold for pose in poses]
    )
    segments: list[SingularSegment] = []
    start: int | None = None
    for i, flag in enumerate(in_zone):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            if i - start >= min_length:
                segments.append(SingularSegment(start=start, end=i - 1))
            start = None
    if start is not None and len(in_zone) - start >= min_length:
        segments.append(SingularSegment(start=start, end=len(in_zone) - 1))
    return segments


def smooth_singularities(
    joints: list[JointState],
    segments: list[SingularSegment],
    pad: int = 2,
) -> list[JointState]:
    """Smooth the rotary axes of ``joints`` through every singular segment.

    ``pad`` controls how many points outside the segment are used to
    estimate the boundary derivatives — larger pad = smoother handoff,
    but more of the original trajectory is implicitly altered (the
    boundary points themselves are kept exactly).
    """
    if not segments:
        return list(joints)

    smoothed = list(joints)
    n = len(smoothed)
    for seg in segments:
        lo = max(0, seg.start - pad)
        hi = min(n - 1, seg.end + pad)
        if hi - lo < 3:
            continue  # not enough context to fit a cubic
        smoothed = _smooth_one_segment(smoothed, lo, hi, seg)
    return smoothed


def _smooth_one_segment(
    joints: list[JointState],
    lo: int,
    hi: int,
    seg: SingularSegment,
) -> list[JointState]:
    """Replace the rotary trajectory in [seg.start, seg.end] with a clamped
    cubic spline anchored at the pad endpoints (lo, hi)."""
    # Parameterise by linear-axis arc length so the spline speed matches
    # the toolhead's physical motion. Crucially, we do **not** include
    # the rotary axes in the parameter — if we did, the C-axis jump that
    # we are trying to smooth would dominate the parameterisation and
    # the "smoothed" spline would reproduce the same jump. Falls back
    # to uniform-index spacing when the linear motion is degenerate
    # (e.g. an in-place tool-axis sweep).
    s = _linear_arc_length_param(joints, lo, hi)

    n_rotary = joints[lo].rotary.shape[0]
    rotary = np.stack([j.rotary for j in joints[lo : hi + 1]])

    # Endpoint slopes from the pad regions (finite differences across the
    # surrounding samples, not the singular interior).
    ds_start = s[1] - s[0] if s[1] > s[0] else 1.0
    ds_end = s[-1] - s[-2] if s[-1] > s[-2] else 1.0
    slope_start = (rotary[1] - rotary[0]) / ds_start
    slope_end = (rotary[-1] - rotary[-2]) / ds_end

    smoothed = list(joints)
    for axis in range(n_rotary):
        spline = CubicHermiteSpline(
            x=np.array([s[0], s[-1]]),
            y=np.array([rotary[0, axis], rotary[-1, axis]]),
            dydx=np.array([slope_start[axis], slope_end[axis]]),
        )
        for offset, s_val in enumerate(s):
            idx = lo + offset
            if not (seg.start <= idx <= seg.end):
                continue  # keep pad endpoints untouched
            new_rotary = smoothed[idx].rotary.copy()
            new_rotary[axis] = float(spline(s_val))
            smoothed[idx] = JointState(
                linear=smoothed[idx].linear, rotary=new_rotary
            )
    return smoothed


def _linear_arc_length_param(joints: list[JointState], lo: int, hi: int) -> np.ndarray:
    """Cumulative arc length over ``joints[lo:hi+1]`` using linear axes only.

    Falls back to a uniform (index-based) parameterisation if the linear
    motion across the segment is negligible — otherwise the spline would
    be evaluated with all-equal x-values and the interpolation would be
    ill-defined.
    """
    n = hi - lo + 1
    s = np.zeros(n)
    for k in range(1, n):
        a = joints[lo + k - 1].linear
        b = joints[lo + k].linear
        s[k] = s[k - 1] + float(np.linalg.norm(b - a))
    if s[-1] < 1e-9:
        return np.arange(n, dtype=float)
    return s


def max_rotary_jerk(joints: list[JointState], ds: float = 1.0) -> float:
    """Cheap diagnostic: max absolute third difference of rotary axes.

    ``ds`` is the step in whatever parameter is used (defaults to unit
    index spacing). Real jerk needs a time parameter; this is only meant
    for unit tests that compare before/after smoothing.
    """
    if len(joints) < 4:
        return 0.0
    rotary = np.stack([j.rotary for j in joints])
    third = np.diff(rotary, n=3, axis=0) / (ds ** 3)
    return float(np.max(np.abs(third)))
