"""End-to-end curved-layer 5-axis pipeline.

Bundles the M2 pieces into a single convenience function:

    TetMesh + face indices
        │
        ▼  solve_displacement_3d (M2c.1, OSQP)
    displacement h(v)
        │
        ▼  field f(v) = z(v) + h(v)
        ▼  extract_curved_layers (M2c.2, marching tets)
    list[IsoSurface]
        │
        ▼  plan_path_on_surface per layer (M2c.3)
    list[OrientedLayer]  # list of list of CutterPose
        │
        ▼  write_oriented_paths_5axis (M1.5)
    5-axis G-code

The pipeline is intentionally small and parameter-light — it's the
M2c.4 integration that proves all the pieces hold hands. Real
production use would expose more knobs (per-layer infill pattern,
adaptive layer heights, perimeter generation, etc.); add them as
keyword arguments here when the need arises.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from reinforced_slicer.kinematics import Machine
from reinforced_slicer.mesh.isosurface import extract_curved_layers
from reinforced_slicer.mesh.tet import TetMesh
from reinforced_slicer.pathing.curved import plan_path_on_surface
from reinforced_slicer.pathing.fiber import plan_fiber_path_on_surface
from reinforced_slicer.postproc.gcode import GcodeConfig
from reinforced_slicer.postproc.gcode_5axis import (
    Gcode5AxisConfig,
    write_oriented_paths_5axis,
)
from reinforced_slicer.slicing.curvi_3d import (
    CurviSlicer3DConfig,
    CurviSlicer3DResult,
    solve_displacement_3d,
)


@dataclass(frozen=True)
class CurvedSlicePipelineResult:
    """Diagnostic artefacts from a pipeline run, plus the emitted G-code."""

    curvi_result: CurviSlicer3DResult
    field: np.ndarray
    n_layers: int
    n_paths: int
    n_path_points: int
    gcode: str


def curved_layer_5axis_pipeline(
    tet_mesh: TetMesh,
    top_indices: np.ndarray,
    bottom_indices: np.ndarray,
    machine: Machine,
    *,
    layer_height: float = 0.2,
    path_spacing: float = 0.4,
    curvi_config: CurviSlicer3DConfig | None = None,
    gcode_config: GcodeConfig | None = None,
    five_axis_config: Gcode5AxisConfig | None = None,
    output_path: Path | None = None,
    alternate_infill_angle: bool = True,
    path_strategy: str = "zigzag",
    fiber_angle_deg: float = 0.0,
) -> CurvedSlicePipelineResult:
    """Run the full QP → iso-surfaces → curved paths → 5-axis G-code pipeline.

    ``path_strategy`` picks the per-layer toolpath generator:

    * ``"zigzag"`` (default) — the XY-zigzag-projected-onto-surface
      planner from M2c.3. Alternates 0°/90° between layers if
      ``alternate_infill_angle`` is set.
    * ``"fiber"`` — the M4 fiber-aligned planner: stripe scalar field
      whose iso-lines run parallel to ``fiber_angle_deg`` (XY plane,
      projected onto each curved layer's tangent plane).
    """
    curvi_result = solve_displacement_3d(
        tet_mesh, top_indices, bottom_indices, curvi_config
    )
    field = tet_mesh.vertices[:, 2] + curvi_result.displacement
    iso_layers = extract_curved_layers(tet_mesh, field, layer_height=layer_height)

    oriented_layers: list[list[list]] = []
    total_paths = 0
    total_points = 0
    for i, iso in enumerate(iso_layers):
        if path_strategy == "fiber":
            angle = fiber_angle_deg + (90.0 if alternate_infill_angle and i % 2 else 0.0)
            paths = plan_fiber_path_on_surface(iso, spacing=path_spacing, fiber_angle_deg=angle)
        elif path_strategy == "zigzag":
            angle = 90.0 if (alternate_infill_angle and i % 2) else 0.0
            paths = plan_path_on_surface(iso, spacing=path_spacing, angle_deg=angle)
        else:
            raise ValueError(f"Unknown path_strategy {path_strategy!r}")
        oriented_layers.append(paths)
        total_paths += len(paths)
        total_points += sum(len(p) for p in paths)

    gcode = write_oriented_paths_5axis(
        oriented_layers,
        machine,
        gcode_config=gcode_config,
        five_axis_config=five_axis_config,
        path=output_path,
        layer_height=layer_height,
    )

    return CurvedSlicePipelineResult(
        curvi_result=curvi_result,
        field=field,
        n_layers=len(iso_layers),
        n_paths=total_paths,
        n_path_points=total_points,
        gcode=gcode,
    )
