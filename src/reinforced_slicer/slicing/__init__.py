"""Volume-to-layer slicing strategies."""

from reinforced_slicer.slicing.curvi_2d import (
    CurviSlicer2DConfig,
    CurviSlicer2DResult,
    solve_displacement,
    vertical_stretch,
)
from reinforced_slicer.slicing.curvi_3d import (
    CurviSlicer3DConfig,
    CurviSlicer3DResult,
    solve_displacement_3d,
    vertical_stretch_3d,
)
from reinforced_slicer.slicing.planar import slice_planar

__all__ = [
    "CurviSlicer2DConfig",
    "CurviSlicer2DResult",
    "CurviSlicer3DConfig",
    "CurviSlicer3DResult",
    "slice_planar",
    "solve_displacement",
    "solve_displacement_3d",
    "vertical_stretch",
    "vertical_stretch_3d",
]
