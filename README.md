# Reinforced-Slicer

A 5-axis additive manufacturing slicer focused on **continuous fiber reinforced thermoplastic (CFRTP)** parts. Python, MIT-licensed, machine-agnostic.

> **Status:** pre-alpha. M0 (3-axis planar baseline) is the first milestone — present so the toolchain can be validated end to end. The interesting 5-axis and fiber-aware code lands in later milestones.

## Why another slicer?

Existing open-source slicers (Cura, PrusaSlicer, OrcaSlicer, Slic3r) are all 3-axis and AGPL/LGPL — hard to extend into a 5-axis fiber-aware pipeline without inheriting copyleft licenses. Research-grade 5-axis code (CurviSlicer, S³-Slicer, VoxelMultiAxisAM) is C++/CUDA and tightly coupled to specific hardware.

This project tries to fill the gap: a Python, permissively-licensed, end-to-end pipeline (mesh → curved layers → fiber paths → 5-axis G-code) that doesn't assume a specific machine. See [`References/`](References/) for the literature this builds on, especially [`References/KNOWLEDGE.md`](References/KNOWLEDGE.md) and [`References/SOFTWARE_INDEX.md`](References/SOFTWARE_INDEX.md).

## Milestones

| M  | Deliverable | Status |
|----|---|---|
| M0 | Repo scaffold, CI, planar 3-axis slicer that emits valid G-code | **in progress** |
| M1 | URDF-driven machine model + Sørby IK + singularity smoothing | planned |
| M2 | CurviSlicer algorithm reimplemented in Python (OSQP-based QP) | planned |
| M3 | Tet mesh + scalar-field iso-surfacing → curved layers | planned |
| M4 | 2-RoSy direction field + stripe-pattern paths on a curved layer | planned |
| M5 | End-to-end STL + (mock) stress → 5-axis fiber G-code + viz | planned |
| M6+ | High-density paths (Fang 2024 periodic field), winding around holes, dual-material | planned |

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

## Repo layout

```
src/reinforced_slicer/
  io/           # mesh I/O, G-code output
  mesh/         # surface + tetrahedral mesh utilities
  fea/          # stress-field input (mock for now, real backend deferred)
  slicing/      # planar (M0), CurviSlicer (M2), S³-field (M3+)
  pathing/      # zigzag (M0), direction-field, stripe-pattern, Eulerian linking
  kinematics/   # URDF/DH machine model, IK, singularity smoothing
  postproc/     # paths -> G-code, collision checks
  viz/          # PyVista-based 3D preview (optional dependency)
tests/          # pytest suite
examples/       # demo parts (added as milestones progress)
References/     # curated literature compilation
```

## License

MIT. See [LICENSE](LICENSE). We deliberately avoid vendoring GPL/AGPL slicer code so this project can stay permissively licensed.

Algorithms from the literature (CurviSlicer, S³-Slicer, Fang 2024, etc.) are reimplemented from descriptions — copyright protects expression, not algorithms. Where a specific patent might cover a method (e.g., the WIPO spherical-coordinate patent), it's flagged in `References/KNOWLEDGE.md` §11. This is not legal advice.
