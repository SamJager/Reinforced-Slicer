"""Path generation on a slice or curved surface."""

from reinforced_slicer.pathing.curved import plan_path_on_surface
from reinforced_slicer.pathing.zigzag import zigzag_fill

__all__ = ["plan_path_on_surface", "zigzag_fill"]
