"""Volume-to-layer slicing strategies."""

from reinforced_slicer.slicing.curvi_2d import (
    CurviSlicer2DConfig,
    CurviSlicer2DResult,
    solve_displacement,
    vertical_stretch,
)
from reinforced_slicer.slicing.planar import slice_planar

__all__ = [
    "CurviSlicer2DConfig",
    "CurviSlicer2DResult",
    "slice_planar",
    "solve_displacement",
    "vertical_stretch",
]
