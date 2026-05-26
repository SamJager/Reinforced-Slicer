# Reinforced-Slicer

A 5-axis additive manufacturing slicer focused on **continuous fiber reinforced thermoplastic (CFRTP)** parts. Python, MIT-licensed, machine-agnostic.

> **Status:** pre-alpha. M0 (3-axis planar baseline) is the first milestone — present so the toolchain can be validated end to end. The interesting 5-axis and fiber-aware code lands in later milestones.

## Why another slicer?

Existing open-source slicers (Cura, PrusaSlicer, OrcaSlicer, Slic3r) are all 3-axis and AGPL/LGPL — hard to extend into a 5-axis fiber-aware pipeline without inheriting copyleft licenses. Research-grade 5-axis code (CurviSlicer, S³-Slicer, VoxelMultiAxisAM) is C++/CUDA and tightly coupled to specific hardware.

This project tries to fill the gap: a Python, permissively-licensed, end-to-end pipeline (mesh → curved layers → fiber paths → 5-axis G-code) that doesn't assume a specific machine. See [`References/`](References/) for the literature this builds on, especially [`References/KNOWLEDGE.md`](References/KNOWLEDGE.md) and [`References/SOFTWARE_INDEX.md`](References/SOFTWARE_INDEX.md).

## Milestones

| M    | Deliverable | Status |
|------|---|---|
| M0   | Repo scaffold, CI, planar 3-axis slicer that emits valid G-code | ✅ |
| M1   | AC-table 5-axis kinematics (Sørby IK) + GLT-2015 singularity smoother | ✅ |
| M1.5 | 5-axis G-code emitter wired through the kinematics layer | ✅ |
| M2a  | 2D CurviSlicer QP via OSQP (toy de-risker) | ✅ |
| M2b  | TetMesh primitives + Kuhn-triangulation synthetic mesher | ✅ |
| M2c  | 3D CurviSlicer + marching tets + curved paths + end-to-end pipeline | ✅ |
| GUI  | Gradio frontend with 4 workflow tabs | ✅ |
| M3   | Real STL tetrahedralisation via LGPL `gmsh` (`[tet]` extra) | ✅ |
| M4   | Direction field + stripe-pattern (Poisson) fiber-aligned paths | ✅ |
| M5   | Real FEA backend (stress field input to QP) | planned |
| M6+  | High-density fiber paths (Fang 2024), winding around holes, multi-material | planned |

## Quickstart

Requires Python 3.11+.

```bash
git clone https://github.com/SamJager/Reinforced-Slicer.git
cd Reinforced-Slicer
python -m venv .venv
.venv\Scripts\activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Slice a cube
python -c "import trimesh; trimesh.creation.box((10,10,10)).apply_translation([5,5,5]).export('cube.stl')"
reinforced-slicer cube.stl -o cube.gcode

# Run the test suite
pytest
```

## GUI (Gradio)

A browser-based UI ships as an optional extra:

```bash
pip install -e ".[dev,gui,tet]"              # tet adds LGPL gmsh for real STL meshing
reinforced-slicer-gui --no-browser           # serves on http://127.0.0.1:7860
reinforced-slicer-gui --share                # public tunnelled URL (72h)
```

Tabs run in workflow order:

1. **Load & preview** — STL upload or synthetic-cube generator, 3D viewport, basic stats.
2. **Planar (3-axis)** — knobs for layer height, infill spacing/angle, temperatures; plots per-layer paths and offers G-code download.
3. **Curved layer (5-axis)** — full M2c pipeline (CurviSlicer QP → iso-surfaces → paths-on-surfaces → 5-axis G-code through the AC-table kinematics). Plots curved layer surfaces with overlaid tool paths and sampled tool-axis arrows.
4. **Kinematics inspector** — sweep a tool-axis trajectory through the AC-table machine; plots rotary trajectory and singularity distance, with toggleable GLT-2015 smoothing.

> **Curved-layer pipeline:** by default uploaded STLs are tetrahedralised via the LGPL `gmsh` backend (install with the `[tet]` extra). Without that, the GUI falls back to an AABB shoebox approximation; the synthetic-cube generator on Tab 1 always uses the synthetic Kuhn-triangulation. See [src/reinforced_slicer/mesh/__init__.py](src/reinforced_slicer/mesh/__init__.py) for the backend-selection details.

## Repo layout

```
src/reinforced_slicer/
  io/           # mesh I/O, G-code output
  mesh/         # surface + tetrahedral mesh utilities (triangle2d, tet, isosurface)
  fea/          # stress-field input (mock for now, real backend deferred)
  slicing/      # planar (M0), CurviSlicer 2D/3D (M2), curved-layer pipeline (M2c)
  pathing/      # zigzag (M0), curved-surface path planner (M2c.3)
  kinematics/   # AC-table machine, IK, singularity smoothing
  postproc/     # paths -> G-code (3-axis + 5-axis emitters)
  viz/          # PyVista-based 3D preview (optional dependency)
  gui/          # Gradio app (optional extra)
tests/          # pytest suite
examples/       # demo parts (added as milestones progress)
References/     # curated literature compilation
```

## License

MIT. See [LICENSE](LICENSE). We deliberately avoid vendoring GPL/AGPL slicer code so this project can stay permissively licensed.

Algorithms from the literature (CurviSlicer, S³-Slicer, Fang 2024, etc.) are reimplemented from descriptions — copyright protects expression, not algorithms. Where a specific patent might cover a method (e.g., the WIPO spherical-coordinate patent), it's flagged in `References/KNOWLEDGE.md` §11. This is not legal advice.
