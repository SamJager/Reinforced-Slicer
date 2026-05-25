# KNOWLEDGE.md — Consolidated Technical Reference

5-axis additive manufacturing, curved-layer slicing, multi-axis path planning, continuous-fiber reinforcement, software. Compiled from the 32 PDFs and curated docs in this project (corpus last updated April 2026).

## Topics index

| §  | Topic | Where to jump |
|----|---|---|
| 0  | PDF filename → paper map | so an agent can resolve a citation to a file |
| 1  | The 4-stage pipeline | mental model for the whole field |
| 2  | Curved-layer slicing | scalar-field, deformation, geodesic, decomposition |
| 3  | Path generation on a surface | iso-*, vector-field, space-filling, medial-axis |
| 4  | Continuous fiber reinforcement (CFRTP) | the largest single thread in the corpus |
| 5  | Kinematics, IK, singularities | how a toolpath becomes machine motion |
| 6  | Hybrid additive + subtractive (HASM) | VASCO, recent CMAME work, Manchester 2025 |
| 7  | Hardware archetypes | gantry+rotary, robot+positioner, hybrid CNC, retrofits |
| 8  | Coverage map: strong / moderate / weak | where the literature is dense vs. thin |
| 9  | Anchor-10 reading order | if you only have time for ten papers |
| 10 | Key people and groups | who to follow |
| 11 | Patents in the corpus | five examples, *not* an FTO sweep |
| 12 | Open problems | what's not solved |

---

## 0. PDF filename → paper map

Filenames in `/mnt/project/*.pdf` are often DOIs or arXiv IDs. Quick lookup:

| Filename | Short name | Authors, year | Topic |
|---|---|---|---|
| `SIG18RobotVolPrint.pdf` | **Dai 2018** | Dai, Wang, Wu, Lefebvre, Fang, Liu — SIGGRAPH 2018 | Anchor: scalar-field support-free volume printing |
| `2019CurviSlicer.pdf` | **CurviSlicer** | Etienne, Ray, Panozzo et al. — SIGGRAPH 2019 | Anchor: deformation-based slightly-curved slicing (3-axis) |
| `3550454_3555516.pdf` | **S³-Slicer** | Zhang, Fang, Huang, Dutta, Kilic, Lefebvre, Wang — SIGGRAPH Asia 2022 | Anchor: deformation + quaternion-field multi-objective slicer |
| `1812_00606v4.pdf` | **Wu 2020** | Wu, Dai, Fang, Liu, Wang — IEEE T-ASE 2020 | Volume decomposition (general support-effective) |
| `2202_11426v2.pdf` | **Open5x** | Hong, Bowyer, Aremu, Boyle — CHI 2022 EA | Accessible 5-axis hardware + Rhino/Grasshopper slicer |
| `2311_17265v2.pdf` | **Zhang 2024 spatial fiber** | Zhang, Fang, Wang et al. — arXiv 2311 | Curved-layer continuous fiber along principal stress |
| `2410_16851v2.pdf` | **Fang 2024 high-density fiber** | (Manchester) — arXiv 2410 | 2-RoSy direction field, dense CFRTP toolpaths |
| `2505_03779v1.pdf` | **Liu 2025 neural co-opt** | Liu, Zhang, Chen et al. — arXiv 2505 | Joint topology + layers + paths via neural fields |
| `2509_10599v1.pdf` | **Chen 2025 HASM** | Chen, Liu, Huang et al. — arXiv 2509 / ACM TOG 2025 | Inverse-operation hybrid AM/SM planning |
| `2604_12236v1.pdf` | **Liu 2026 multi-axis DLP** | (Michigan) — arXiv 2604 | Multi-axis DLP/SLA with variable-exposure curing |
| `2112_02030v2.pdf` | **Moter 2021 raster-angle TopOpt** | Moter, Abdelhamid, Czekanski — arXiv 2112 | Stress-constrained TopOpt with raster-angle DV |
| `case_ahlers_2019.pdf` | **Ahlers 2019** | Ahlers, Stein, Zhang — IEEE CASE 2019 | Slic3r-based 3-axis non-planar with collision check |
| `Duarte_Xana_Teresa_ismael_curved.pdf` | **Duarte 2022** | Duarte et al. — Rapid Prototyping J. 2022 | Spline-based 5-axis curved-layer for shells |
| `Grandguillaume_Lavernhe_Tournier_HSM_2015.pdf` | **GLT 2015** | Grandguillaume, Lavernhe, Tournier — HSM 2015 | Rotary-axis smoothing near singularity (machining) |
| `1s2_0S2666496825000020main.pdf` | **He 2025 OSS WAAM** | He et al. — RPI/Wason Tech 2025 | OSS multi-robot WAAM software architecture |
| `NON_PLANAR_TOOLPATH_FOR_LARGE_SCALE_ADDITIVE10_46519ij3dptdi_9563131838713.pdf` | **Aladag 2021** | Eyercioglu, Aladag — IJ3DPTDI 2021 | Non-planar toolpaths for *large-scale* AM (LSAM) |
| `PartScale_build_orientation_opitimization.pdf` | **Cheng & To 2019** | Cheng, To — CAD 2019 | Part-scale orientation TopOpt for residual stress (metal AM) |
| `Sultanetal_v4i225274308.pdf` | **Sultan 2025 review** | Sultan et al. — RAST 2025 | Recent OA review of non-planar toolpath optimization |
| `appliedmath0600035.pdf` | **Li 2026 end-to-end 5-axis mesh** | Li, Ma, Zhang, Shen — *Algorithms* 2026 | End-to-end 5-axis end-milling on triangle mesh (machining) |
| `applsci1107509.pdf` | **Rodriguez-Padilla 2021** | Rodriguez-Padilla et al. — Appl. Sci. 2021 | Algorithm: project 2D pattern onto tessellated surface |
| `materials1702005.pdf` | **Wu, Liu, Liu 2024** | Wu, Liu, Liu — *Materials* 2024 | Geometric-complexity control in fiber-composite TopOpt |
| `materials1804249.pdf` | **Freitas 2025 review** | Freitas et al. — *Materials* 2025 | OA review of hybrid additive/subtractive manufacturing |
| `micromachines1601316v2.pdf` | **Han 2025 decomp** | Han, Qin, Chen, Liu, Cui — *Micromachines* 2025 | Pareto + beam-search model decomposition (multi-axis) |
| `processes1300473.pdf` | **Li 2025 FRC curved-layer** | Li, Shi, Yan (Northwestern Polytechnical) — *Processes* 2025 | Deformed-space FRC slicer + vector-field paths + supports |
| `qwac103.pdf` | **Chu 2025 spiral bevel** | Chu, Zhou et al. — JCDE 2025 | 5-axis flank milling, spiral bevel gears (machining) |
| `3dp_2020_0048.pdf` | **Loh 2022 Hilbert FGM** | Loh et al. — *3DPAM* 2022 | Hilbert area-filling for functionally-graded FDM |
| `3dp_2020_0335.pdf` | **Brian 2022 concrete** | Brian, Salmon et al. — *3DPAM* 2022 | 6-axis robotic concrete printing (NASA habitat) |
| `WPI_undergrad_thesis_5Axis_3D_printing.pdf` | **WPI thesis** | Coeytaux, Crook, Pauwels, Whelan — WPI MQP | End-to-end 5-axis system: hardware + software + IK + G-code |
| `US20130189435A1.pdf` | **Mackie patent 2013** | Mackie et al. (Wisconsin) | Dual-rotation-axis 3D printer (turntable + rotating arm) |
| `US20170320267A1.pdf` | **ORNL nozzle patent 2017** | Lind, Post, Love et al. (UT-Battelle / ORNL) | Variable-width deposition via rotatable non-circular nozzle |
| `US20180056602A1.pdf` | **Thermwood patent 2018** | Susnjara et al. (Thermwood) | Closed-loop extrusion control for large-scale AM (LSAM) |
| `WO2016178977A1.pdf` | **Lee patent 2016** | Jay Lee — WIPO PCT | AM using **spherical coordinates** (rho/theta/phi) |

> Note: `WO2016178977A1.pdf` has no extractable text (image-only PDF). Title and abstract verified by direct page render.

---

## 1. The 4-stage pipeline (mental model)

Almost every paper in this corpus fits into one or more of these four stages. When asked "where does X fit," try mapping to this first:

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT  ──→  SLICE  ──→  PATH  ──→  ORIENT  ──→  KINEMATIZE  ──→  G-CODE / motion
│ (mesh, FEA)  (layers)  (curves)  (n̂ vectors)   (X,Y,Z,A,B,C)
└─────────────────────────────────────────────────────────────────┘
```

| Stage | What it does | Sub-paradigms (jump to §) |
|---|---|---|
| **SLICE** | Volume → ordered sequence of curved surface layers | scalar-field (§2.1), deformation (§2.2), geodesic (§2.3), volume decomposition (§2.4), spherical/ellipsoidal (§2.5) |
| **PATH** | Surface layer → continuous curve filling it | iso-parametric, iso-planar, iso-scallop, vector-field/stripe, space-filling (Fermat, Hilbert), medial-axis (§3) |
| **ORIENT** | Per point, choose nozzle/tool direction n̂ within the **domain of admissible orientation** (collision-free, gouge-free) | Castagnetti DAO concept (§3.6); for AM, normal-to-layer is usually default |
| **KINEMATIZE** | (CC point + n̂) → machine joint values (X,Y,Z + 2 rotaries) avoiding singularities, respecting velocity/acceleration/jerk | Sørby IK, RRTTT 5-axis (§5) |

**Why this matters:** the existing literature splits cleanly along this line. CurviSlicer and S³-Slicer are *slicing* algorithms; Knöppel stripe patterns and Crane heat-method are *path-generation* primitives; Sørby/GLT 2015 are *kinematics*. If a question is about "the whole pipeline," you'll combine work from 2-3 different stages.

**Why machining matters to AM:** stages 2-4 were all solved (or studied) for 5-axis CNC machining decades earlier. The AM community has been re-deriving with AM-specific twists:
- machining "cutting strip width" ↔ AM "deposition strip width"
- machining "gouging avoidance" (tool cuts into workpiece) ↔ AM "collision with previously deposited material"
- machining "scallop height" ↔ AM "surface roughness from path spacing"

This is why the bibliography deliberately includes machining references (Lasemi 2010 review, Sun 2022 trajectory review, Sørby 2007).

---

## 2. Curved-layer slicing

The core problem: given a tetrahedral or surface mesh of the part, output a sequence of curved layers whose union is the part and which satisfy manufacturing objectives.

### 2.1 Scalar-field optimization (Dai 2018 paradigm)

**Anchor:** `SIG18RobotVolPrint.pdf` — Dai, Wang, Wu, Lefebvre, Fang, Liu 2018, *ACM TOG (SIGGRAPH 2018)*.

**Key idea:** define a scalar field $G(x)$ on the volume. Its iso-surfaces will be the printing layers, in order of increasing $G$. Optimize $G$ to satisfy:

1. **Support-free:** every iso-surface is supported from below by previously printed volume. Equivalently: $\nabla G$ is roughly aligned with the build direction $d_p$ inside the part interior.
2. **Convex / collision-free:** iso-surfaces are *convex with respect to the nozzle's accessibility cone*. Dai's algorithm uses a **convex-front advancing** voxel growth strategy (Section 4).
3. **No "shadowed voxels":** voxels that get occluded by already-printed material can never be reached. The algorithm has an explicit *shadow-prevention* sub-routine that holds back voxels that would create unreachable regions (Section 4.3).
4. **Curve covering of layers:** each layer is then covered with a smooth toolpath that respects the printer head's kinematic limits.

**Pipeline (Dai 2018):**
1. Voxelize part (Dai uses voxel widths of $0.8d$ where $d$ is the nozzle diameter — calibrated experimentally).
2. Greedy convex-front advancing: grow layers outward such that the convex-hull constraint is maintained.
3. Shadow-prevention: detect voxels that would become unreachable, defer them.
4. Extract iso-surfaces of $G$ at uniform intervals.
5. Generate paths on each layer.

**Hardware tested:** UR5 robot arm with FDM head; positioning accuracy ~0.1mm repeatability, ±1mm in low-speed motion. Authors flag that thin-feature deposition is unreliable on FDM — would be better on WAAM or with higher-precision 5-axis CNC kinematics.

**Key strength:** handles high-genus topologies and complex overhangs. Computed in ~33s for a 540k-voxel model.

**Key limitation:** field is defined on voxels (not continuous), so layer thickness is discretized. Single objective (support-free) — can't directly trade off with strength or surface quality.

**Successor:** S³-Slicer (§2.2) generalizes to multi-objective. Neural Slicer (Yi 2024, not in corpus PDFs but in bibliography) makes the pipeline differentiable.

**Code:** https://github.com/daichengkai/VoxelMultiAxisAM (check repo LICENSE — research code).

### 2.2 Deformation-based slicing (CurviSlicer / S³-Slicer paradigm)

Two related papers in the corpus. The key trick: instead of computing curved layers directly, compute a *deformation* $M$ of the model such that planar slices of $M(\text{model})$ map to good curved layers of the original via $M^{-1}$.

#### 2.2.1 CurviSlicer (Etienne 2019) — `2019CurviSlicer.pdf`

**Setting:** 3-axis FFF printer (e.g. Ultimaker 2), so slightly-curved deposition (within the deposition cone the nozzle/extruder can achieve without collision).

**Key idea:** the deformation $M_h$ is a *vertical-only* displacement field $h(p)$ on a tetrahedral mesh of the part. This restriction keeps the problem well-posed for 3-axis hardware (the printer can only deposit slightly out of plane).

**Mathematical formulation:**
- Unknowns: $h(p)$ at each tet vertex.
- Objective (high-weight soft constraint): flatten the top-of-part surface triangles in $F$ so they become parallel to the slicing plane.
- Hard constraint (linear): per-tetrahedron, $1 \leq z(\nabla h_t) \leq \tau_{max}/\tau_{min}$ where $\tau_{min}, \tau_{max}$ are admissible slice thicknesses on the printer (this is the *stretch* constraint and prevents thickness violations).
- Solved as **quadratic programming** with **Gurobi** as the QP solver.
- Iteratively relaxes flatness on triangles that can't be flattened, taking from the boundary inward.

**Pipeline:**
1. Compute $h$ via QP.
2. Apply $M_h$ to the model → planar-slice the deformed model with a standard slicer (IceSL is the backend).
3. Resample toolpaths at the nozzle-diameter rate.
4. Map each toolpath point through $M_h^{-1}$ back to the curved space.
5. Offset each point down by $\tau_{max}/2$ to put it at slice mid-thickness.

**Strength:** elegant convex QP, integrates with off-the-shelf planar slicers, guaranteed collision-free on 3-axis hardware. Open-source, the most accessible OSS in the field.

**Limitation:** restricted to *slightly* curved deposition (doesn't exploit additional DOFs of multi-axis). Not for 5-axis.

**Code:** https://github.com/mfx-inria/curvislicer (uses IceSL as planar slicer backend).

#### 2.2.2 S³-Slicer (Zhang 2022) — `3550454_3555516.pdf`

**Setting:** general multi-axis AM (5-axis FDM, 6-DOF robot arm with positioner). SIGGRAPH Asia 2022 *Best Paper*.

**Key idea:** generalize CurviSlicer in two ways:
1. Allow arbitrary rotation (not just vertical-only stretching) — represented as **quaternion field** on tet elements.
2. Simultaneously optimize for three objectives: **Support-Free (SF), Strength-Reinforcement (SR), Surface-Quality (SQ)** — see "$S^3$" name.

**Mathematical formulation:**
- Per-element quaternion $q_e$ representing local rotation that brings the local printing direction (LPD) to $d_p = (0,0,1)$.
- Inner loop: optimize quaternion field $Q^* = \{q_e^*\}$ to:
  - Minimize quaternion difference between neighboring elements (smoothness)
  - Satisfy LPD constraints locally per element: $C_{SF}$ on boundary elements, $C_{SQ}$ on boundary elements, $C_{SR}$ on critical (high-stress) elements
- Outer loop: assemble locally-rotated elements into globally consistent deformed model $M^d$ via **scale-controlled deformation** — controls the variation in layer thickness.
- Both inner and outer loops use **local/global solvers** (à la ARAP).

**Pipeline (Section 2 of paper, 8 steps):**
1. Input tet mesh $M$, FEA stress tensors per element. $M^d \leftarrow M$.
2. Compute rotation per element from $M \to M^d$ as quaternions $\mathcal{Q}$.
3. Inner loop: optimize $\mathcal{Q}^*$.
4. Outer loop: assemble $\mathcal{Q}^*$ → deformed $M^d$ via scale-controlled deformation.
5. Map height-field of $M^d$ → scalar field $G(\cdot)$ on $M$.
6. Check terminal condition (∇G as LPDs). If not converged, return to step 2.
7. Extract iso-surfaces of $G$ as curved layers; apply adaptive slicing if needed.
8. Generate per-layer toolpaths: **hybrid of contour-parallel and stress-reinforced directional-parallel**.

**Quantitative results:** average surface error reduced 28.2% (0.632mm → 0.454mm) vs. planar slicing on bunny test. Compute time <2 min for all examples (up to 245k tet elements). Bridge model strength improved.

**Adaptive slicing** is applied "only when necessary" — typical models don't need it. Layer thickness control is built into the scale-controlled deformation, so adaptivity is rarely needed.

**Notable:** **compatible quaternions matter.** Tests show 0 inner-loop iterations → deformation doesn't converge on the Bridge model. 1 iteration → converges quickly. Pass rotations through the quaternion optimization step before deformation.

**Mesh resolution dependence:** the metric $\Pi$ (Equation 13 in paper) decreases with resolution but compute time scales (~8.5s @ 63k tets, 35.6s @ 143k, 158s @ 390k tets).

**Code:** https://github.com/zhangty019/S3_DeformFDM. Also includes references to **"S4 Slicer"** by Joshua Bird — a simpler educational extension.

**Why S³-Slicer is the current SOTA "general" slicer:** it's the only published method that simultaneously satisfies SF + SR + SQ. Successor work (Neural Slicer 2024) makes it differentiable; corpus paper `2505_03779v1.pdf` (Liu 2025 neural co-opt) further integrates topology optimization.

#### 2.2.3 Deformation for FRC (Li 2025) — `processes1300473.pdf`

The Northwestern Polytechnical (Xi'an) group published an FRC-oriented adaptation in *Processes* 13(2):473, 2025. The novelty vs. S³-Slicer:
- Layer is forced *as parallel as possible to the prescribed fiber-orientation vector field* (rather than the broader SR criterion).
- Vector-field-driven path planning on each layer (see §3.2).
- Separate algorithm for **curved-layer-aware support generation**.

Uses deformed-space mapping but the deformation is constrained to align with a user-prescribed fiber field. Good engineering-level paper; non-Manchester, so worth cross-checking when looking for alternative formulations.

### 2.3 Geodesic-based slicing

Layers are iso-geodesic surfaces from a chosen seed surface (e.g. the part's substrate). Aibuild's commercial product reportedly uses this approach (https://www.designforam.com/p/geodesic-slicing-a-generalised-framework). The corpus has Crane et al. 2013 "Geodesics in Heat" in the bibliography as the underlying numerical method.

**Strengths:** intuitive (layers follow the part shape); plays well with conformal printing on existing substrates.

**Limitations:** seed-surface dependence; doesn't optimize for stress alignment unless geodesic distance happens to align with stress.

### 2.4 Volume / model decomposition (3+2-axis paradigm)

Instead of *continuous* 5-axis motion, decompose the part into chunks each printed at a *fixed* orientation. Within each chunk you can use vanilla 3-axis slicing.

#### 2.4.1 Wu 2020 (RoboFDM-general) — `1812_00606v4.pdf`

**Key idea:** beam-guided search over clipping-plane sequences that minimize total overhang area + decomposition step count, subject to manufacturing constraints. Generalization of Wu/Dai 2017 RoboFDM (predecessor to Dai 2018).

**Pipeline:**
1. Greedy scheme: pick the next clipping plane $\gamma$ that maximizes local objective $J_L$ (descent in risky area).
2. With self-support constraint: require $R(\mathcal{M}^+_c, \gamma) = 0$ (i.e. the region above the plane is fully self-supporting given current orientation).
3. Beam-guided search (multi-branch) to avoid local optima of pure greedy.
4. Supplementary support-structure generation for unavoidable overhangs.

**Hardware:** demonstrated on (a) Cartesian-motion with rotating bed, (b) rotational-motion-based (UR5 + table). Both economic vs. true 5-axis.

**Strength:** simpler than continuous curved-layer methods; works on cheaper hardware; handles loops and high-genus models.

**Limitation:** can produce visible seams between sub-volumes; staircase still present within each chunk.

#### 2.4.2 Han 2025 — `micromachines1601316v2.pdf`

Recent OA paper from Guangxi University. Uses **Pareto multi-objective optimization** over (overhang area, decomposition steps) + **beam search** over decomposition sequences. Engineering-level results on complex models. Confirms the decomposition lineage remains active.

### 2.5 Spherical / ellipsoidal slicing

Slicing primitives that aren't planar.

- **Spherical** (Liu 2024 in bibliography, plus `WO2016178977A1.pdf` patent): useful for truss/lattice structures with spherical accessibility.
- **Ellipsoidal** (Cluster 3 in bibliography): explicit collision and gouging avoidance during decomposition.
- **Patent WO2016178977A1**: Jay Lee's WIPO PCT patent on AM using **spherical coordinates (ρ, θ, φ)**. The patent's `FIG. 1` flowchart shows: (1) Cartesian STL file → (2) Spherical STL file → (3) analysis to determine optimal build point → (4) set ρ = 1 increment → (5) rotate object so entire surface at ρ passes under print head → (6) print all identified points → (7) increment ρ. This is **multi-directional radial printing** rather than true continuous 5-axis, but it's IP to be aware of.

### 2.6 Non-planar within 3-axis (slightly-curved)

Special case: 3-axis hardware that bends G-code locally to follow a tilted top surface. Lower ambition than 5-axis but commercially relevant.

- **CurviSlicer** (§2.2.1) — the principled deformation-based version.
- **Ahlers 2019** (`case_ahlers_2019.pdf`) — Slic3r fork that detects surfaces suitable for non-planar printing and uses a *geometric model of the printhead and extruder* to check collisions. Open-source, practical, runs on common 3-axis printers.
- **CNC Kitchen blog** — maker-grade post-processor that bends planar G-code.
- **Aladag 2021** (`NON_PLANAR_TOOLPATH_FOR_LARGE_SCALE_ADDITIVE10....pdf`) — application of non-planar concepts to *large-scale* AM (LSAM) where larger bead sizes make stair-stepping worse; preliminary experimental results only.

---

## 3. Path generation on a surface

Once you have a curved surface layer, you need a continuous curve (or near-continuous, accepting retracts) filling it. Direct CNC-machining ancestors. Sun et al. 2022 trajectory-planning review (Chinese J. Aeronautics, in bibliography) is the modern survey.

### 3.1 Iso-* family

| Strategy | What it does | When to use |
|---|---|---|
| **Iso-parametric** | Follow surface's parametric (u,v) curves | Easy on NURBS / parametric surfaces. Uneven coverage on curved surfaces. |
| **Iso-planar** | Intersect surface with parallel planes; use intersection curves | Robust on triangle meshes. Standard for 3-axis. Hu/Chen/Tang 2017 is the 5-axis-CNC reference. |
| **Iso-scallop** | Space adjacent paths so the residual "scallop" between them has constant height | Optimal for surface quality, minimizes total path length subject to roughness budget. Suresh & Yang 1994 (machining); transferable to AM via "deposition strip" analogy. |
| **Iso-geodesic** | Iso-surfaces of geodesic distance field | Plays well with curved layers; Crane et al. 2013 heat method is the fast algorithm. |

### 3.2 Vector-field / direction-field methods

The dominant approach for stress-aligned and fiber-aligned printing. The vector field $V$ defines the preferred path direction at each surface point; the path is an integral curve of $V$.

**Foundational tools:**
- **Knöppel et al. 2015** "Stripe Patterns on Surfaces" (in bibliography) — converts a direction field into evenly-spaced stripe patterns on a triangle mesh. Mathematical engine for many multi-axis AM toolpath methods.
- **2-RoSy direction fields** — represents directions modulo 180° (a line, not an arrow). Resolves the **directional ambiguity** of principal-stress fields (where the eigenvalue sign is arbitrary).
- **4-RoSy** — direction modulo 90° (cross field). Used for quad meshing; less common in AM.

**Three core challenges with stress-aware vector fields** (well stated in `2410_16851v2.pdf` Section 1.2, Figure 1):
1. **Directional ambiguity** — principal stresses from FEA come from eigenvalue decomposition; the sign of the eigenvector is arbitrary. Naive smoothing causes vector cancellation ("vanishing problem"). Fix: 2-RoSy representation.
2. **Low fiber coverage** — paths traced as integral curves of $V$ have non-uniform spacing; dense in stress-concentrated regions, sparse elsewhere. Fix: convert to *periodic scalar field* (Knöppel-style) → uniform iso-curve spacing.
3. **Turbulence in stress-concentration regions** — at singular points (bolt holes), $\sigma_1 \approx \sigma_2$ and the field has incompatible regions. Fix: segment out singular regions, treat separately.

### 3.3 The deformation-based S³ family for fiber paths (Manchester pipeline)

**Zhang 2024 spatial fiber** (`2311_17265v2.pdf`):

1. **Stress field processing**: trace principal stress lines (PSLs) as integral curves of $\sigma_{max}$ from sample seed elements. Stop when reaching boundary or max-length.
2. **Curved layer slicing**: optimize scalar field $G$ guided by PSLs → iso-surfaces $\{S\}$ as curved layers (S³-Slicer machinery).
3. **Spatial fiber toolpath generation per layer**: another field optimization, $P$, on each $S$, optimizing for both stress-orientation + toolpath continuity. Iso-curves of $P$ = fiber toolpaths $\mathcal{T}$.
4. Sequence with information for continuity across layers.

**Quantitative results:** up to **644% failure load** and **240% stiffness** improvement vs. planar baseline on tensile tests with complex 3D stress states (Bike Fork model).

**Fang 2024 high-density** (`2410_16851v2.pdf`):

Extension of Zhang 2024 that solves the "low coverage" problem. Uses **2-RoSy direction field → periodic parameterization → iso-curves of the periodic scalar field**. Result: paths with **near-equal hatching distance** even in non-uniform stress regions.

Also extends S³-Slicer for **winding compatibility around holes** — ensures fiber toolpaths can wind coherently around bolt holes (which are stress concentration points).

**Quantitative results:**
- 84.6% improvement in fracture force, 54.4% improvement in stiffness vs. prior method on tensile tests.
- 140.8% improvement in failure load, 84.9% improvement in stiffness on bridge model 3-point bending test.
- SEM cross-sections show visibly denser fiber distribution.

**Hardware used:** ABB 6-DOF robot arm + 2-DOF positioner (8-DoF total). Printhead extrudes PLA matrix + PVA support + Markforged CF-FR-50 continuous carbon fiber.

### 3.4 Vector-field driven path planning on a layer (Li 2025) — `processes1300473.pdf`

Different approach (Northwestern Polytechnical):
1. From the desired fiber orientation field, compute a **scalar potential field $\phi^q$** on each curved layer such that $\nabla\phi^q$ aligns with the orientation field.
2. Extract iso-lines of $\phi^q$ at spacing $\Delta\phi^q$ to get hatching paths.
3. **Continuity via Eulerian graph construction**: trim iso-lines by inward-offset boundary contours; renumber intersection vertices; build a graph where each vertex has degree 2; identify connected sub-graphs via DFS; connect adjacent sub-graphs by inserting bridges $Q_k$ at distances $L_k = \Delta\phi^q / \sin\theta_k$. Result: single Eulerian path traversable by Fleury's algorithm.

This is the **continuous-path-on-a-layer** algorithm — important for fiber AM because every retract means a fiber cut.

### 3.5 Space-filling curves

For when continuity matters more than direction:

- **Fermat spirals** (SFCDecomp) — single-stroke coverage with controlled spacing. Used in some commercial slicers.
- **Hilbert curves** — `3dp_2020_0048.pdf` (Loh 2022) uses Hilbert area-filling for functionally graded FDM, varying local compliance by varying curve parameters. Demonstrates a shoe-sole case study.

### 3.6 Medial-axis-based and other niche

- **Medial axis transform (MAT)**: especially useful for thin-walled or branching geometries. Coupek 2018 (bibliography) in AM; DED-IM (cluster 7) in WA-DED. Innovative DED-Arc 2025 uses medial-axis + active decomposition + Bézier offset.
- **Stress-line tracing**: directly trace stress lines as toolpaths (Xia, Liu). Simple but fails in turbulent regions; superseded by scalar-field methods.
- **"Wave projection"** (Ren, Liu in references): link vector field to phase/scalar field via wave functions. Has continuity problems for fiber AM (can't represent path discontinuities).

### 3.7 Iso-planar mesh paths in 5-axis (Li 2026) — `appliedmath0600035.pdf`

Machining paper, but the algorithmic structure transfers. End-to-end 5-axis end-milling on a triangle mesh:
1. **Clustering analysis** for optimal workpiece orientation.
2. **Normal vector distribution analysis** to segment shallow vs. steep regions.
3. **GPU-accelerated collision detection** for feasible tool-orientation domains.
4. **Iso-planar tool paths + TSP optimization** for tool lifting/movement between regions.

Useful as a template for "end-to-end" 5-axis pipelines in AM. The shallow/steep segmentation maps cleanly to AM's "regions printable directly" vs. "regions needing reorientation."

### 3.8 Conformal printing on existing surfaces (Rodriguez-Padilla 2021) — `applsci1107509.pdf`

Algorithm for projecting a 2D pattern (lattice, infill) onto an arbitrary non-planar **tessellated** surface. Practical, implementation-oriented. Math: per-triangle local frame + barycentric interpolation. Useful as a building block for conformal AM on existing substrates.

---

## 4. Continuous fiber reinforcement (CFRTPC)

The single largest thread in this corpus. Multiple papers, anchored in the Manchester group. Key vocabulary: **CFRTP** = continuous fiber reinforced thermoplastic; **CFRTPC** = same + "composite"; **CCF** = continuous carbon fiber; **CFRP** = continuous fiber reinforced polymer (umbrella, can be thermoset).

### 4.1 Why fiber alignment matters mechanically

Fiber composites have *anisotropic* properties. Maximum strength is along the fiber axis. Two design principles, both supported by mechanical testing in the corpus papers:

1. **Continuous fibers placed along the directions of maximal principal stress.** [Sugiyama 2020; Heitkamp 2023; Zhang 2024]
2. **Loops of continuous fibers connecting multiple load-bearing regions** (so loads transfer through fiber rather than through matrix-fiber interface). [Li 2020; Sugiyama 2020]

Failure modes observed in mechanical tests (Zhang 2024 et al.):
- **Matrix cracking** — when matrix is the weakest link, fix by adding fiber.
- **Delamination** — between layers when fiber isn't aligned with stress.
- **Fiber pull-out** — at fiber/matrix interface; dense fiber packing increases this *but improves overall strength*.
- **Fiber breakage** — the *desirable* failure mode (means fiber was bearing significant load).

### 4.2 Why curved layers + multi-axis matter for CFRTPC

In **planar-layer** CFRTPC printing, fibers are constrained to in-plane directions only. This is a "2.5D" approach (Markforged, Anisoprint, 9T Labs all use this; see §4.6). It fundamentally cannot align fibers with 3D principal stress directions in geometries where stress flows out-of-plane (e.g., GE-bracket benchmark model with bolted joints connecting through-thickness).

Multi-axis AM with curved layers solves this. The key insight: by tilting the layer surface to follow the stress field, in-layer fibers can align with the 3D stress directions.

### 4.3 The fiber AM pipeline (Manchester)

The Manchester group's papers form a coherent pipeline:

```
[Fang 2020 Reinforced FDM]   → vector-field multi-axis path planning, up to 6.35× load capacity
        ↓
[Zhang 2022 S³-Slicer]       → general multi-axis slicer, multi-objective SF+SR+SQ
        ↓
[Zhang 2024 spatial fiber]   → curved layers + 3D stress, scalar-field paths
                               + dual-robot hardware with normal-force consolidation
                               644% failure load improvement
        ↓
[Fang 2024 high-density]     → 2-RoSy + periodic param for uniform fiber spacing
                               + winding compatibility around holes
                               140.8% failure load on bridge model
        ↓
[Liu 2025 neural co-opt]     → joint topology + layers + paths via neural fields
                               uses Hoffman criterion (not just principal stress)
                               supports 5/3/2.5-axis with same framework
```

### 4.4 Toolpath strategies for CFRTP (taxonomy from `2410_16851v2.pdf`)

**Geometric rule-based** (the industry default):
- Zigzag, sinusoidal, spiral, cellular, contour-parallel, hybrid (Markforged Eiger uses zigzag).
- Simple to implement, low compute. Doesn't exploit stress alignment.

**Stress-driven explicit (tracing-based)**:
- Stress vector tracing (SVT) — trace from element to element along $\sigma_{max}$.
- Load-dependent path planning (LPP) — extension with min-bead-width constraint.
- Anisoprint commercial product uses something like this.
- **Weakness:** requires pre-processing (orientation flipping); fails in turbulent regions.

**Field-based implicit**:
- Extract iso-curves from a scalar field $\phi$ optimized to align with stress.
- Sugiyama 2020 iterative refinement; Manchester papers; Li 2025.
- **Weakness:** general scalar fields produce non-uniform spacing → sparse coverage.

**Periodic scalar field** (Fang 2024 high-density):
- Resolves both ambiguity and uniform-spacing problems simultaneously.
- Currently the most fiber-dense method published.

### 4.5 Manufacturing constraints specific to fibers

Constraints that don't apply to pure FDM but do constrain CFRTP toolpaths:

- **Min turning angle** — continuous fiber has a finite minimum bend radius. Sharp corners cause fiber buckling/misalignment. Manage during path planning (Huang 2023 turning-angle optimization).
- **No overlapping deposits** — fibers can't pile up the way matrix can. Hatching distance must be ≥ fiber width.
- **Fiber misalignment / breakage** — Zhang 2021 characterized; risk increases with multi-axis motion.
- **In-nozzle vs. out-of-nozzle impregnation** — two competing strategies for combining fiber + matrix. In-nozzle (Markforged) is simpler; out-of-nozzle (research) allows higher fiber volume fraction.
- **Normal-force consolidation** — Zhang 2024's dual-arm setup applies a normal force during deposition to compact the fiber/matrix. Improves interlaminar adhesion in curved-layer printing.

### 4.6 Commercial CFRTP systems (planar-layer baseline)

For reference / benchmarking. None of these do curved-layer multi-axis CFRTP commercially yet (as of 2026):

| System | Approach | URL | Notes |
|---|---|---|---|
| **Markforged** | Planar zigzag, in-nozzle impregnation | markforged.com | Industry leader, Eiger software |
| **Anisoprint** | Planar, stress-field guided | anisoprint.com | Coextrusion approach |
| **9T Labs** | Planar, towpreg | 9tlabs.com | Higher fiber volume fraction |

Research note from Zhang 2024 abstract: planar-layer CFRTP achieves "2.5D" placement only. Multi-axis is needed for truly 3D stress fields.

### 4.7 Topology optimization for fiber composites

Two papers in corpus integrate TopOpt with fiber AM:

**Wu, Liu, Liu 2024** — `materials1702005.pdf`. Compares 2.5D vs. 3D vs. 3D-with-directional-material-removal TopOpt for fiber composites. Counter-intuitive finding: **simpler 3D topologies can outperform complex ones** because larger cross-sections give more degrees of freedom for fiber-path layout and improve inter-layer bonding. CFRPLA from ESUN, printed on JGMAKER JG-E6 (0.4mm nozzle, 240°C/60°C, paths in Cura 5.0).

**Liu 2025 neural co-opt** — `2505_03779v1.pdf`. Joint optimization of (topology, curved layer sequence, path orientations) via three implicit neural fields. Uses **Hoffman criterion** (failure index >1.0 = yielded) instead of pure principal-stress alignment — allows trading off strength against manufacturability. Supports 5/3/2.5-axis with the same framework. Differentiable end-to-end. On the GE-Bracket benchmark at 15% volume fraction, the 5-axis co-optimized result achieved $F_f = 1.519$ kN vs. the sequential 5-axis result's $F_f = 1.141$ kN — i.e. **co-optimization beats sequential design even with the same hardware capability**.

**Moter 2021** — `2112_02030v2.pdf`. 2D TopOpt of orthotropic materials with raster angle as explicit design variable (per-element fictitious density + angle). Stress-constrained via modified SIMP + MMA. Adjusted P-norm clustering for max-stress in principal material coordinates. 2D focused but formulation is generic.

### 4.8 Stress-constrained orientation TopOpt — alternative formulations

In addition to the joint-optimization papers above:

- **Direction-Oriented Stress-Constrained TopOpt** (`2112_02030v2.pdf` Moter) — raster angle as DV.
- **Self-support TopOpt + curved layers** (CMAME 2025, bibliography) — concurrent topology + slicing + sequence.
- **Stress-oriented image-processing path opt** (CIRP Annals, bibliography) — different formulation.

---

## 5. Kinematics, IK, singularities

Once you have a 3D toolpath with nozzle orientations, convert to machine joint values respecting velocity/acceleration/jerk limits and avoiding singularities. AM literature thins out here; read the machining literature.

### 5.1 Forward and inverse kinematics for an RRTTT 5-axis (Grandguillaume 2015) — `Grandguillaume_Lavernhe_Tournier_HSM_2015.pdf`

**Setting:** classic 5-axis structure with 3 translation axes (X, Y, Z) plus 2 rotation axes. The corpus paper uses **A-C rotary** configuration (rotation about X-axis and Z-axis).

**Forward kinematics for RRTTT (A on X-rot, C on Z-rot):**
$$i = \sin(C)\sin(A), \quad j = -\cos(C)\sin(A), \quad k = \cos(A)$$
where $(i, j, k)$ is the tool-axis direction in the part frame.

**Inverse kinematics has two solution domains** corresponding to $A > 0$ or $A < 0$:

| Sign region | $A_1, C_1$ solution | $A_2, C_2$ solution |
|---|---|---|
| $j < 0$ | $A_1 = \arccos(k), C_1 = -\arctan(i/j)$ | $A_2 = -\arccos(k), C_2 = -\arctan(i/j) + \pi$ |
| $j = 0$ | depends on $i$ sign | depends on $i$ sign |
| $j > 0$ | $A_1 = \arccos(k), C_1 = -\arctan(i/j) + \pi$ | $A_2 = -\arccos(k), C_2 = -\arctan(i/j)$ |

**Singular configuration:** $i = 0$ **and** $j = 0$ — i.e. when the tool axis is along $(0,0,1)$, the rotation about C is undefined (any C value gives the same tool axis). The machine has no preferred orientation; any infinitesimal change in $(i,j)$ produces large C swings.

### 5.2 Why singularities matter

Two problems near the singularity:

1. **Solution-space swapping**: when $j$ changes sign, the choice between $A_1/C_1$ and $A_2/C_2$ branches changes. Without care this produces up to **180° discontinuities in C-axis** position — the machine has to make a near-instantaneous large rotary motion.
2. **Slowdowns**: the controller respects max velocity/acceleration/jerk on each axis. When C has to swing rapidly, the feedrate is forced down → marks on the part, productivity loss.

### 5.3 Singularity avoidance strategies (taxonomy)

From the bibliography "Singularities cause/effect/avoidance" 2017 review + the corpus paper:

| Strategy | Idea | Reference |
|---|---|---|
| **Path deformation** | Pre-process the toolpath to bend it away from the singularity | Affouard 2004 (bibliography) |
| **Geometric constraints** | Pose orientation as constrained optim, exclude near-singular region | Wan 2018 (bibliography) |
| **Damped pseudoinverse** | Damped Jacobian → smooth IK through singularity at cost of trajectory error | "Closed-loop IK around singular points" 2023 (bibliography) |
| **Pass-through with B-splines** | Fit B-spline to rotary positions near singularity, modify to pass exactly through the singular point while respecting velocity/accel/jerk limits | **GLT 2015 (this corpus paper)** |
| **C3-continuous B-spline tool path** | Make whole path $C^3$-continuous so derivatives don't spike near singularity | Yang (bibliography) |
| **Modify rotation only** | Modify axis-rotation position near singularity so the new position passes exactly *through* the singularity point | Sørby 2007 (bibliography) |
| **Tool-axis reorientation in (i,j) plane** | Analyze tool path in the (i,j) plane; modify tool orientation to remove/soften incoherent movements | Tournier (referenced from GLT 2015) |

**GLT 2015 approach (corpus paper):**
1. Detect incoherent rotary movements during machining simulation (large jumps in C with small changes in tool axis).
2. Fit B-spline curves to the rotary-axis positions near the singularity point.
3. Modify the curves to *go through* the singularity exactly (rather than around).
4. Re-discretize for linear interpolation in the controller.
5. Validate experimentally for max velocity / acceleration / jerk.

Velocity/acceleration/jerk in articular space:
$$\dot{\mathbf{q}} = \mathbf{q}_s(s) \cdot \dot{s}, \quad \ddot{\mathbf{q}} = \mathbf{q}_{ss}(s) \dot{s}^2 + \mathbf{q}_s(s) \ddot{s}, \quad \dddot{\mathbf{q}} = \mathbf{q}_{sss}(s)\dot{s}^3 + 3\mathbf{q}_{ss}(s)\dot{s}\ddot{s} + \mathbf{q}_s(s)\dddot{s}$$
where $s$ is path parameter. For controller-limit analysis, tangential accel/jerk along the path can be neglected when feedrate is rapidly varying (i.e. exactly when the singularity matters).

### 5.4 Numerical chain in 5-axis (CAM → NC)

```
CAD → CAM (toolpath)  ────→  POST-PROCESSOR  ────→  NUMERICAL CONTROLLER  ────→  MACHINE
       (Xp,Yp,Zp,i,j,k)        (Xm,Ym,Zm,A,C)        (joint commands)            (servos)
       part-frame             machine-frame
                              OR
                              hybrid (Xp,Yp,Zp,A,C)
```

Three forms for the toolpath:
1. **Part-frame only** $(X_p, Y_p, Z_p, i, j, k)$: machine-independent. CAM tool can output once; NC unit does the IK at runtime.
2. **Machine-frame only** $(X_m, Y_m, Z_m, A, C)$: machine-specific. Postprocessor does the IK once; you control machine motion explicitly.
3. **Hybrid** $(X_p, Y_p, Z_p, A, C)$: kinematic part-frame motion but explicit rotaries.

Forms 2 and 3 give you control over kinematic performance (because you've already chosen the IK branch and can smooth it) but are not portable across machines.

### 5.5 Implications for AM slicer design

- An **AM slicer** that outputs part-frame G-code with $(X, Y, Z, i, j, k)$ tool orientations is most portable but offloads the singularity problem to whoever post-processes.
- A **slicer that targets a specific machine** can do the IK + singularity smoothing internally (S³-Slicer mentions "singularity-aware motion planning" as Step 6 in its broader pipeline, with a separate GitHub project).
- For robot-arm hardware (Manchester ABB setup, Dai UR5), the kinematic chain is **different** — typically a 6-DOF serial arm + 2-DOF positioner = 8 DOF. The singularity structure is different (wrist singularities, elbow singularities) and IK is solved differently. The corpus has Liu & Huang 2019 (hybrid-robot kinematics) in the bibliography.

### 5.6 The WPI thesis on 5-axis IK — `WPI_undergrad_thesis_5Axis_3D_printing.pdf`

This is an end-to-end engineering thesis. Hardware: stationary nozzle + 3-Cartesian-axis bed + 2 rotary axes (A, B) on the build plate. Software stack covers:

1. **Volume decomposition** (Section 3.2.1, p.17): detects overhanging features, generates "sub-volumes" each printable without supports.
2. **Build direction per sub-volume** (3.2.2, p.25).
3. **Build sequencing** (3.2.3, p.30).
4. **Collision detection** (3.2.4, p.31).
5. **5-axis G-code generation** (3.2.5, p.33).
6. **Forward kinematics** (3.3.4, p.39): standard transformation matrix derivation for moving bed + rotation axes A, B.
7. **Inverse kinematics** (3.3.5, p.44): closed-form solution for their specific kinematic structure.
8. **Embedded control** (Section 3.4): control loop, stepper operation, closed-loop feedback.

Limited to "simple overhanging features" (per the thesis abstract). Useful as a **complete reference implementation** at the undergraduate-engineering level — covers all the pieces an end-to-end slicer needs.

### 5.7 Trajectory planning (path → motion)

After IK, you still need to compute a **time-parameterized trajectory** respecting feedrate, acceleration, jerk on each axis. Sun et al. 2022 (Chinese J. Aeronautics, bibliography) is the modern review of trajectory planning for free-form-surface machining. The Wang & Tang 2007 paper (bibliography) is the key reference for incorporating rotary-axis angular-velocity limits **into** the toolpath search itself rather than as a post-smoothing step.

For high-speed milling-style requirements, the trajectory planner must be **$C^2$ continuous in position** (and ideally $C^3$ for jerk continuity).

---

## 6. Hybrid additive + subtractive manufacturing (HASM)

5-axis hybrid machines (AM head + CNC spindle) are commercially mature (Mazak, DMG Mori, Hybrid Manufacturing Technologies). Algorithmic planning is less mature.

### 6.1 Chen 2025 — `2509_10599v1.pdf` (Manchester, latest)

**Approach:** "inverse operation" based planning. Plan a sequence of (additive, subtractive) operations that progressively *transforms the target model into a null shape* via inverse operations.

**Theoretical contribution:** prove that **any model can be fabricated exactly** by a sequence generated by their approach.

**Implementation:** voxel-based, scalable. Plans interleaved AM/SM steps where:
- AM adds material (possibly with temporary supports, visualized as green voxels)
- SM removes material (including supports)
- Both ensure **manufacturability and structural stability** of intermediate shapes

Pre-added supports (purple in Fig. 1) are placed during a preparation stage and removed at the very end. Demonstrated on the GE-Bracket model (the same benchmark used in Manchester's CFRTP work — Manchester has a model menagerie).

This is the **most general** hybrid-planning algorithm published. It supersedes prior work that decomposed into pre-defined slabs or blocks.

### 6.2 Freitas 2025 review — `materials1804249.pdf`

OA review of hybrid manufacturing. Covers:
- Process taxonomy: AM-then-SM, SM-then-AM, interleaved, combined-in-single-toolhead.
- Hardware integration: which commercial systems offer what.
- Sensor integration: in-process metrology, closed-loop correction.
- Software: process planning (cluster 6 of bibliography).
- Materials: metal hybrid mostly (DED + milling), some polymer.

Good orientation read for the field.

### 6.3 VASCO and the recent CMAME work (bibliography only, not in PDFs)

- **VASCO** (Zhong 2023): Volume-And-Surface Co-decomposition. Slab-based dynamic-directed graph + beam-guided block decomposition. Was the SOTA before Chen 2025.
- **TopOpt for HASM** (CMAME 2024): joint topology + 5-axis HASM with dynamic AM/SM alternation.
- **Recursive volume decomposition** (J. Manuf. Sys 2024): decision-criteria-driven recursive decomposition.

### 6.4 The hybrid-AM-relevant case from the corpus PDFs

- `2509_10599v1.pdf` Chen 2025 — see §6.1, the main one.
- `materials1804249.pdf` Freitas 2025 — review, §6.2.
- `PartScale_build_orientation_opitimization.pdf` Cheng & To 2019 — adjacent: voxel-based residual-stress-aware orientation optimization for metal powder-bed AM. Not strictly hybrid but the voxel methodology is similar and used in some HASM planners.

---

## 7. Hardware archetypes

Five common configurations:

### 7.1 Gantry + 2-axis rotating/tilting bed

- Standard FDM XYZ Cartesian gantry, 2 rotary axes (A + B, or A + C) added to the build plate.
- **Examples:** Duarte 2022 system (`Duarte_Xana_Teresa_ismael_curved.pdf`), WPI thesis (`WPI_undergrad_thesis_5Axis_3D_printing.pdf`), Murtezaoglu 2018 (bibliography), Open5x (`2202_11426v2.pdf`), Fractal 5 Pro (bibliography).
- **Pros:** mechanically simple, builds on existing FDM stack, IK is straightforward (Sørby formulas apply).
- **Cons:** rotating bed limits part weight + size; collision envelope is awkward when bed tilts.

### 7.2 Gantry + 2-axis rotary head

- XYZ Cartesian, 2 rotary axes on the print head (e.g., 5AXISMaker, some research systems).
- **Pros:** part stays still → can be heavy/large.
- **Cons:** moving rotary axes on head adds mass to the moving carriage → vibration, lower max acceleration; cable management.

### 7.3 6-DOF robot arm

- 6-DOF industrial arm (UR5/UR10, ABB IRB) with printhead end-effector.
- **Examples:** Dai 2018 (UR5 — `SIG18RobotVolPrint.pdf`), most Manchester papers, ETH Gramazio-Kohler.
- **Pros:** maximum orientation freedom; large work volume; off-the-shelf robotic platform; can be combined with a positioner for ≥8-DOF.
- **Cons:** lower precision than gantry (Dai notes 0.1mm repeatability vs. <0.01mm for high-end gantry); proprietary controllers complicate G-code; serial-arm singularities.

### 7.4 6-DOF arm + 1-2 axis positioner

- Robot arm holds printhead; positioner holds workpiece. Total 7-8 DOF.
- **Examples:** Zhang 2024 spatial fiber (`2311_17265v2.pdf`) — dual robotic arms with normal-force consolidation; Fang 2024 (`2410_16851v2.pdf`) — ABB + 2-DOF positioner (8 DOF total).
- **Pros:** redundant DOFs let the planner avoid singularities and improve reach.
- **Cons:** even more complex IK; need to coordinate two devices in real time.

### 7.5 Hybrid CNC platforms (5-axis CNC + AM head)

- Existing 5-axis CNC machining center, AM head fitted in tool changer or as add-on.
- **Examples:** Mazak Integrex, DMG Mori LASERTEC, Enomoto Kogyo 5-axis hybrid (industry, bibliography).
- **Pros:** mature kinematics + controller; can switch between AM and SM in single setup; high precision.
- **Cons:** expensive; AM thermal management vs. CNC cooling fluids; controller integration.

### 7.6 Wireframe / spherical / specialty

- **Wu, Peng et al. 2016 5DOF wireframe printer** (bibliography) — strings of filament in mid-air. Different paradigm.
- **WO2016178977A1 spherical-coordinate printer** (corpus patent) — printhead at radius $\rho$, rotate the part about $\theta$ and $\phi$. Effectively a 5-DOF radial system. Different IK entirely.

### 7.7 Open-source retrofit projects (worth knowing)

| Project | Base printer | License | URL |
|---|---|---|---|
| **Open5x** (Hong 2022, corpus paper) | Prusa i3 MK3s | Open hardware + Rhino/Grasshopper slicer (license not specified in CHI paper — verify) | https://github.com/HongFreddy/open5x |
| **Rep5x** | Ender 5 Pro / Ender 3 V3 SE | GPL v3 | https://github.com/dennisklappe/Rep5x |
| **Fractal 5 Pro** | Voron-based design | check repo | https://fractal-robotics.com/ |

GPL-license implication for Rep5x: any derivative software you ship must be GPL too. If you're building a proprietary commercial slicer, avoid vendoring Rep5x.

### 7.8 Large-scale (LSAM)

Different design constraints. Larger nozzles (10-25mm vs. 0.4mm), pellet-fed extruders instead of filament, single-screw vs. dual-screw extruders, robot-arm or gantry-on-rails systems.

- **Thermwood (US20180056602A1 corpus patent)** — closed-loop extrusion control for LSAM: pressure sensor on the melt, adjusts pump speed and extruder screw speed based on sensed pressure and translation rate. Anti-stringing, anti-starve-feed control.
- **ORNL/UT-Battelle (US20170320267A1 corpus patent)** — variable-width deposition via rotatable **non-circular nozzle** (e.g., rectangular outlet). The angular orientation of the outlet relative to path direction defines bead width. Trades high deposition rate against fine resolution within a single print.
- **Aladag 2021** — non-planar toolpaths for LSAM, preliminary experimental results. Discretization effects are *worse* at large scale because beads are bigger.
- **Brian 2022 concrete** (`3dp_2020_0335.pdf`) — 6-axis robotic concrete printing for NASA habitat challenge. Non-coplanar layers, embedding of utilities, 1/3-scale fully enclosed structure without support.

---

## 8. Coverage map — strong / moderate / weak in this corpus

**Strong** (dozens of papers, multiple competing methods, OSS code available):
- Scalar-field-based curved-layer slicing for support-free fabrication (Dai 2018 → S³-Slicer → Neural Slicer)
- Deformation-based curved-layer slicing (CurviSlicer → S³-Slicer)
- Stress-aligned multi-axis printing for fiber composites (Fang 2020 → Zhang 2024 → Fang 2024)
- 5-axis CNC tool-path generation (mature field — Lasemi 2010, Hu 2017, Li 2026)
- Hybrid AM+SM 5-axis process planning (VASCO → Chen 2025)

**Moderate** (solid handful of papers, room for new work):
- Multi-axis path planning for branching / multi-genus topologies
- Collision detection between nozzle assembly and previously-printed material
- Continuous-fiber multi-axis path planning *high-density coverage* problem (Fang 2024 is the only published solution as of 2026)
- Variable layer thickness in curved-layer settings (S³-Slicer applies it "only when necessary")
- 5-axis singularity smoothing (machining-mature; AM less so)

**Weak / open** (few papers, mostly conceptual):
- In-process correction / closed-loop control on 5-axis AM (Bhatt et al. and multi-robot WAAM are early)
- Topology-aware path planning that robustly handles holes, branchings, and high-genus
- Slicer-aware machine design (most slicers assume specific kinematics)
- **Open-source 5-axis slicer for hobbyist hardware** — explicitly called out as a gap by the Open5x team and the broader community. Fractal 5 Pro's Python slicer is closest but young.
- Real-time replanning for adaptive printing
- Standardized G-code / toolpath formats for 5-axis AM

---

## 9. Anchor-10 reading order

If you only have time for ten papers, read these in this order:

1. **Lasemi 2010 review** (bibliography) — machining baseline
2. **Sun 2022 trajectory review** (bibliography) — modern machining trajectory planning
3. **Wang 2024 multi-axis review** (bibliography) — AM map of the field
4. **Sørby 2007** (bibliography) — 5-axis IK & singularities mental model
5. **Dai 2018** (`SIG18RobotVolPrint.pdf`) — AM anchor paper, scalar-field paradigm
6. **CurviSlicer 2019** (`2019CurviSlicer.pdf`) — deformation paradigm, read code too
7. **Fang 2020 Reinforced FDM** (bibliography) — stress alignment + multi-axis
8. **S³-Slicer 2022** (`3550454_3555516.pdf`) — current SOTA general slicer, read code too
9. **VASCO 2023** (bibliography) or **Chen 2025** (`2509_10599v1.pdf`) — hybrid AM/SM
10. **Yi 2024 Neural Slicer** (bibliography) or **Liu 2025 co-opt** (`2505_03779v1.pdf`) — neural-field current frontier

After these ten, next steps depend on sub-problem:

| If you're working on… | Read next |
|---|---|
| Slicer architecture | CurviSlicer code, S³-Slicer code, Open5x slicer code |
| Path-on-surface generation | Knöppel 2015 (bibliography), Crane 2013 (bibliography), Iso-scallop machining papers |
| Kinematics / singularities | Sørby 2007, GLT 2015 (`Grandguillaume_...`), Wang & Tang 2007 (bibliography) |
| Stress alignment | Fang 2020, Zhang 2024 (`2311_17265v2.pdf`), Liu 2025 (`2505_03779v1.pdf`) |
| Hybrid AM+SM | VASCO, Chen 2025 (`2509_10599v1.pdf`), Freitas 2025 review |
| Continuous fiber | Zhang 2024 + Fang 2024 (both in PDFs) |
| End-to-end engineering example | WPI thesis (`WPI_undergrad_thesis_5Axis_3D_printing.pdf`), Open5x (`2202_11426v2.pdf`) |

---

## 10. Key people and groups

| Name | Affiliation | Why |
|---|---|---|
| **Charlie C.L. Wang** | University of Manchester (formerly TU Delft, CUHK) | By far the most prolific group in algorithmic multi-axis AM. ~40% of cited algorithmic papers. |
| Tianyu Zhang, Guoxin Fang, Chengkai Dai, Chenming Wu, Yuming Huang | Manchester | Wang's students; lead authors on the major papers |
| **Sylvain Lefebvre** | Inria, MFX team (Nancy) | CurviSlicer, IceSL, SLA work. Co-author on Dai 2018 and S³-Slicer. |
| **Sanjay Joshi** | Penn State | Xinyi Xiao's 5-axis support-free process planning |
| **Matthew Frank** | Iowa State | Hybrid AM+SM process planning |
| **Andy Gleadall** | Loughborough | FullControl GCode Designer, direct-G-code design |
| **Gershon Elber** | Technion | Accessibility analysis, 5-axis machining geometry |
| **Sanjay Sarma** | MIT | Historical machining/AM (Balasubramaniam, Putta theses) |
| **Lin Lu** | Shandong / Peking U | VASCO, computational fabrication |
| **Daniele Panozzo** | NYU | CurviSlicer co-author, geometry processing |
| **Aibuild + 5AXISWORKS** | Industry (UK) | Funder of S³-Slicer; commercial development partner. Aibuild commercial product uses geodesic slicing (separate from S³-Slicer). |

Manchester's GitHub: https://github.com/zhangty019, https://github.com/daichengkai (separate orgs but Wang group).

---

## 11. Patents in the corpus (NOT an FTO sweep)

| Patent | Title | Assignee | Status | Relevance |
|---|---|---|---|---|
| **US20130189435A1** (`US20130189435A1.pdf`) | Three-Dimensional Printing System Using Dual Rotation Axes | Mackie et al. (individuals, Madison WI) | Application 2013 | Hardware: dual-rotation-axis printer (rotating arm + rotating platform). Check if granted/abandoned. |
| **US20170320267A1** (`US20170320267A1.pdf`) | Variable Width Deposition for Additive Manufacturing with Orientable Nozzle | UT-Battelle (ORNL) | Application 2017 | **Rotatable non-circular nozzle** for variable bead width. Relevant to any slicer controlling extrusion width via head orientation. |
| **US20180056602A1** (`US20180056602A1.pdf`) | Methods and Apparatus for Processing and Dispensing Material During AM | Thermwood | Application 2018 | Pressure-sensed closed-loop extrusion control for LSAM. Coordinated control of pump and extruder screw based on translation rate. |
| **WO2016178977A1** (`WO2016178977A1.pdf`) | System and Method for Additive Manufacturing Using **Spherical Coordinates** | Jay Lee (individual) | WIPO PCT 2016 | Different paradigm: $(\rho, \theta, \phi)$ machine coordinates rather than Cartesian. |
| (in bibliography only) US11701813B2 | Multi-input print heads with microfluidic mixing | various | Granted 2023 — likely active | Recent multi-axis printing patent worth FTO-screening |
| (in bibliography only) US7291002B2 | 3D printing apparatus and methods | various | Filed 2003 — likely expired or near | Continuous radial printing about a rotating build table |
| (in bibliography only) EP3117982A1, CN106273450A | Variable-width nozzle / multi-axis multi-jet | various | Application | Hardware patents |

> **Caveat repeated** from README.md and `gaps_and_next_steps.md`: this is a *starting point* for FTO analysis, not legal advice. Patent claims are interpreted by lawyers. Run USPTO, Espacenet, WIPO PATENTSCOPE, CNIPA searches before commercial deployment. See `gaps_and_next_steps.md` § 2 for suggested search strings.

---

## 12. Open problems

From the corpus papers' explicit limitations/future-work sections plus the project's `gaps_and_next_steps.md`:

1. **High-density fiber coverage** in 3D space is *just* solved (Fang 2024 high-density). Validation outside Manchester is open.
2. **Closed-loop in-process correction on 5-axis AM** — currently early-stage. Multi-Robot WAAM and Bhatt 2022 are starting points. The corpus's `1s2_0S2666496825000020main.pdf` (He 2025 OSS WAAM) provides an OSS architecture but not the correction algorithm.
3. **Topology-aware path planning** — high-genus, branching parts still cause issues for all curved-layer methods. Decomposition methods (§2.4) handle topology better but produce visible seams.
4. **Open-source end-to-end 5-axis FDM slicer** — community gap explicitly noted by Open5x team and Fractal Robotics. CurviSlicer is 3-axis; S³-Slicer is research-grade; FullControl is direct-G-code (not a slicer); no production-quality OSS option exists.
5. **Multi-material curved-layer printing** — hinted at by Reinforced FDM (dual-material) and Liu 2026 multi-axis DLP (variable cure) but underdeveloped.
6. **Standard G-code dialect for 5-axis AM** — every system uses its own (Marlin extensions, Klipper extensions, RepRapFirmware Duet config, robot-vendor specific). 3MF can carry the metadata but the toolchain isn't there.
7. **Slicer-aware machine design** — most slicers assume specific kinematics; a general-machine slicer that takes a URDF/DH description and adapts is open.
8. **Real-time replanning** — adapting to in-process measurement (warpage, layer defects). Cheng & To 2019 (`PartScale_build_orientation_opitimization.pdf`) is part-scale orientation only, not real-time.
9. **Layer adhesion and inter-layer mechanics in curved-layer printing** — physical-experimental papers exist (separate from algorithmic ones) but the corpus's coverage is light.
10. **Resin-based multi-axis** (DLP/SLA on rotating platforms) — Liu 2026 (`2604_12236v1.pdf`) shows variable-exposure curing for multi-axis DLP. Small subliterature.
11. **Powder-bed-based 5-axis** — mostly impractical due to powder-bed physics; some hybrid PBF systems exist but the corpus doesn't cover this in depth.
12. **Chinese-language literature** — explicit gap, see `gaps_and_next_steps.md`. The Manchester papers reference some Chinese-language work but the corpus didn't search CNKI/Wanfang directly.
