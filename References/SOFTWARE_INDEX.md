# SOFTWARE_INDEX.md — Tools, Libraries, Slicers

Every piece of named software in the corpus, organized for the question "**what should I use for X?**" Last refreshed against the corpus April 2026. Verify license + status before depending on anything.

## How to read this

Each entry has:
- **License** — read the actual `LICENSE` file in the repo; my tag is informational only.
- **Status** — `active`, `research`, `archived`, `unknown`.
- **Fit** — what it's good for in the context of a 5-axis AM project.
- **Caveats** — known gotchas.

---

## Quick decision tree

```
What do you want to do?
├── Slightly-curved slicing on 3-axis printer (no extra hardware)
│   → CurviSlicer (§A.1) — most accessible OSS, gentle learning curve
│   → Ahlers Slic3r fork (§A.2) — if you want a plug-in for an existing slicer
│   → CNC Kitchen non-planar G-code bend (§A.3) — quickest hack
│
├── Multi-axis curved-layer slicing (general, research)
│   → S³-Slicer (§B.1) — current SOTA, C++/CUDA, research-grade
│   → VoxelMultiAxisAM (§B.2) — Dai 2018 reference impl, simpler
│   → Neural Slicer (bibliography, code TBD) — newest paradigm
│
├── Continuous-fiber multi-axis
│   → S³-Slicer + Manchester pipeline (§B.1 + §B.3) — academic SOTA
│   → Markforged Eiger / Anisoprint Aura (§D.1) — commercial planar
│
├── Direct G-code prototyping for non-planar paths
│   → FullControl GCode Designer (§A.4) — Python, mature, well-documented
│
├── WAAM / metal multi-axis
│   → RPI/Wason OSS WAAM stack (§B.4) — end-to-end open architecture
│   → DED-IM (§B.5) — wire-arc DED specific
│   → ModuleWorks DED (§D.4) — commercial CAM library
│
├── 5-axis hardware retrofit
│   → Open5x (§E.1) — Prusa MK3s + Rhino/Grasshopper
│   → Rep5x (§E.2) — Ender retrofit (GPL!)
│   → Fractal 5 Pro slicer (§E.3) — Voron-based, Python slicer
│
└── Hybrid AM+SM commercial CAM
    → Aibuild (§D.2), Autodesk Netfabb, Siemens NX AM (§D.3) — closed
```

---

## A. 3-axis non-planar / slightly-curved tools

### A.1 CurviSlicer — recommended starting point

| Field | Value |
|---|---|
| **URL** | https://github.com/mfx-inria/curvislicer |
| **License** | check repo `LICENSE` — research code from Inria (likely permissive but verify) |
| **Language** | C++ (uses Gurobi for QP) |
| **Status** | Research-grade, but most polished OSS in the field |
| **Paper** | `2019CurviSlicer.pdf` Etienne et al. SIGGRAPH 2019 |
| **What it does** | Computes a deformation of the model that, planar-sliced and "uncurved," produces gently curved layers on 3-axis FFF |
| **Fit** | Best entry point for any deformation-based slicing project. Production-ish code. Uses **IceSL** as planar slicer backend. |
| **Caveats** | Requires **Gurobi** QP solver (commercial; free academic license). 3-axis only — doesn't exploit additional DOFs. Output toolpaths are guaranteed collision-free on standard 3-axis hardware. |

### A.2 Slic3r non-planar fork (Ahlers)

| Field | Value |
|---|---|
| **URL** | TAMS group at Universität Hamburg — search "Ahlers Slic3r non-planar" |
| **License** | Slic3r is AGPL — fork inherits |
| **Language** | C++ (Slic3r base) |
| **Status** | Research, but builds on the actively-maintained Slic3r |
| **Paper** | `case_ahlers_2019.pdf` Ahlers, Stein, Zhang IEEE CASE 2019 |
| **What it does** | Extends Slic3r to detect surface regions suitable for non-planar printing; uses a *geometric model of the printhead and extruder* to check collisions and generate collision-free non-planar toolpaths |
| **Fit** | Good if you already work in the Slic3r/PrusaSlicer ecosystem |
| **Caveats** | AGPL means derivatives must be AGPL too. Not for proprietary integration. Detection is geometric (not stress-aligned). |

### A.3 CNC Kitchen non-planar G-code bend

| Field | Value |
|---|---|
| **URL** | https://www.cnckitchen.com/blog/non-planar-3d-printing-by-bending-g-code (code on author's GitHub — search "Stefan CNC Kitchen non-planar") |
| **License** | check repo |
| **Language** | Python |
| **Status** | Maker-grade, blog-published |
| **What it does** | Post-process planar G-code by bending it onto a target surface |
| **Fit** | Quickest demo / prototype. Good for one-off creative parts. |
| **Caveats** | Doesn't replace a real slicer; doesn't handle collisions principally; intended for cosmetic top-layer effects. |

### A.4 FullControl GCode Designer

| Field | Value |
|---|---|
| **URL** | https://fullcontrol.xyz/ + GitHub link from there |
| **License** | OSS (verify) |
| **Language** | Python; runs in Colab/Jupyter |
| **Status** | Active, maintained by Andy Gleadall (Loughborough) |
| **Paper** | Gleadall 2021 *Additive Manufacturing* 46:102109 |
| **What it does** | Directly design G-code from Python — bypass the STL/slicer pipeline entirely. Per-segment control of width, height, speed, position, extrusion. |
| **Fit** | Best for prototyping non-planar paths algorithmically. Per-segment parameter control is unique. Good for research and education. |
| **Caveats** | Not a slicer for arbitrary STL — you describe paths directly. You write Python; you get G-code. |

---

## B. Multi-axis curved-layer research code

### B.1 S³-Slicer — current SOTA

| Field | Value |
|---|---|
| **URL** | https://github.com/zhangty019/S3_DeformFDM |
| **Project page** | https://guoxinfang.github.io/S3_Slicer |
| **License** | check repo `LICENSE` |
| **Language** | C++ with CUDA acceleration |
| **Status** | Research; SIGGRAPH Asia 2022 Best Paper |
| **Paper** | `3550454_3555516.pdf` Zhang, Fang, Huang et al. *ACM TOG* 41(6) 2022 |
| **What it does** | Multi-axis curved-layer slicer with simultaneous SF + SR + SQ objectives via quaternion-field deformation. The most general published slicer for multi-axis AM. |
| **Pipeline** | tet mesh + FEA stresses → quaternion-field optimization → scale-controlled deformation → scalar field G → iso-surfaces as layers → hybrid contour-parallel + stress-directional toolpaths |
| **Fit** | If you want SOTA quality and have C++/CUDA chops. The Manchester pipeline (Zhang 2024, Fang 2024) is built on top. |
| **Caveats** | Research code — expect rough edges. Requires FEA pre-step. Computational expense (~2 min for 245k-tet models). Singularity-aware motion planning is a separate downstream step (see [S3 motion planning repo](https://github.com/zhangty019), search Manchester GitHub). Mentions a simpler educational extension **"S4 Slicer" by Joshua Bird** — also worth checking. |

### B.2 VoxelMultiAxisAM — Dai 2018 reference implementation

| Field | Value |
|---|---|
| **URL** | https://github.com/daichengkai/VoxelMultiAxisAM |
| **License** | check repo `LICENSE` |
| **Language** | C++ |
| **Status** | Research; reference implementation of an anchor paper |
| **Paper** | `SIG18RobotVolPrint.pdf` Dai et al. SIGGRAPH 2018 |
| **What it does** | Scalar-field-based curved-layer generation via convex-front advancing + shadowed-voxel avoidance |
| **Fit** | Conceptually simpler than S³-Slicer (single objective, no quaternion field). Good for understanding the scalar-field paradigm before tackling S³. |
| **Caveats** | Single objective (support-free only). Voxel-discretized field — layer thickness comes out coarse. Older code. |

### B.3 Support generation for curved RoboFDM

| Field | Value |
|---|---|
| **URL** | https://github.com/zhangty019/Support_Generation_for_Curved_RoboFDM |
| **License** | check repo `LICENSE` |
| **Language** | C++ |
| **Status** | Research |
| **Paper** | Zhang ICRA 2023 (bibliography) |
| **What it does** | Generates support structures **for curved-layer printing**, where the supports themselves are non-planar |
| **Fit** | Companion to S³-Slicer. Use if you've adopted curved-layer slicing and need supports for unavoidable overhangs. |
| **Caveats** | Tightly coupled to S³-Slicer; needs the same input pipeline. |

### B.4 RPI/Wason OSS WAAM stack — `1s2_0S2666496825000020main.pdf`

| Field | Value |
|---|---|
| **URL** | https://github.com/rpiRobotics (search for "WAAM" repos; paper references this org) |
| **License** | likely permissive (typical of Wason Technology releases) — verify per repo |
| **Language** | Python, C++, via **Robot Raconteur** middleware |
| **Status** | Active (2025) |
| **Paper** | `1s2_0S2666496825000020main.pdf` He et al. 2025 |
| **What it does** | End-to-end OSS WAAM architecture: CAD → part slicing → robot motion planning → in-process sensing → metrology → process tuning → part evaluation. Hardware-agnostic (Motoman, Fronius, etc.) |
| **Fit** | If you're building any robot+sensor end-to-end multi-axis system, study this architecture even if WAAM isn't your target. **Best published reference for system architecture.** |
| **Caveats** | WAAM-specific physics in places (weld bead deposition); the *architecture* is general. Tested with Motoman + Fronius. |

### B.5 DED-IM

| Field | Value |
|---|---|
| **URL** | https://github.com/machipanski/DED-IM |
| **License** | check repo `LICENSE` |
| **Language** | Python |
| **Status** | Research |
| **What it does** | Image-based segmentation of 3D models for WA-DED path planning. Wraps a novel mapping/path-planning method. |
| **Fit** | Niche — wire-arc DED specifically. Useful primarily if your domain is large metal AM. |

### B.6 Neural Slicer (Yi 2024)

| Field | Value |
|---|---|
| **URL** | not in corpus PDFs; arXiv 2404.15061 in bibliography. Code release pending — check Manchester GitHub. |
| **License** | TBD |
| **Language** | likely Python (PyTorch given the neural-field approach) |
| **Status** | Research, very recent |
| **Paper** | Yi 2024 ACM TOG |
| **What it does** | Differentiable end-to-end multi-axis slicing via neural networks. Representation-agnostic. Loss functions for SF + SR. |
| **Fit** | Frontier paradigm. Worth watching but probably not the right starting point for an engineering project today. |

### B.7 Liu 2025 neural co-optimization — `2505_03779v1.pdf`

Similar to B.6 — code likely on Manchester GitHub. Joint topology + layers + path optimization. Three implicit neural fields. Supports 5/3/2.5-axis with same framework. Frontier work.

---

## C. Underlying geometry / numerics libraries

Not slicers themselves but commonly used building blocks. Most are battle-tested.

| Library | Use | URL | License |
|---|---|---|---|
| **CGAL** | mesh ops, exact arithmetic, polyhedra | https://www.cgal.org/ | dual-license: GPL or commercial |
| **libigl** | geometry processing for triangle meshes | https://libigl.github.io/ | MPL2 |
| **OpenMesh** | mesh data structures | https://www.graphics.rwth-aachen.de/software/openmesh/ | BSD-style |
| **CinoLib** | mesh processing | https://github.com/mlivesu/cinolib | MIT |
| **Geometric Tools** | computational geometry | https://www.geometrictools.com/ | Boost license |
| **PyMesh** | Python mesh wrangling | https://pymesh.readthedocs.io/ | MPL2 |
| **Gurobi / CPLEX / Mosek** | QP/LP/MIQP solvers (CurviSlicer uses Gurobi) | various | commercial (free academic) |
| **OSQP** | open-source QP | https://osqp.org/ | Apache 2.0 |
| **Eigen** | linear algebra | https://eigen.tuxfamily.org/ | MPL2 |
| **Open3D** | point cloud, mesh, viz (3D AM workflows) | http://www.open3d.org/ | MIT |
| **Robot Raconteur** | robotics middleware (used by RPI/Wason WAAM) | https://robotraconteur.com/ | Apache 2.0 |

For **direction-field / stripe-pattern** computation (the foundation under vector-field path planning):
- Knöppel 2015 "Stripe Patterns" code — DDG community releases, search Discrete Differential Geometry pages
- Crane et al. "Geodesics in Heat" — https://www.cs.cmu.edu/~kmcrane/Projects/HeatMethod/ — reference implementation by author
- libigl includes some direction-field utilities

---

## D. Commercial systems (closed-source, for reference / benchmarking)

### D.1 CFRTP commercial slicers (planar-layer only)

| Vendor | Product | URL | Notes |
|---|---|---|---|
| **Markforged** | Eiger | https://markforged.com | Industry leader. Zigzag CCF paths. In-nozzle impregnation. |
| **Anisoprint** | Aura | https://anisoprint.com | Stress-field guided paths. Coextrusion. |
| **9T Labs** | Red series | https://www.9tlabs.com | Higher fiber volume fraction. Towpreg-based. |

None of these do **multi-axis curved-layer** CFRTP commercially as of 2026.

### D.2 Aibuild + S³-Slicer commercial partner

| Field | Value |
|---|---|
| **URL** | https://ai-build.com/ |
| **License** | Closed commercial |
| **What it does** | Industrial-scale multi-axis robotic AM software. Uses **geodesic-based** slicing in commercial product (different from the deformation-based S³-Slicer they sponsor academically). |
| **Fit** | Industry benchmark only; you can't get the source. Whitepaper https://www.designforam.com/p/geodesic-slicing-a-generalised-framework gives conceptual overview. |
| **Caveats** | Don't conflate "Aibuild's commercial product" with "S³-Slicer" — they're related but technically distinct. |

### D.3 General multi-axis CAM / build-prep

| Vendor | Product | Use case |
|---|---|---|
| **Autodesk** | Netfabb | Build prep, DED toolpath support |
| **Materialise** | Magics | File repair, build prep |
| **Siemens** | NX AM | 5-axis hybrid CAM |
| **Hexagon (Vero)** | Edgecam, VISI | 5-axis CAM with AM modules |
| **Autodesk** | PowerMill Additive | 5-axis DED |
| **AdaOne** | AdaOne | Large-scale robotic AM |

All closed-source. Useful as feature/capability benchmarks for an OSS or research slicer.

### D.4 ModuleWorks DED

| Field | Value |
|---|---|
| **URL** | https://www.moduleworks.com/software-components/toolpath/additive/direct-energy-deposition/ |
| **License** | Commercial CAM library |
| **What it does** | Closed-source CAM toolpath library widely used as a backend for hybrid AM/SM systems |
| **Fit** | Reference for what production-quality DED CAM looks like. |

### D.5 Other commercial multi-axis slicers

| Vendor | Product | URL |
|---|---|---|
| **5-Axis-Slicer** | 5-Axis Slicer | https://www.5-axis-slicer.com/ |
| **Phasio** | (blog) | https://www.phas.io/post/5-axis-toolpath-optimisation |
| **Generative Machine** | desktop 5-axis using Aibuild | https://ai-build.com/resources/ai-driven-5-axis-desktop-3d-printing/ |

---

## E. Open-source 5-axis hardware projects (and their slicers)

### E.1 Open5x

| Field | Value |
|---|---|
| **URL** | GitHub: search "HongFreddy/open5x" or "Open5x"; project page from CHI 2022 paper |
| **License** | Open hardware. Slicer license: not specified in CHI paper — **verify before reuse**. |
| **Language** | Slicer in **Rhino + Grasshopper** (visual scripting, Python under the hood) |
| **Status** | Research, with active community |
| **Paper** | `2202_11426v2.pdf` Hong, Bowyer, Aremu, Boyle 2022 CHI Extended Abstracts |
| **Hardware** | Prusa i3 MK3s + 3D-printed 2-axis rotary gantry (axes labeled U, V); Duet 2 control board |
| **Slicer pipeline** | Import geometry → user selects surface → auto-generate B-spline conformal toolpath → subdivide to polylines @ 0.2mm/segment → compute 5-axis IK and motion → optimize for AM → export G-code |
| **Fit** | **Best published reference for accessible 5-axis FDM**. Rhino/Grasshopper is approachable for non-coders. CAD design + slicing + simulation in one environment. |
| **Caveats** | Rhino is commercial (~$1k/seat); Grasshopper is free with Rhino. Slicer is integrated, not standalone — not directly reusable as a library. |

### E.2 Rep5x

| Field | Value |
|---|---|
| **URL** | https://github.com/dennisklappe/Rep5x |
| **License** | **GPL v3** |
| **Language** | check repo |
| **Status** | Maker community |
| **Hardware** | Ender 5 Pro / Ender 3 V3 SE retrofit |
| **Fit** | Cheapest 5-axis path; well-documented mechanical retrofit. |
| **Caveats** | **GPL!** Any derivative software you ship must be GPL too. **Do not vendor into a proprietary product.** OK for OSS or in-house research. |

### E.3 Fractal 5 Pro

| Field | Value |
|---|---|
| **URL** | https://fractal-robotics.com/ (slicer repo via main site) |
| **License** | check repo |
| **Language** | Python (slicer) |
| **Status** | Recent (2025); active |
| **Hardware** | Voron-based open-design 5-axis printer |
| **Coverage** | Hackaday https://hackaday.com/2025/08/04/open-source-5-axis-printer-has-its-own-slicer/ |
| **Fit** | Newest entrant; Python slicer is more readable than C++/CUDA research code. |
| **Caveats** | Young project; expect rapid changes. |

### E.4 5DOF wireframe (Wu 2016, bibliography)

Different paradigm — printing strings of filament in mid-air. Specialty hardware. Not for general 5-axis slicing.

---

## F. Foundational 3-axis tools you'll integrate with

Because every multi-axis slicer eventually needs to either (a) generate 2D paths or (b) post-process 3-axis output:

| Tool | URL | License | Use |
|---|---|---|---|
| **IceSL** | https://icesl.loria.fr/ | Free (Inria) | Planar slicer backend; what CurviSlicer uses |
| **PrusaSlicer** | https://github.com/prusa3d/PrusaSlicer | AGPL | Standard FFF slicer |
| **Slic3r** | https://slic3r.org/ | AGPL | Original ancestor; Ahlers fork builds on this |
| **OrcaSlicer** | https://github.com/SoftFever/OrcaSlicer | AGPL | Modern community fork |
| **Cura** | https://github.com/Ultimaker/Cura | LGPL/AGPL | Ultimaker, widely used |
| **PrusaSlicer Arachne perimeter generator** | https://help.prusa3d.com/article/arachne-perimeter-generator_352769 | AGPL | Variable-width perimeter — relevant 3-axis precedent for adaptive line width |

**Arachne** is worth singling out: it's a variable-width perimeter generator developed by Ultimaker/Prusa. If you want adaptive line width on a 5-axis system (matching the deposited bead width to local geometry), Arachne is the 3-axis precedent for the algorithm.

---

## G. Things this corpus does *not* cover (look elsewhere)

- **Klipper firmware** for 5-axis configuration — community macros and dev work, not in this corpus
- **RepRapFirmware Duet** 5-axis configs — Open5x uses this; documentation at https://docs.duet3d.com
- **ROS / ROS2** robotic AM packages — for robot-arm AM systems
- **MoveIt** motion planning for robot arms
- **Robot vendor SDKs** — UR script, ABB RAPID, KUKA KRL, Motoman INFORM
- **Chinese research code** — see `gaps_and_next_steps.md`. CNKI has more work that doesn't surface in English search.

---

## H. Recommended workflow for a new 5-axis AM software project

Based on the corpus's evidence:

1. **Start with CurviSlicer** (§A.1) end-to-end on your hardware. Even though it's 3-axis, the codebase is the most accessible entry into deformation-based slicing. You'll learn the QP formulation, the relaxation strategy, the mesh-deformation primitives.
2. **Reproduce a single Dai-2018-style scalar-field slicing example** using VoxelMultiAxisAM (§B.2). Now you understand both schools (scalar-field and deformation).
3. **Implement a basic 5-axis postprocessor** using Sørby's IK formulas (`Grandguillaume_...` for the equations). Test with a known toolpath. Now you have machine motion that respects singularities.
4. **Pick one capability** (support-free, stress-aligned, or hybrid AM/SM) and read the sub-literature in depth. Read S³-Slicer code (§B.1) when you're ready for the multi-objective case.
5. **For continuous fiber**: read the Manchester pipeline as a whole (Zhang 2024 + Fang 2024 in corpus). The Northwestern Polytechnical group's Li 2025 (`processes1300473.pdf`) is a strong alternative formulation to cross-check against.
6. **For hybrid AM/SM**: start from Chen 2025 (`2509_10599v1.pdf`) — it generalizes prior work and proves universal fabricability.

This matches the consensus in the corpus: the field has converged on "compute a curved-layer field, then plan paths on it, then convert to machine motion." Open questions are about *which* field to compute, *which* path topology to use, and how to handle the kinematics-AM coupling.
