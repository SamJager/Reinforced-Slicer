"""Machine kinematics: forward/inverse, singularity handling."""

from reinforced_slicer.kinematics.ac_table import AcTableConfig, AcTableMachine
from reinforced_slicer.kinematics.machine import (
    CutterPose,
    JointLimits,
    JointState,
    Machine,
)
from reinforced_slicer.kinematics.singularity import (
    SingularSegment,
    detect_singular_segments,
    max_rotary_jerk,
    smooth_singularities,
)

__all__ = [
    "AcTableConfig",
    "AcTableMachine",
    "CutterPose",
    "JointLimits",
    "JointState",
    "Machine",
    "SingularSegment",
    "detect_singular_segments",
    "max_rotary_jerk",
    "smooth_singularities",
]
