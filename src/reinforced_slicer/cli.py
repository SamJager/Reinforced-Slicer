"""Command-line entrypoint for the M0 planar baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

import trimesh

from reinforced_slicer.kinematics import AcTableMachine
from reinforced_slicer.postproc.gcode import GcodeConfig, write_gcode
from reinforced_slicer.postproc.gcode_5axis import write_gcode_5axis
from reinforced_slicer.slicing.planar import PlanarSliceConfig, slice_planar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reinforced-slicer",
        description="5-axis slicer for fiber reinforced printing (M0 planar baseline).",
    )
    parser.add_argument("input", type=Path, help="Input mesh file (STL, OBJ, PLY, ...)")
    parser.add_argument("-o", "--output", type=Path, default=Path("out.gcode"))
    parser.add_argument("--layer-height", type=float, default=0.2)
    parser.add_argument("--infill-spacing", type=float, default=0.4)
    parser.add_argument("--infill-angle", type=float, default=45.0)
    parser.add_argument("--nozzle-temp", type=int, default=210)
    parser.add_argument("--bed-temp", type=int, default=60)
    parser.add_argument(
        "--five-axis",
        action="store_true",
        help="Emit 5-axis G-code routed through an AC-table machine model "
        "(tool axis is vertical, so A=C=0 throughout; useful as a seam check).",
    )
    args = parser.parse_args(argv)

    mesh = trimesh.load(args.input, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        raise SystemExit(f"Could not load a triangle mesh from {args.input}")

    slice_cfg = PlanarSliceConfig(
        layer_height=args.layer_height,
        infill_spacing=args.infill_spacing,
        infill_angle_deg=args.infill_angle,
    )
    gcode_cfg = GcodeConfig(nozzle_temp_c=args.nozzle_temp, bed_temp_c=args.bed_temp)

    part = slice_planar(mesh, slice_cfg)
    if args.five_axis:
        machine = AcTableMachine()
        write_gcode_5axis(part, machine, gcode_cfg, path=args.output)
    else:
        write_gcode(part, args.output, gcode_cfg)
    print(f"Wrote {len(part.layers)} layers to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
