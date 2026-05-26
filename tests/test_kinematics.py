"""Kinematics: FK/IK round-trip, branch continuity, singularity smoothing."""

from __future__ import annotations

from math import pi

import numpy as np
import pytest

from reinforced_slicer.kinematics import (
    AcTableConfig,
    AcTableMachine,
    CutterPose,
    JointState,
    detect_singular_segments,
    max_rotary_jerk,
    smooth_singularities,
)


def _spherical_pose(theta: float, phi: float, position: tuple[float, float, float]) -> CutterPose:
    """Build a pose with tool axis on the unit sphere at (theta, phi)."""
    axis = np.array(
        [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
    )
    return CutterPose(position=np.array(position), tool_axis=axis)


class TestForwardInverseRoundTrip:
    def setup_method(self) -> None:
        self.machine = AcTableMachine()

    @pytest.mark.parametrize(
        "theta,phi",
        [
            (pi / 6, 0.0),
            (pi / 6, pi / 2),
            (pi / 4, pi / 4),
            (pi / 3, -pi / 3),
            (pi / 2 - 0.2, 1.7),
            (pi / 3, pi),
        ],
    )
    def test_ik_then_fk_recovers_pose(self, theta: float, phi: float) -> None:
        pose = _spherical_pose(theta, phi, position=(10.0, -5.0, 50.0))
        solutions = self.machine.ik(pose)
        assert solutions, "expected at least one IK solution for a non-singular pose"
        for joints in solutions:
            recovered = self.machine.fk(joints)
            assert recovered.position == pytest.approx(pose.position, abs=1e-9)
            assert recovered.tool_axis == pytest.approx(pose.tool_axis, abs=1e-9)

    def test_singular_pose_returns_single_solution(self) -> None:
        pose = CutterPose(position=np.zeros(3), tool_axis=np.array([0.0, 0.0, 1.0]))
        solutions = self.machine.ik(pose)
        assert len(solutions) == 1
        # FK round-trip still works at the singular pose.
        recovered = self.machine.fk(solutions[0])
        assert recovered.tool_axis == pytest.approx(pose.tool_axis, abs=1e-9)

    def test_ik_two_branches_for_generic_pose(self) -> None:
        pose = _spherical_pose(pi / 3, 0.7, position=(0.0, 0.0, 0.0))
        solutions = self.machine.ik(pose)
        assert len(solutions) == 2
        a_values = sorted(js.rotary[0] for js in solutions)
        assert a_values[0] < 0 < a_values[1], "expected ±A branches"


class TestBranchContinuity:
    def test_sweeping_path_does_not_swap_branches(self) -> None:
        machine = AcTableMachine()
        # Sweep azimuth phi from -π/3 to +π/3 at fixed tilt — far from
        # singularity, so a single branch should cover the whole sweep.
        poses = [
            _spherical_pose(pi / 4, phi, position=(0.0, 0.0, 0.0))
            for phi in np.linspace(-pi / 3, pi / 3, 50)
        ]
        path = machine.solve_path(poses)
        c_diffs = np.diff([js.rotary[1] for js in path])
        # No 2π flips in C: every step under one radian.
        assert np.max(np.abs(c_diffs)) < 1.0

    def test_path_through_low_tilt_keeps_c_unwrapped(self) -> None:
        machine = AcTableMachine()
        # Tilt drops to ~5° at midpoint — still non-singular but close.
        # Branch choice should remain stable; absolute C jumps must stay small.
        poses = [
            _spherical_pose(theta, pi / 6, position=(0.0, 0.0, 0.0))
            for theta in np.concatenate(
                [np.linspace(pi / 3, 0.1, 30), np.linspace(0.1, pi / 3, 30)[1:]]
            )
        ]
        path = machine.solve_path(poses)
        c_jumps = np.abs(np.diff([js.rotary[1] for js in path]))
        assert np.max(c_jumps) < 0.5


class TestSingularitySmoothing:
    def _near_singular_path(self) -> tuple[AcTableMachine, list[CutterPose], list[JointState]]:
        machine = AcTableMachine()
        # Path that swings tool axis through the +Z direction (singularity):
        # tilt theta goes 30° -> ~0° -> 30°, azimuth phi swings sign across
        # the singularity, forcing the IK to pick a large C jump.
        n = 41
        thetas = np.concatenate(
            [np.linspace(pi / 6, 0.01, n // 2), np.linspace(0.01, pi / 6, n - n // 2)]
        )
        phis = np.concatenate(
            [np.full(n // 2, -pi / 4), np.full(n - n // 2, 3 * pi / 4)]
        )
        poses = [
            _spherical_pose(t, p, position=(0.0, 0.0, 0.0))
            for t, p in zip(thetas, phis, strict=True)
        ]
        path = machine.solve_path(poses)
        return machine, poses, path

    def test_detector_flags_the_singular_zone(self) -> None:
        machine, poses, _ = self._near_singular_path()
        segments = detect_singular_segments(machine, poses, threshold=0.05)
        assert segments, "expected at least one near-singular segment"
        # The middle of the path is where tilt is smallest.
        middle = len(poses) // 2
        assert any(seg.start <= middle <= seg.end for seg in segments)

    def test_smoother_reduces_rotary_jerk(self) -> None:
        machine, poses, path = self._near_singular_path()
        segments = detect_singular_segments(machine, poses, threshold=0.1)
        smoothed = smooth_singularities(path, segments, pad=3)

        before = max_rotary_jerk(path)
        after = max_rotary_jerk(smoothed)
        # Smoothing should knock the worst rotary jerk down substantially.
        assert after < 0.5 * before, f"smoother did not improve jerk: {before=}, {after=}"

    def test_smoother_preserves_path_outside_segments(self) -> None:
        machine, poses, path = self._near_singular_path()
        segments = detect_singular_segments(machine, poses, threshold=0.1)
        smoothed = smooth_singularities(path, segments, pad=3)

        in_segment = np.zeros(len(path), dtype=bool)
        for seg in segments:
            in_segment[seg.start : seg.end + 1] = True
        for i, (orig, new) in enumerate(zip(path, smoothed, strict=True)):
            if not in_segment[i]:
                assert new.rotary == pytest.approx(orig.rotary, abs=1e-12)
                assert new.linear == pytest.approx(orig.linear, abs=1e-12)


class TestJointLimits:
    def test_ik_rejects_pose_outside_a_limits(self) -> None:
        cfg = AcTableConfig(a_min=-pi / 6, a_max=pi / 6)
        machine = AcTableMachine(cfg)
        # A pose tilting beyond ±30° can't be reached.
        pose = _spherical_pose(pi / 3, 0.0, position=(0.0, 0.0, 0.0))
        assert machine.ik(pose) == []

    def test_ik_rejects_pose_outside_linear_envelope(self) -> None:
        cfg = AcTableConfig(
            linear_min=np.array([-1.0, -1.0, -1.0]),
            linear_max=np.array([1.0, 1.0, 1.0]),
        )
        machine = AcTableMachine(cfg)
        pose = CutterPose(position=np.array([100.0, 0.0, 0.0]), tool_axis=np.array([0.0, 0.0, 1.0]))
        assert machine.ik(pose) == []
