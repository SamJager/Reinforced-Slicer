"""Path generation on a slice or curved surface."""

from reinforced_slicer.pathing.curved import plan_path_on_surface
from reinforced_slicer.pathing.direction_field import (
    DirectionField,
    direction_field_from_xy_angle,
    project_target_direction,
)
from reinforced_slicer.pathing.fiber import plan_fiber_path_on_surface
from reinforced_slicer.pathing.iso_curves import IsoCurve, extract_iso_curves
from reinforced_slicer.pathing.stripe_field import (
    estimate_field_spacing,
    stripe_scalar_field,
)
from reinforced_slicer.pathing.zigzag import zigzag_fill

__all__ = [
    "DirectionField",
    "IsoCurve",
    "direction_field_from_xy_angle",
    "estimate_field_spacing",
    "extract_iso_curves",
    "plan_fiber_path_on_surface",
    "plan_path_on_surface",
    "project_target_direction",
    "stripe_scalar_field",
    "zigzag_fill",
]
