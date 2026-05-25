# Annotated Bibliography — 5-Axis Slicing & Path Planning

Each entry is formatted:

> **[Authors, Year]** — Title. *Venue*. DOI/URL.
> *Access:* `<tag>` | *IP/use:* `<tag>`
> Relevance: brief note on what this paper contributes to your project.

The "Relevance" notes are my paraphrases. Paper claims should be re-verified before being cited in your own work.

---

## 1. Reviews & surveys (start here)

**[Wang et al., 2024]** — A comparative review of multi-axis 3D printing. *Journal of Manufacturing Processes / J. Manuf. Sys.* https://www.sciencedirect.com/science/article/abs/pii/S1526612524004432
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Synthesizes the unified workflow of multi-axis 3D printing, comparing technologies and implementation mechanisms across slicing, path planning, and machine architecture. Useful as a structured map of the field — gives you the taxonomy to organize your own work.

**[Anonymous review, 2024]** — A review of multi-axis additive manufacturing: Potential, opportunity and challenge. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S2214860424001210
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Covers four sub-areas: curved layers for staircase elimination, multi-axis support-free, load-path planning for mechanical optimization, and large-scale multi-axis machines. Same general scope as the Wang review above; useful to cross-check.

**[Rajan et al., 2025]** — A comprehensive analysis of non-planar toolpath optimization in multi-axis 3D printing. *Review of Applied Science and Technology* 4(2). https://rast-journal.org/index.php/RAST/article/view/22
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Recent (2025) review specifically on curved-layer slicing strategies. Less rigorous than the *AM* journal reviews but freely available and useful as a survey of slicing-strategy options.

**[Sun et al., 2022]** — Path, feedrate and trajectory planning for free-form surface machining: a state-of-the-art review. *Chinese Journal of Aeronautics* 35(8). https://doi.org/10.1016/j.cja.2022.02.014
*Access:* `OA` (typically) | *IP/use:* `Cite-and-paraphrase`
The machining counterpart to the AM reviews above. Covers iso-parametric, iso-planar, iso-scallop, vector-field, and other strategies — most of which transfer directly.

**[Lasemi et al., 2010]** — Recent development in CNC machining of freeform surfaces: A state-of-the-art review. *Computer-Aided Design.* (cited heavily; classic anchor) https://www.sciencedirect.com/science/article/abs/pii/S0010448510000539
*Access:* `Paywalled` | *IP/use:* `Reference-only`
The foundational review of 5-axis CNC tool path generation, tool orientation, and tool geometry selection for freeform surfaces. Read this before reading any of the machining-side primary literature.

**[Vector-field machining review, 2025]** — A Review of Vector Field-Based Tool Path Planning for CNC Machining of Complex Surfaces. *Symmetry* 17(8). https://www.mdpi.com/2073-8994/17/8/1300
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Recent (2025) survey of vector-field methods for 5-axis machining. Vector-field methods are the conceptual bridge to the stress-aligned AM work in cluster 5.

**[WAAM path planning review]** — Nguyen et al. 2021. A Review of Path Planning for Wire Arc Additive Manufacturing (WAAM). *J. Adv. Manuf. Sys.* https://www.worldscientific.com/doi/10.1142/S0219686721500293
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Review of path-planning techniques specifically for WAAM, where weld bead geometry imposes constraints absent from polymer FDM.

**[Hybrid manufacturing review, 2018]** — Hybrid additive and subtractive manufacturing processes and systems: a review. https://www.researchgate.net/publication/329421387
*Access:* `Author-PDF` (often) | *IP/use:* `Reference-only`
Foundational review of hybrid AM+SM, covering the 5-axis hybrid platforms that are the closest commercial analog to what you are building.

**[Hybrid manufacturing review, 2025]** — A Review of Hybrid Manufacturing: Integrating Subtractive and Additive Manufacturing. *PMC.* https://pmc.ncbi.nlm.nih.gov/articles/PMC12471480/
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Recent open-access review of hybrid manufacturing systems — covers commercial systems, process planning, and case studies.

---

## 2. Foundational multi-axis AM (curved-layer slicing & support-free)

These are the most-cited algorithmic papers in the field. Read all of them.

**[Dai et al., 2018]** — Support-Free Volume Printing by Multi-Axis Motion. *ACM TOG (SIGGRAPH 2018)* 37(4). https://doi.org/10.1145/3197517.3201342
*Access:* `Author-PDF` at https://mewangcl.github.io/pubs/SIG18RobotVolPrint.pdf | *IP/use:* `Algorithm-reusable`
**Anchor paper.** Introduces the volume-to-surfaces-to-curves decomposition strategy: optimize a scalar field over the volume so that its iso-surfaces are convex, support-free, collision-free curved layers. This single paper defines the dominant algorithmic paradigm for the field. Companion code at https://github.com/daichengkai/VoxelMultiAxisAM (`Code-OSS`, license check needed).

**[Zhang et al., 2022]** — S³-Slicer: A General Slicing Framework for Multi-Axis 3D Printing. *ACM TOG (SIGGRAPH Asia 2022)* 41(6). https://doi.org/10.1145/3550454.3555516 (SIGGRAPH Asia 2022 Best Paper)
*Access:* `Author-PDF` via Manchester Research Explorer; project page https://guoxinfang.github.io/S3_Slicer | *IP/use:* `Algorithm-reusable`
Generalization of Dai 2018 that simultaneously optimizes for support-free, strength-reinforcement, and surface-quality objectives via rotation-driven deformation and quaternion fields. **This is currently the state-of-the-art "general" multi-axis slicer.** Code at https://github.com/zhangty019/S3_DeformFDM (`Code-OSS`).

**[Fang et al., 2020]** — Reinforced FDM: Multi-axis filament alignment with controlled anisotropic strength. *ACM TOG (SIGGRAPH Asia 2020)* 39(6). https://doi.org/10.1145/3414685.3417834
*Access:* `Author-PDF` at https://mewangcl.github.io/pubs/SIGAsia2020ReinforcedFDM.pdf | *IP/use:* `Algorithm-reusable`
Multi-axis layer/path generation that aligns filaments along principal stress directions. Reports up to 6.35× load capacity vs planar FDM. Bridges multi-axis slicing with mechanical optimization.

**[Etienne et al., 2019]** — CurviSlicer: Slightly curved slicing for 3-axis printers. *ACM TOG (SIGGRAPH 2019)* 38(4). https://doi.org/10.1145/3306346.3323022
*Access:* `Author-PDF` at https://cims.nyu.edu/gcl/papers/2019-CurviSlicer.pdf | *IP/use:* `Algorithm-reusable`; code `Code-OSS` at https://github.com/mfx-inria/curvislicer
Computes a deformation of the model that, when sliced planarly and then "uncurved" via the inverse deformation, produces gently curved layers on a 3-axis printer. Important conceptual ancestor of S³-Slicer's deformation-based approach. **And the code is open and well-documented** — read this for implementation ideas.

**[Wu et al., 2017]** — RoboFDM: A robotic system for support-free fabrication using FDM. *IEEE ICRA.* https://ieeexplore.ieee.org/document/7989143
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Predecessor to Dai 2018 — uses model decomposition with beam search to find a small set of clipping planes that yield support-free 2.5D sub-volumes. Important historical reference.

**[Wu et al., 2020]** — General Support-Effective Decomposition for Multi-Directional 3-D Printing. *IEEE T-ASE* 17(2). 
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Generalization of RoboFDM for arbitrary models. Useful comparison baseline.

**[Zhang et al., 2023]** — Support generation for robot-assisted 3D printing with curved layers. *IEEE ICRA 2023.*
*Access:* `Paywalled` (author-PDF likely on Manchester repository) | *IP/use:* `Reference-only`; code at https://github.com/zhangty019/Support_Generation_for_Curved_RoboFDM
Companion to S³-Slicer covering the support-structure generation problem when the build layers themselves are curved. Important — supports remain necessary even with curved layers.

**[Yi et al., 2024]** — Neural Slicer for Multi-Axis 3D Printing. *ACM TOG.* https://doi.org/10.1145/3658212 / arXiv 2404.15061
*Access:* `Preprint` (arXiv) + `Paywalled` ACM | *IP/use:* `Algorithm-reusable`
Neural-network-based, representation-agnostic slicer for multi-axis 3D printing. Differentiable pipeline with loss functions for support-free and strength reinforcement. Latest evolution of the Manchester group's work.

**[Xu, Chen, Tang 2019]** — Curved layer based process planning for multi-axis volume printing of freeform parts. *Computer-Aided Design* 114, 51–63. https://doi.org/10.1016/j.cad.2019.05.007
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Curved-layer process planning specifically for volume printing — alternative algorithmic lineage to the Manchester/TU Delft group.

**[Liu et al., 2024 — spherical truss]** — Spherical path planning for multi-axis support-free additive manufacturing of truss structures. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S152661252301112X
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Spherical-slicing approach for truss/lattice structures, where typical curved-layer methods struggle.

**[Li et al., 2025 (Geodesic Distance Field VolDecomp)]** — Geodesic Distance Field-based Curved Layer Volume Decomposition for Multi-Axis Support-free Printing. (Semantic Scholar entry: https://www.semanticscholar.org/paper/46d2374dff6db86ba31403b55e82c3c4ebbe8385)
*Access:* `Paywalled` (likely Author-PDF via authors) | *IP/use:* `Reference-only`
Uses iso-geodesic distance surfaces (IGDS) as printing layers — alternative to scalar-field optimization, leveraging intrinsic geometry of the surface.

**[Wang et al., 2019]** — Research and implementation of a non-supporting 3D printing method based on 5-axis dynamic slice algorithm. *Robotics and Computer-Integrated Manufacturing* 57. 
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Practical 5-axis dynamic slicing — engineering-leaning paper from the Chinese mainstream literature.

**[Coupek et al., 2018]** — Reduction of support structures and building time by optimized path planning algorithms in multi-axis additive manufacturing. *Procedia CIRP.*
*Access:* `OA` (Procedia is typically OA) | *IP/use:* `Cite-and-paraphrase`
Early industry-leaning work on support reduction via multi-axis path planning.

**[Murtezaoglu et al., 2018]** — Five-axis additive manufacturing of freeform models through buildup of transition layers. *Journal of Manufacturing Systems / Robotics & CIM.* https://www.sciencedirect.com/science/article/abs/pii/S0278612518301419
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Designs a 5-axis FDM machine and uses transition layers (variable intra-layer thickness) to print freeform shells — alternative to the curved-layer paradigm.

**[Ahlers et al., 2019]** — 3D Printing of Nonplanar Layers for Smooth Surface Generation. *IEEE CASE 2019.* https://tams.informatik.uni-hamburg.de/publications/2019/case_ahlers_2019.pdf
*Access:* `Author-PDF` | *IP/use:* `Algorithm-reusable`
Open-source extension to Slic3r (3-axis) that detects regions suitable for non-planar printing and generates collision-free toolpaths via a printhead-geometry model. Practical and implementation-oriented — code referenced in paper.

**[Liu et al., 2026 (Multi-Axis DLP)]** — Multi-Axis Additive Manufacturing for Customized Automotive Components. arXiv 2604.12236. https://arxiv.org/html/2604.12236
*Access:* `Preprint` | *IP/use:* `Cite-and-paraphrase`
Recent (2026) work extending the multi-axis curved-slicing paradigm to DLP/SLA, with per-pixel cure-map generation. Shows the curved-layer approach generalizing beyond extrusion.

**[Liu et al., 2025 — FRC curved-layer]** — Curved-Layer Slicing and Continuous Path Planning for Multi-Axis Printing of Fiber-Reinforced Composite Structures. *Processes* 13(2):473. https://www.mdpi.com/2227-9817/13/2/473
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Curved-layer slicing via deformed-space mapping that aligns layers with prescribed fiber-orientation vector fields, plus continuous path planning per layer. Also covers support generation for curved layers.

**[Duarte et al., 2022]** — Curved layer path planning on a 5-axis 3D printer. *Rapid Prototyping Journal* 28(4). https://doi.org/10.1108/RPJ-02-2021-0025
*Access:* `Author-PDF` at https://repositorium.uminho.pt/bitstreams/3ed7e6f9-391d-41f0-a03e-c47c88dfb756/download | *IP/use:* `Cite-and-paraphrase`
Spline-based curved-layer path planning for shell-type objects on a 5-axis printer (rotating + tilting bed). Includes a printer simulator. Less ambitious than the Manchester/TU Delft work but more accessible as a starting point.

**[Feng et al., 2022 — supportless 5-axis]** — Supportless 5-Axis 3D-Printing and Conformal Slicing: A Simulation-based Approach. (Various — see ResearchGate https://www.researchgate.net/publication/370077269)
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Curved-layered material extrusion with conformal-surface offsets and geodesic-distance toolpaths. Implementation on a delta + rotating platform.

**[Isothermal-surface slicing]** — Additive manufacturing of non-planar layers using isothermal surface slicing. *Additive Manufacturing*. https://www.sciencedirect.com/science/article/abs/pii/S1526612522009173
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Generalizes geodesic-distance fields to a "virtual heat transfer" temperature field for slicing. Conceptually elegant alternative to scalar-field optimization.

**[Bhatt et al., 2022 (et seq.)]** — Various papers on robotic AM with neural-network-based deposition trajectory generation; representative reference: cited in Liu et al. comprehensive support-free library, https://www.sciencedirect.com/science/article/abs/pii/S2214860424005542
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Bhatt et al. at USC have published a series of practical papers on robotic AM with closed-loop trajectory compensation — worth tracking that author for engineering depth.

---

## 3. Volume / model decomposition for multi-directional printing

**[Wei et al., 2018 — convex decomposition]** — Skeleton-based convex decomposition of overhang features in multi-directional AM (cited in many subsequent works).
*Access:* `Paywalled` | *IP/use:* `Reference-only`

**[Luo et al., 2014]** — Chopper: Partitioning models into 3D-printable parts. *ACM TOG.* (Foundational beam-search decomposition.)
*Access:* `Paywalled` (Author-PDF likely) | *IP/use:* `Reference-only`
Original beam-search clipping-plane decomposition for 3D printing — predecessor to all multi-directional decomposition work.

**[Dong et al., 2025]** — Support-Free 3D Printing Based on Model Decomposition. *Micromachines* 16(12):1316. https://www.mdpi.com/2072-666X/16/12/1316
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Recent OA paper using Pareto optimization + beam search to find cutting planes minimizing overhang area. Good engineering-level treatment.

**[Wang et al. 2025 — strength-enhanced]** — Strength-enhanced volume decomposition for multi-directional additive manufacturing. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S2214860423001422
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Volume decomposition that considers mechanical strength (not just geometry) when selecting sub-volume directions.

**[Ellipsoidal slicing]** — Volume Decomposition for Multi-axis Support-free and Gouging-free Printing based on Ellipsoidal Slicing. *Computer-Aided Design.* https://www.sciencedirect.com/science/article/abs/pii/S0010448521001469
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Ellipsoidal slicing primitives as an alternative to planar/scalar-field — explicit collision and gouging avoidance during decomposition.

**[Comprehensive support-free library, 2024]** — A comprehensive support-free slicing method library for variable posture additive manufacturing. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S2214860424005542
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Recent work proposing a "library" of slicing methods selected per geometry — useful for understanding the comparative performance of decomposition strategies.

**[Xiao & Joshi]** — Process planning for five-axis support free additive manufacturing. *Procedia Manufacturing / various.* https://www.researchgate.net/publication/344193798
*Access:* `Author-PDF` likely | *IP/use:* `Reference-only`
Penn State group's automated process-planning software for 5-axis AM. Featured in 3DNatives industry coverage.

**[Lee et al.]** — Partitioning algorithm for 3+2-axis metal printing (cited as foundational in ellipsoidal-slicing paper above).
*Access:* `Paywalled` | *IP/use:* `Reference-only`

---

## 4. Tool-path generation on curved surfaces (geodesic, vector-field, iso-* methods)

**[Fang et al., 2024 — high-density spatial fiber]** — Toolpath Generation for High Density Spatial Fiber Printing Guided by Principal Stresses. arXiv 2410.16851. https://arxiv.org/html/2410.16851v1
*Access:* `Preprint` | *IP/use:* `Cite-and-paraphrase`
Uses 2-RoSy direction-field representation + periodic scalar field to generate dense fiber toolpaths aligned with stress directions in 3D space. Latest in the Manchester lineage.

**[Knöppel et al., 2015]** — Stripe Patterns on Surfaces. *ACM TOG.* https://doi.org/10.1145/2766947
*Access:* `Author-PDF` (Discrete Differential Geometry pages) | *IP/use:* `Algorithm-reusable`
Foundational geometry-processing paper — generates evenly-spaced stripe patterns on surfaces from direction fields. The mathematical engine that several multi-axis AM toolpath methods use to convert a vector field into an actual path.

**[Crane et al., 2013]** — Geodesics in Heat: A new approach to computing distance based on heat flow. *ACM TOG.* https://www.cs.cmu.edu/~kmcrane/Projects/HeatMethod/
*Access:* `Author-PDF` | *IP/use:* `Algorithm-reusable`
The "heat method" for fast geodesic distance computation — used as a building block in many multi-axis slicers.

**[Iso-Planar Path Gen, 2002 / 2017]** — Adaptive iso-planar tool path generation for machining of free-form surfaces (Ding et al. 2003, Hu Tang 2017). https://www.sciencedirect.com/science/article/abs/pii/S0010448502000489
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Foundational machining iso-planar work — the ancestor of many AM iso-planar toolpath methods.

**[Iso-Scallop, Suresh & Yang 1994]** — Constant scallop-height machining of free-form surfaces. *J. Eng. Ind.*
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Foundational. Iso-scallop = uniform height of remaining "ridges" between adjacent passes; minimizes path length subject to a quality constraint. Direct AM analog: optimal layer/path spacing for surface quality.

**[Iso-scallop mesh, 2021]** — Iso-scallop tool path planning for triangular mesh surfaces in multi-axis machining. *Robotics & CIM.* https://www.sciencedirect.com/science/article/abs/pii/S0736584521000892
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Iso-scallop on triangle meshes (i.e., on the same kind of input you'll have for AM) for non-spherical tools.

**[Vector-field machining ref above]** — see cluster 1.

**[End-to-end mesh tool-path, 2026]** — End-to-End Tool Path Generation for Triangular Mesh Surfaces in Five-Axis CNC Machining. *Algorithms* 6(3):35. https://www.mdpi.com/2673-9909/6/3/35
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Recent (2026) end-to-end algorithm for 5-axis end-milling toolpath generation on meshes, using geodesic-distance-aware path spacing. Directly relevant — the same kind of pipeline you need for AM.

**[Conformal 3D printing tessellated, 2021]** — Algorithm for the Conformal 3D Printing on Non-Planar Tessellated Surfaces. *Applied Sciences* 11(16):7509. https://www.mdpi.com/2076-3417/11/16/7509
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Mathematical algorithm to project a 2D pattern onto an arbitrary tessellated non-planar surface. Practical, easy-to-implement reference for "given a curved layer, here is its toolpath."

**[Fermat spiral / SFCDecomp]** — Multicriteria Optimized Tool Path Planning in 3D Printing using Space-Filling Curve Based Domain Decomposition. https://www.researchgate.net/publication/354401121
*Access:* `Author-PDF` likely | *IP/use:* `Reference-only`
Continuous Fermat-spiral fills + space-filling-curve decomposition for large 3D-printing problems. Useful for the per-layer infill problem.

**[Hilbert curve infill]** — Path planning for the infill of 3D printed parts utilizing Hilbert curves. https://www.sciencedirect.com/science/article/pii/S235197891830221X
*Access:* `Paywalled` (likely Procedia OA — verify) | *IP/use:* `Reference-only`
Hilbert-curve infill for continuous-motion printing — minimizes idle moves, improves isotropy.

**[Continuous global path planning, multi-branched]** — Adaptive path-planning method based on medial-axis decomposition and transfinite mapping for multi-branched regions (cited in Wang 2024 review).
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Medial-axis decomposition for continuous toolpaths in branching geometries — directly relevant if your parts have branching topology.

**[Wang & Tang, 2007]** — Automatic Generation of Gouge-Free and Angular-Velocity-Compliant Five-Axis Toolpath. *Computer-Aided Design* 39(10), 841–852.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Foundational paper that incorporates the rotary-axis angular-velocity limit *into* the toolpath search instead of post-smoothing. Important for the path-planning ↔ kinematics interface.

---

## 5. Stress-aligned & fiber-reinforced multi-axis printing

**[Fang et al., 2020 — Reinforced FDM]** — see cluster 2.

**[Zhang et al., 2024 — Spatial Fiber Curved Slicing]** — Exceptional Mechanical Performance by Spatial Printing with Continuous Fiber: Curved Slicing, Toolpath Generation and Physical Verification. arXiv 2311.17265. https://arxiv.org/html/2311.17265v2
*Access:* `Preprint` | *IP/use:* `Cite-and-paraphrase`
Curved layers aligned with maximal principal stresses; companion to Reinforced FDM with continuous-fiber experimental validation.

**[Neural co-optimization, 2025]** — Neural Co-Optimization of Structural Topology, Manufacturable Layers, and Path Orientations for Fiber-Reinforced Composites. arXiv 2505.03779. https://arxiv.org/html/2505.03779v1
*Access:* `Preprint` | *IP/use:* `Cite-and-paraphrase`
Joint optimization of topology, curved-layer slicing, and path orientation — uses Hoffman criterion instead of pure principal-stress alignment, allowing more manufacturability flexibility.

**[Self-support TopOpt + curved layers, 2025]** — Self-support structure topology optimization for multi-axis additive manufacturing incorporated with curved layer slicing. *Computer Methods in Applied Mechanics and Engineering* 438. https://www.sciencedirect.com/science/article/abs/pii/S0045782525001136
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Concurrent topology + slicing + sequence optimization. Important if you want to integrate design and manufacturing planning.

**[Stress-oriented path optimization]** — Stress-oriented 3D printing path optimization based on image processing algorithms for reinforced load-bearing parts. https://www.sciencedirect.com/science/article/abs/pii/S0007850621000615
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Image-processing-based generation of stress-aligned paths.

**[Direction-Oriented stress-constrained TopOpt]** — Kundu & Zhang 2021. arXiv 2112.02030. https://arxiv.org/abs/2112.02030
*Access:* `Preprint` | *IP/use:* `Cite-and-paraphrase`
TopOpt of orthotropic materials with explicit raster-angle design — relevant to integrated design+process planning for AM.

**[Looping / load-oriented non-planar paths]** — referenced in the Hilbert curve paper.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Non-planar load-oriented path optimization — direct precursor to multi-axis stress-aligned methods.

---

## 6. Hybrid additive + subtractive manufacturing (5-axis HASM/ASHM)

**[Zhong et al., 2023 — VASCO]** — Volume and Surface Co-Decomposition for Hybrid Manufacturing. *ACM TOG* 42(6). https://doi.org/10.1145/3618324
*Access:* `Author-PDF` https://fanchao98.github.io/VASCO%20page/vasco.html | *IP/use:* `Algorithm-reusable`
Slab-based dynamic-directed graph + beam-guided block decomposition to plan 5-axis hybrid AM/SM sequences with collision-free guarantees. The most important hybrid-planning paper for your use case.

**[5-axis ASHM PB-based, 2025]** — Process research of the powder bed-based 5-axis additive/subtractive hybrid manufacturing for internal features. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S2214860425001769
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Recent (2025) practical 5-axis ASHM system with global toolpath planning + cutter contact accessibility judgment + adaptive layering.

**[TopOpt for HASM, 2024]** — Topology optimization for hybrid additive-subtractive manufacturing incorporating dynamic process planning. *CMAME.* https://www.sciencedirect.com/science/article/abs/pii/S0045782524005267
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Joint topology + 5-axis HASM process planning with dynamic alternation between AM and SM stages.

**[Recursive volume decomposition for HM, 2024]** — Optimal process planning for hybrid additive–subtractive manufacturing using recursive volume decomposition with decision criteria. https://www.sciencedirect.com/science/article/abs/pii/S0278612523002005
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Decision-criteria-driven recursive volume decomposition — automated HM planning.

**[DGTO]** — Derivable Geodesics-coupled Topology Optimization (referenced in the self-support TopOpt paper above) — concurrent design of structure, slices, and AM/SM sequences.
*Access:* `Paywalled` | *IP/use:* `Reference-only`

**[5-axis hybrid DED + milling]** — Five-axis hybrid manufacturing with DED and milling for complex multi-branched metallic parts. https://www.researchgate.net/publication/389225265
*Access:* `Author-PDF` likely | *IP/use:* `Reference-only`
Practical 5-axis DED+milling for branching metallic parts.

**[Chen & Frank, 2019]** — Process planning for hybrid additive and subtractive manufacturing to integrate machining and DED. *Procedia Manufacturing* 34. https://www.researchgate.net/publication/334551543
*Access:* `OA` (Procedia) | *IP/use:* `Cite-and-paraphrase`
Foundational work on integrating machining-style process planning with DED.

**[Hybrid SM-AM, 2020]** — Hybrid subtractive–additive manufacturing processes for high value-added metal components. *IJAMT.* https://link.springer.com/article/10.1007/s00170-020-06099-8
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Industrial-perspective review including 5-axis hybrid operation sequencing.

---

## 7. Wire-arc & DED multi-axis path planning

**[WAAM review]** — see cluster 1.

**[Open-source WAAM software architecture, 2025]** — Open-source software architecture for multi-robot Wire Arc Additive Manufacturing (WAAM). https://www.sciencedirect.com/science/article/pii/S2666496825000020
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
End-to-end OSS architecture for WAAM — slicing, robot motion planning, metrology, in-process sensing, process tuning. Built on Robot Raconteur. Relevant as an architectural reference for an end-to-end 5-axis pipeline.

**[Multi-Robot Scan-n-Print WAAM, 2024]** — arXiv 2411.15915. https://arxiv.org/html/2411.15915v1
*Access:* `Preprint` | *IP/use:* `Cite-and-paraphrase`
Three-robot WAAM with closed-loop height control via laser scanning. Useful for the in-process correction problem.

**[DED-IM, 2024]** — A Novel Method for Mapping and Path Planning in Wire Arc Directed Energy Deposition. *IEEE.* https://ieeexplore.ieee.org/document/10935302/ (code at https://github.com/machipanski/DED-IM, `Code-OSS`)
*Access:* `Paywalled` paper, `Code-OSS` for code | *IP/use:* `Algorithm-reusable`
Image-based segmentation of 3D models for WA-DED path planning. Open code is a plus.

**[WA-DED state of the art]** — The state-of-the-art of wire arc directed energy deposition (WA-DED) for large metallic component manufacture. https://www.tandfonline.com/doi/full/10.1080/0951192X.2022.2162597
*Access:* `OA` (likely) | *IP/use:* `Cite-and-paraphrase`
Recent comprehensive review of WA-DED including process planning.

**[Path optimization for thin-walled WAAM, 2026]** — Path optimization strategies for wire-arc additive manufacturing of thin-walled parts. *IJAMT.* https://link.springer.com/article/10.1007/s00170-026-17736-z
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Recent (2026) treatment of robotic vs gantry trade-offs and path strategies for thin-walled WAAM.

**[DED path planning, 2020]** — Automated Tool-Path Generation for Rapid Manufacturing of AM DED Geometries. *Steel Research International.* https://onlinelibrary.wiley.com/doi/full/10.1002/srin.202000017
*Access:* `OA` (likely) | *IP/use:* `Cite-and-paraphrase`
Zig-zag and contour-parallel automated DED path planning with experimental validation.

**[Innovative DED-Arc path planning, 2025]** — Innovative path planning for arc based DED of multi-featured thin-walled structures. https://www.sciencedirect.com/science/article/abs/pii/S1526612525006681
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Medial axis + active decomposition + curve fitting + Bézier offset for adaptive forming paths. Recent (2025) and engineering-leaning.

**[Multi-direction WAAM slicing]** — Process planning for robotic wire and arc additive manufacturing. *IEEE Conference 2015.* https://ieeexplore.ieee.org/document/7334441/
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Foundational multi-direction slicing with medial-axis-transform (MAT) path planning for WAAM.

---

## 8. Build orientation & part decomposition (3-axis precursors directly relevant)

**[Crispo & Kim 2025]** — Combined topology and build orientation optimization for support structure minimization in additive manufacturing. *SMO* 68:216. https://link.springer.com/article/10.1007/s00158-025-04124-6
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Joint topology + build-orientation optimization. The 3-axis version of the problem you solve with multi-axis flexibility.

**[Cheng & To 2019]** — Part-Scale Build Orientation Optimization for Minimizing Residual Stress and Support Volume for Metal Additive Manufacturing. *Computer-Aided Design* 113. (Author-PDF: https://par.nsf.gov/servlets/purl/10105270)
*Access:* `Author-PDF` | *IP/use:* `Cite-and-paraphrase`
Voxel-based residual-stress-aware orientation optimization for metal AM.

**[Chen et al., 2023]** — Concurrent Build Direction, Part Segmentation, and Topology Optimization for AM Using Neural Networks. *J. Mech. Des.* 145(9). https://doi.org/10.1115/1.4062663
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Neural-network approach to joint segmentation + orientation + topology — methodologically interesting bridge to ML-based planning.

**[Ezair, Massarwi, Elber 2015]** — Orientation analysis of 3D objects toward minimal support volume in 3D-printing. *Computers & Graphics* 51, 117–124.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Foundational paper on orientation-vs-support tradeoff. Cite when motivating multi-axis as a generalization.

**[Pandey et al.]** — Various foundational adaptive-slicing papers (referenced in CurviSlicer).
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Background on layer-thickness adaptation as a degree of freedom orthogonal to (and sometimes combined with) curved layers.

**[Build orientation MADM, 2022]** — Build Orientation Optimization Problem in Additive Manufacturing (multi-attribute decision making). https://www.researchgate.net/publication/326163964
*Access:* `Author-PDF` | *IP/use:* `Reference-only`
Multi-attribute decision-making for orientation selection.

---

## 9. 5-axis CNC machining — tool path generation (transferable to AM)

**[Lasemi review 2010]** — see cluster 1.

**[Hu, Chen, Tang 2017]** — Efficiency-optimal iso-planar tool path generation for five-axis finishing machining of freeform surfaces. *Computer-Aided Design* 83, 33–50.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Efficiency-optimal iso-planar 5-axis paths considering machine kinematic capacities — important methodological reference.

**[Lee 1998]** — Non-isoparametric tool path planning by machining strip evaluation for 5-axis sculptured surface machining. *Computer-Aided Design* 30(7), 559–570.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Foundational paper on machining-strip evaluation. The "strip" concept generalizes nicely to AM (deposition strip width).

**[Morishige et al., 1999]** — Tool path generation using C-space for 5-axis control machining. *J. Manuf. Sci. Eng.* 121.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Configuration-space planning for 5-axis machining — same concept later picked up for AM by Ahlers et al.

**[Castagnetti, Duc, Ray 2008]** — The domain of admissible orientation concept: A new method for five-axis tool path optimisation. *Computer-Aided Design* 40, 938–950.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
"DAO" concept — at each cutter contact point, the set of orientations that satisfy all constraints. Highly relevant to multi-axis AM where you need to choose nozzle orientation per path point.

**[Kim, Elber, Bartoň et al., 2015]** — Precise gouging-free tool orientations for 5-axis CNC machining. *Computer-Aided Design* 58, 220–229.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Algorithmic gouging avoidance — directly transferable to nozzle/printed-layer collision avoidance.

**[Li et al. 2011 — cutter partition]** — Cutter partition-based tool orientation optimization for gouge avoidance in five-axis machining. *Int. J. Mach. Tools Manuf.* (Cited in Tool Orientation Optimization paper above.)
*Access:* `Paywalled` | *IP/use:* `Reference-only`

**[Tool Orientation Optimization, 2020]** — Tool Orientation Optimization and Path Planning for 5-Axis Machining. *J. Sys. Sci. Complexity.* https://link.springer.com/article/10.1007/s11424-020-9270-1
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Comprehensive treatment of tool orientation + CC-point planning for flat-end 5-axis cutters.

**[Mane & Pande 2019]** — Adaptive Tool Path Planning Strategy for 5-Axis CNC Machining of Free Form Surfaces. *ASME MSEC 2019.* https://doi.org/10.1115/MSEC2019-2737
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Curvature-based adaptive iso-parametric strategy — algorithmic ideas transfer to AM.

**[5-axis flank milling spiral bevel]** — Optimal tool path generation and cutter geometry design for five-axis CNC flank milling of spiral bevel gears. https://academic.oup.com/jcde/article/9/5/2024/6713622
*Access:* `OA` (Oxford Academic JCDE — typically OA) | *IP/use:* `Cite-and-paraphrase`
Specialized but conceptually rich treatment of 5-axis envelope/swept-surface methods.

---

## 10. 5-axis CNC machining — kinematics, singularities, postprocessor

**[Sørby 2007]** — Inverse kinematics of five-axis machines near singular configurations. *Robotics and Computer-Integrated Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S0890695506001027
*Access:* `Paywalled` | *IP/use:* `Reference-only`
**Required reading.** Forward and inverse kinematics for 5-axis machines and the singular-configuration problem (rotary axis parallel to tool axis). Same problem appears in 5-axis AM.

**[Affouard et al., 2004]** — Avoiding 5-axis singularities using tool path deformation. *International Journal of Machine Tools & Manufacture.*
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Foundational paper on singularity avoidance via path deformation.

**[Singularities cause/effect/avoidance, 2017]** — Singularities in five-axis machining: Cause, effect and avoidance. *Robotics & CIM.* https://www.sciencedirect.com/science/article/abs/pii/S0890695516306113
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Comprehensive review of 5-axis singularity behaviors and mitigation strategies.

**[Closed-loop IK around singular points, 2023]** — A novel method to minimize the five-axis CNC machining error around singular points based on closed-loop inverse kinematics. *IJAMT.* https://link.springer.com/article/10.1007/s00170-023-11991-0
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Damped Jacobian pseudoinverse for handling singularities.

**[Wan et al., 2018]** — Singularity avoidance for five-axis machine tools through introducing geometrical constraints. *Int. J. Mach. Tools Manuf.* 127.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Geometric-constraint-based singularity avoidance.

**[Liu & Huang 2019]** — Inverse kinematics of a 5-axis hybrid robot with non-singular tool path generation. *Robotics & CIM* 56.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Hybrid-robot kinematics — relevant if your hardware is a delta-style or hexapod-style 5-axis system rather than a serial gantry.

**[Sun, Sun, Lee 2019]** — A gouge-free tool axis reorientation method for kinematics-compliant avoidance of singularity in 5-axis machining. *J. Manuf. Sci. Eng.* 141(5).
*Access:* `Paywalled` | *IP/use:* `Reference-only`

**[Pseudoinverse postprocessor]** — Generalized pseudo inverse kinematics at singularities for developing five-axes CNC machine tool postprocessor.
*Access:* `Author-PDF` likely | *IP/use:* `Reference-only`
Practical postprocessor implementation — read for the engineering details of the IK→G-code translation.

**[Kinematical smoothing rotary axis]** — Grandguillaume, Lavernhe, Tournier. https://hal.science/hal-01223135/document
*Access:* `OA` (HAL) | *IP/use:* `Cite-and-paraphrase`
Smoothing rotary-axis motion near singularities for high-speed milling.

**[Sun et al., 2022 trajectory review]** — Path, feedrate and trajectory planning for free-form surface machining: a state-of-the-art review. *Chinese J. Aeronautics* 35(8), 12–29.
*Access:* `Author-PDF` likely (Chinese J. Aeron. is sometimes OA) | *IP/use:* `Cite-and-paraphrase`
Trajectory planning with feedrate/jerk constraints — necessary reading for the path → motion-control interface.

---

## 11. Hardware & open-source 5-axis printers

**[Hong et al. 2022 — Open5x]** — Open5x: Accessible 5-axis 3D printing and conformal slicing. *ACM CHI 2022 Extended Abstracts.* arXiv 2202.11426. https://arxiv.org/abs/2202.11426
*Access:* `Preprint` (arXiv); ACM is `Paywalled` | *IP/use:* `Cite-and-paraphrase`; hardware/code repo `Code-OSS` (license check)
**Important reference for accessible 5-axis hardware.** Retrofits a Prusa i3 MK3s with a 2-axis rotating gantry, plus a Rhino/Grasshopper-based slicer. Open hardware files and CAD provided.

**[Rep5x]** — GitHub https://github.com/dennisklappe/Rep5x — Open-source 5-axis 3D printer retrofit system for Ender 5 Pro / Ender 3 V3 SE. License: GPL v3.
*Access:* `Code-OSS` (`Code-GPL`) | *IP/use:* `Code-GPL` (vendoring requires GPL-compatible licensing)
Maker-grade retrofit project — useful for hardware ideas but be aware of GPL implications if you reuse code.

**[Generative Machine 5-axis]** — Industry coverage: https://www.fabbaloo.com/news/a-better-way-to-design-a-five-axis-desktop-3d-printer
*Access:* `Industry` | *IP/use:* `Reference-only`
Commercial 5-axis desktop platform with AI-generated structural design. Software is from Aibuild (closed).

**[Fractal Robotics Fractal 5 Pro]** — https://3druck.com/en/diy/fractal-robotics-introduces-open-5-axis-3d-printer-with-slicer-58149101/ + https://hackaday.com/2025/08/04/open-source-5-axis-printer-has-its-own-slicer/
*Access:* `Industry` | *IP/use:* `Reference-only`
Open-design 5-axis printer (Voron-based) with its own Python slicer. Recent (2025).

**[Enomoto Kogyo 5-axis hybrid]** — https://3dprint.com/132475/5-axis-3d-printer-japan/
*Access:* `Industry` | *IP/use:* `Reference-only`
Industry-scale 5-axis hybrid (FDM + milling) using existing 5-axis CNC control.

**[Llewellyn-Jones, Allen, Trask 2016]** — Curved Layer Fused Filament Fabrication Using Automated Tool-Path Generation. *3D Printing and Additive Manufacturing* 3, 236–243.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Early curved-layer FFF on a delta robot — important precursor.

**[Wu, Peng, Guimbretière, Marschner 2016]** — Printing Arbitrary Meshes with a 5DOF Wireframe Printer. *ACM TOG (SIGGRAPH 2016)* 35(4):101.
*Access:* `Paywalled` (Author-PDF likely on Cornell pages) | *IP/use:* `Reference-only`
5-DOF wireframe printer — different paradigm but relevant for multi-axis hardware design considerations.

**[Helm, Willmann, Thoma et al. 2015]** — Iridescence Print: Robotically Printed Lightweight Mesh Structures. *3D Printing and AM* 2(3), 117–122.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
ETH Gramazio-Kohler robotic AM — architecture/large-scale lineage.

**[Open Source 5-Axis Printer Has Its Own Slicer]** — https://hackaday.com/2025/08/04/open-source-5-axis-printer-has-its-own-slicer/
*Access:* `Industry` (blog) | *IP/use:* `Reference-only`
Hackaday coverage of Fractal 5 Pro — useful as a recent overview of state of the open hardware.

---

## 12. Open-source software, slicers, and code repositories

**[S³-Slicer code]** — https://github.com/zhangty019/S3_DeformFDM
*Access:* `Code-OSS` | *IP/use:* check repo LICENSE
**Critical resource.** Reference implementation of the S³-Slicer paper; also includes references to the simpler "S4 Slicer" extension by Joshua Bird.

**[VoxelMultiAxisAM code]** — https://github.com/daichengkai/VoxelMultiAxisAM
*Access:* `Code-OSS` | *IP/use:* check repo LICENSE
Companion code to Dai et al. 2018 SIGGRAPH paper.

**[Support_Generation_for_Curved_RoboFDM code]** — https://github.com/zhangty019/Support_Generation_for_Curved_RoboFDM
*Access:* `Code-OSS` | *IP/use:* check repo LICENSE
Companion to Zhang ICRA 2023 support-generation paper.

**[CurviSlicer code]** — https://github.com/mfx-inria/curvislicer
*Access:* `Code-OSS` | *IP/use:* read LICENSE
Inria's open implementation of the CurviSlicer paper. Production-ish code; uses IceSL as the planar slicer backend. **Most accessible OSS in the field.**

**[FullControl GCode Designer]** — Gleadall 2021. *Additive Manufacturing* 46:102109. https://www.sciencedirect.com/science/article/abs/pii/S2214860421002748 + https://fullcontrol.xyz/
*Access:* `Paywalled` paper, `Code-OSS` for software | *IP/use:* `Code-OSS` (license check) + `Cite-and-paraphrase` for paper
Open-source framework for direct G-code design — bypass STL/slicer pipeline. Useful for prototyping non-planar paths and for the per-segment parameter control.

**[DED-IM code]** — https://github.com/machipanski/DED-IM
*Access:* `Code-OSS` | *IP/use:* check LICENSE

**[Aibuild — geodesic slicing]** — https://www.designforam.com/p/geodesic-slicing-a-generalised-framework
*Access:* `Industry` | *IP/use:* `Reference-only`
Commercial framework using geodesic slicing for multi-axis. Closed-source but conceptually documented.

**[5 Axis Slicer]** — https://www.5-axis-slicer.com/
*Access:* `Industry` (Code-Closed) | *IP/use:* `Reference-only`
Commercial 5-axis slicer.

**[ModuleWorks DED]** — https://www.moduleworks.com/software-components/toolpath/additive/direct-energy-deposition/
*Access:* `Industry` (Code-Closed) | *IP/use:* `Reference-only`
Commercial CAM library widely used as a backend for hybrid systems.

**[PrusaSlicer Arachne perimeter generator]** — Kuipers et al., Ultimaker / Prusa. https://help.prusa3d.com/article/arachne-perimeter-generator_352769
*Access:* `Code-OSS` (PrusaSlicer/Cura are AGPL) | *IP/use:* `Code-GPL/AGPL` for code; algorithm description: Cite the Kuipers paper if used.
Variable-width perimeter generator — relevant 3-axis precedent for adaptive line width that you may want for 5-axis.

**[Slic3r non-planar fork (Ahlers)]** — referenced from cluster 2; check Hamburg TAMS group repos.
*Access:* `Code-OSS` likely | *IP/use:* check LICENSE

**[Non-planar bending GCode (CNC Kitchen)]** — https://www.cnckitchen.com/blog/non-planar-3d-printing-by-bending-g-code (code on the author's GitHub)
*Access:* `Code-OSS` | *IP/use:* check LICENSE
Maker-grade approach: post-processes planar G-code to bend it non-planar. Inspirational and practical.

---

## 13. Patents

⚠️ **Caveat repeated**: I am not a patent lawyer. The flagging below is a starting point for your FTO analysis, not a substitute for legal advice. Verify status (granted vs application, in-force vs expired, jurisdiction) before relying on any of this.

**[US20130189435A1]** — Three-Dimensional Printing System Using Dual Rotation Axes (2013 application). https://patents.google.com/patent/US20130189435A1/en
*Access:* `Patent` | *IP/use:* `Patent-active` (verify current status)
Hardware patent on a dual-rotation-axis 3D printer with turntable. If the application was abandoned the claims may not be enforceable; check Google Patents legal status.

**[EP3117982A1]** — 3D Printing System and Process. https://patents.google.com/patent/EP3117982A1/en
*Access:* `Patent` | *IP/use:* `Patent-active` (verify)
Variable-width nozzle with continuous orientation adjustment — relevant for slicer software that controls extrusion width and nozzle direction.

**[CN106273450A]** — Multi-axis multi-jet 3D printer. https://patents.google.com/patent/CN106273450A/en
*Access:* `Patent` | *IP/use:* `Patent-active` (verify)
Chinese patent on multi-axis printer hardware.

**[US11701813B2]** — Methods for three-dimensionally printing and associated multi-input print heads and systems. https://patents.google.com/patent/US11701813B2/en
*Access:* `Patent` | *IP/use:* `Patent-active`
Multi-axis control over print-head/substrate translation and rotation, including microfluidic mixing nozzles. Recent (2023) US patent — likely still active.

**[US7291002B2]** — Apparatus and methods for 3D printing. https://patents.google.com/patent/US7291002B2/en
*Access:* `Patent` | *IP/use:* `Patent-active` (filed 2003 — likely expired or near expiry; verify)
Continuous radial printing about a rotating build table.

**Search recommendations for additional patents**: Search Google Patents for:
- `"five-axis" OR "5-axis" "additive manufacturing" inassignee:"5AXISMaker"`
- `"multi-axis" "non-planar" slicing`
- `"rotating build platform" 3D printing`
- `"curved layer" deposition path`
- Companies: Stratasys, EOS, GE Aviation, Optomec, Sciaky, Mazak (hybrid), DMG Mori (hybrid), Hybrid Manufacturing Technologies, Aibuild, 5AXISWORKS LTD, Open5x originators (Hong, Imperial College).

---

## 14. Industry / commercial systems

**[Aibuild]** — https://ai-build.com/ — Industry leader in software for large-scale & multi-axis robotic AM. Funder of S³-Slicer (5AXISWORKS).
*Access:* `Industry` | *IP/use:* `Reference-only`

**[ModuleWorks]** — see cluster 12.

**[RAMLAB]** — https://www.ramlab.com/resources/waam-101/ — WAAM systems integrator.
*Access:* `Industry` | *IP/use:* `Reference-only`

**[Sciaky EBAM]** — https://www.sciaky.com/additive-manufacturing/what-is-ded-3d-printing — Industry pioneer in electron-beam DED.
*Access:* `Industry` | *IP/use:* `Reference-only`

**[Mazak / DMG Mori hybrid]** — Major commercial 5-axis hybrid AM/SM machine OEMs. Limited public technical info; reference for benchmarking.
*Access:* `Industry` | *IP/use:* `Reference-only`

**[Phasio]** — https://www.phas.io/post/5-axis-toolpath-optimisation
*Access:* `Industry` | *IP/use:* `Reference-only`
Industry blog overview.

**[Generative Machine + Aibuild collaboration]** — https://ai-build.com/resources/ai-driven-5-axis-desktop-3d-printing/
*Access:* `Industry` | *IP/use:* `Reference-only`
Recent (2025/26) industry collaboration on 5-axis desktop systems.

---

## 15. Theses & dissertations

**[Balasubramaniam, MIT 2001]** — Automatic 5-axis NC toolpath generation. PhD thesis, MIT Mech. Eng. http://hdl.handle.net/1721.1/29225
*Access:* `Thesis` | *IP/use:* `Cite-and-paraphrase`
Foundational MIT thesis on automatic 5-axis toolpath generation under Sanjay Sarma. Machining-side, but the algorithms transfer.

**[Putta, MIT 2010]** — Automatic tool path generation for multi-axis machining. PhD thesis, MIT.
*Access:* `Thesis` | *IP/use:* `Cite-and-paraphrase`
Follow-on to Balasubramaniam.

**[Goh, 2023]** — Point cloud processing and toolpath generation for robotic 3D printing.
*Access:* `Thesis` | *IP/use:* `Cite-and-paraphrase`
Recent thesis on point-cloud-based toolpath generation for robotic AM.

**[Xinyi Xiao, Penn State]** — PhD work on automated 5-axis support-free AM process planning. https://www.3dnatives.com/en/five-axis-additive-manufacturing-140120215/
*Access:* `Thesis` (find via Penn State repository) | *IP/use:* `Cite-and-paraphrase`

**[Brick Geometries / Harvard GSD]** — Architectural thesis on 3 & 5-axis FDM ceramics. https://research.gsd.harvard.edu/maps/2017/03/24/brick-geometries-5-axis-additive-manufacturing-for-architecture/
*Access:* `Thesis` | *IP/use:* `Cite-and-paraphrase`
Architectural-design lineage of 5-axis AM.

**Search hints**: ProQuest Dissertations and Theses, EThOS (UK), HAL (France), DiVA (Sweden) for additional theses. Google Scholar is hit-or-miss for this. Most-relevant supervisors: Charlie C.L. Wang (Manchester), Sanjay Joshi (Penn State), Sylvain Lefebvre (Inria), Sanjay Sarma (MIT), Gershon Elber (Technion), Andy Gleadall (Loughborough), Matthew Frank (Iowa State).

---

## 16. Adjacent: non-planar 3-axis & specialty (concrete, hydrogel, bio)

**[Multi-planar Slicing — Mrazek blog]** — https://blog.honzamrazek.cz/2023/01/multi-planar-slicing-for-3d-printers-for-both-fdm-and-resin/
*Access:* `Industry` (blog) | *IP/use:* `Reference-only`
Conceptually clear walkthrough of multi-planar slicing for both FDM and resin. Good intuition primer.

**[Hackaday non-planar slicer overview]** — https://hackaday.com/2022/04/23/a-universal-non-planar-slicer-for-3d-printing-is-worth-thinking-about/
*Access:* `Industry` (blog) | *IP/use:* `Reference-only`

**[Nonplanar layers shahid, 2024]** — Modeling of non-planar slicer for improved surface quality in material extrusion 3D printing. arXiv 2411.07225.
*Access:* `Preprint` | *IP/use:* `Cite-and-paraphrase`
Combined planar+non-planar slicing for complex objects.

**[Robotic FDM free-form fabrication, 2025]** — Robotic FDM for free-form fabrication: evaluating adaptive non-planar slicing with different contour methods. *Rapid Prototyping Journal.* https://doi.org/10.1108/RPJ-03-2024-0109
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Iso-geodesic slicing for branching geometries on a robotic FDM cell — engineering-leaning recent paper.

**[Concrete 3D printing path planning, 2023]** — Global continuous path planning for 3D concrete printing multi-branched structure. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S221486042300194X
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Adaptive global path planning for branching concrete-printing structures.

**[Concrete 3DCP TSP path planning, 2024]** — A TSP-based continuous path planning for additive manufacturing of concrete. *Progress in Additive Manufacturing.* https://link.springer.com/article/10.1007/s40964-024-00746-2
*Access:* `Paywalled` | *IP/use:* `Reference-only`
TSP-based continuous path generation — algorithmic ideas transfer to other extrusion AM.

**[Large-area concrete pavement path planning]** — https://link.springer.com/article/10.1007/s44223-023-00032-1
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`

**[Non-planar AM with hydrogels review, 2025]** — *npj Soft Matter.* https://www.nature.com/articles/s44431-025-00006-5
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Recent OA review including toolpath strategies for non-planar hydrogel printing.

**[High-Precision Multi-Axis Robotic Bioprinting, 2025]** — *Bioengineering* 12(9):949. https://www.mdpi.com/2306-5354/12/9/949
*Access:* `OA` | *IP/use:* `Cite-and-paraphrase`
Multi-axis robotic bioprinting with conformal paths.

**[Wulle et al., 2022]** — Multi-axis 3D printing of gelatin methacryloyl hydrogels on a non-planar surface obtained from MRI. *Additive Manufacturing* 50:102566.
*Access:* `Paywalled` | *IP/use:* `Reference-only`
Patient-specific conformal multi-axis printing.

**[Conformal AM direct-print, 2019]** — Conformal additive manufacturing using a direct-print process. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S2214860419308048
*Access:* `Paywalled` | *IP/use:* `Reference-only`

**[Iso-Planar dynamic conformal slicing]** — A dynamic slicing algorithm for conformal additive manufacturing. *Additive Manufacturing.* https://www.sciencedirect.com/science/article/abs/pii/S2214860422000306
*Access:* `Paywalled` | *IP/use:* `Reference-only`

---

## "Anchor 10" reading order

If you only have time for ten papers, read these (in this order) before doing anything else:

1. **Lasemi 2010 review** (machining baseline)
2. **Sun 2022 trajectory review** (Chinese J. Aeronautics — modern machining)
3. **Wang 2024 multi-axis 3D printing review** (AM map of the field)
4. **Sørby 2007** (5-axis IK & singularities — required mental model)
5. **Dai et al. 2018 Support-Free Volume Printing** (the AM anchor paper)
6. **Etienne et al. 2019 CurviSlicer** (read code too)
7. **Fang et al. 2020 Reinforced FDM**
8. **Zhang et al. 2022 S³-Slicer** (read code too)
9. **Zhong et al. 2023 VASCO** (hybrid, but the planning method is broader)
10. **Yi et al. 2024 Neural Slicer** (current state of the art)
