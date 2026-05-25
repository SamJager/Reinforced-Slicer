# Overview of the Field — How the Literature Maps Together

This is a narrative complement to `bibliography.md`. The goal is to give you a mental model of the field before you dive into individual papers, and to highlight which sub-questions are well-solved vs. still open.

## The big picture

Multi-axis additive manufacturing — usually 5-axis, sometimes 6-axis robotic — is "the standard 3-axis pipeline plus two more degrees of freedom." Those extra DOFs let you do things that 3-axis can't:

1. **Eliminate or reduce support structures** by tilting the part so that overhangs become vertical.
2. **Reduce or eliminate the staircase effect** by depositing material along curved layers that follow the part's surface.
3. **Align material anisotropy with stress** so printed parts can be much stronger.
4. **Print conformal features** onto an existing curved substrate.
5. **Combine with subtractive operations** in a single setup (hybrid).

The challenge is that the algorithms that supervise a 3-axis printer (uniformly stack horizontal slices) don't generalize naively. You need:

- A way to **slice the part into curved layers** (or non-planar layers, or a sequence of differently-oriented sub-volumes).
- A way to **generate a path on each curved layer** that covers the area, follows desired orientations, avoids self-intersection, and is continuous.
- A way to **orient the nozzle** at every point so it sits on the local surface normal (or some preferred direction) without collision.
- A way to **convert that into machine motion** (XYZ + rotational axes) that is collision-free, smooth, and avoids kinematic singularities.

Almost all of these problems were solved (or studied) for 5-axis CNC machining decades earlier. The AM community has been re-deriving those solutions with AM-specific twists (deposition strip width instead of cutting strip; collision with previously-deposited material instead of with the workpiece holder).

## Two main "schools" of curved-layer slicing

### School 1: Scalar-field optimization (TU Delft / Manchester / Inria)

Pioneered by **Dai et al. 2018 (Support-Free Volume Printing)** and developed through the Manchester group's papers (Wu, Zhang, Fang, Yi, all under Charlie C.L. Wang). The recipe:

1. Define a scalar field `G(x)` over the volume of the part.
2. The iso-surfaces of `G` will be the curved printing layers.
3. Optimize `G` so that its iso-surfaces satisfy your manufacturing objectives: support-free (each iso-surface is supported from below), collision-free (each iso-surface is convex w.r.t. the printer head's accessibility cone), strength-aligned (iso-surface normals follow the principal stress directions), low staircase (iso-surface normals match the part's outer surface normals where applicable).
4. Slice along iso-surfaces of the optimized field; generate per-layer toolpaths; project to robot motion.

The latest in this lineage is **Yi et al. 2024 (Neural Slicer)**, which makes the whole pipeline differentiable and replaces hand-coded objectives with neural-network loss functions.

### School 2: Deformation-based slicing (Inria / Manchester)

Pioneered by **Etienne et al. 2019 (CurviSlicer)** and continued in **Zhang et al. 2022 (S³-Slicer)**. The recipe:

1. Compute a deformation `M` of the model that "unbends" it, so that planar slices of `M(model)` correspond to good curved layers of the original.
2. Slice planarly in the deformed space; map the resulting paths back through `M⁻¹`.

Conceptually this is equivalent to scalar-field optimization (the deformation is essentially defining a scalar field), but it has different implementation tradeoffs — easier to combine with off-the-shelf planar slicers, harder to handle topological complexity. S³-Slicer uses quaternion fields for the rotation part of the deformation, which gives it more expressiveness than CurviSlicer.

### Other approaches

- **Geodesic-based slicing**: iso-geodesic surfaces from a chosen starting surface (e.g., Feng et al., Li et al. geodesic-distance-field decomposition). Aibuild's commercial slicer reportedly uses this approach.
- **Spherical / ellipsoidal slicing**: slicing primitives are spheres or ellipsoids rather than planes, useful for certain topologies (truss structures, parts with spherical accessibility).
- **Multi-directional decomposition (3+2-axis)**: instead of using continuous 5-axis motion, decompose the part into chunks each printed at a fixed orientation, with 3-axis printing within each chunk. Older but still important — Wu/RoboFDM 2017, Dong 2025 model decomposition.

## The path-planning sub-problem

Once you have a curved layer surface, you still need to fill it with toolpath. This problem has direct CNC-machining ancestors:

- **Iso-parametric**: follow the parametric curves of the surface. Easy but uneven coverage on curved surfaces.
- **Iso-planar**: intersect the surface with a stack of parallel planes; use the intersection curves as paths. Robust on triangle meshes.
- **Iso-scallop**: space adjacent paths so the residual "scallop" between them has constant height. Optimal for surface quality.
- **Vector-field-based**: pick a direction field over the surface (e.g., principal stress directions) and trace integral curves of that field as paths.
- **Space-filling curves**: Fermat spirals (SFCDecomp), Hilbert curves — give continuous single-stroke coverage, useful for AM where retract/restart is costly.
- **Medial-axis-based**: especially for thin-walled or branching geometries; Coupek 2018 in AM, DED-IM 2024 in WA-DED.

The vector-field approach is currently the hot one for AM because it directly couples to mechanical objectives (align with stress) and to fiber alignment for composites. The relevant geometry-processing tools are direction-field design (de Goes/Crane, 2-RoSy/4-RoSy fields) and stripe-pattern generation (Knöppel et al. 2015).

## The kinematics sub-problem

Once you have a 3D path with nozzle orientations, you have to convert it to machine motion (X, Y, Z, A, B for a typical 5-axis configuration). This is where the AM literature thins out and you need to read the machining literature directly. Required reading:

- **Sørby 2007** for the math of forward/inverse kinematics and the singular configuration (rotary axis parallel to tool axis).
- **The Singularities review** for the menu of singularity-avoidance strategies (path deformation, geometric constraints, damped pseudoinverse, etc.).
- **Wang & Tang 2007** for incorporating angular-velocity limits into the toolpath search itself, not as a postprocessor.

For AM specifically, S³-Slicer's "Step 6" mentions "singularity-aware motion planning" as a post-step, and there's a corresponding GitHub project. Worth tracking.

## Where the literature is strong vs. weak

### Strong (dozens of papers, multiple competing methods, OSS code available)
- Scalar-field-based curved-layer slicing for support-free fabrication
- Deformation-based curved-layer slicing
- Stress-aligned multi-axis printing for fiber composites
- 5-axis CNC tool path generation (mature field)
- Hybrid AM+SM 5-axis process planning (Zhong VASCO is the standout)

### Moderate (solid handful of papers, room for new contributions)
- Multi-axis path planning for branching / multi-genus topologies
- Collision detection between nozzle assembly and previously-printed material
- Continuous-fiber multi-axis path planning (high-density coverage problem)
- Variable layer thickness in curved-layer settings

### Weak / open (few papers, mostly conceptual or one-off)
- **In-process correction / closed-loop control on 5-axis AM** — Bhatt et al. and the Multi-Robot WAAM paper are early; lots of room
- **Topology-aware path planning** that handles holes, branchings, and high-genus models robustly
- **Slicer-aware machine design** — most slicers assume specific machine kinematics; a general-machine slicer is open
- **Open-source 5-axis slicer for hobbyist hardware** — the Hong/FreddyHong (Open5x) team has explicitly called for this; current OSS options (S³-Slicer, CurviSlicer, FullControl) all have caveats
- **Real-time replanning** for adaptive printing
- **Standardized G-code / toolpath formats** for 5-axis AM (each system uses its own)

## "Anchor 10" reading order — repeated from bibliography.md

1. **Lasemi 2010 review** (machining baseline)
2. **Sun 2022 trajectory review** (Chinese J. Aeronautics — modern machining)
3. **Wang 2024 multi-axis 3D printing review** (AM map of the field)
4. **Sørby 2007** (5-axis IK & singularities — required mental model)
5. **Dai et al. 2018 Support-Free Volume Printing** (the AM anchor paper)
6. **Etienne et al. 2019 CurviSlicer** (read the code too)
7. **Fang et al. 2020 Reinforced FDM**
8. **Zhang et al. 2022 S³-Slicer** (read the code too)
9. **Zhong et al. 2023 VASCO** (hybrid, but the planning method is broader)
10. **Yi et al. 2024 Neural Slicer** (current state of the art)

After those ten, the right next step depends on which sub-problem you're tackling:

- **Slicer architecture** → CurviSlicer code, S³-Slicer code, Open5x slicer code
- **Path-on-surface generation** → Knöppel 2015 (stripe patterns), Crane 2013 (heat method), Iso-scallop machining papers
- **Kinematics / singularities** → Sørby 2007, the Singularities review, Wang & Tang 2007
- **Stress alignment** → Fang 2020, Zhang 2024 spatial fiber, Neural Co-Optimization 2025
- **Hybrid AM+SM** → VASCO and the recent CMAME papers

## Key research groups (people to follow)

- **Charlie C.L. Wang's group** (now at University of Manchester, formerly TU Delft and CUHK) — by a wide margin the most prolific group in algorithmic multi-axis AM. Followers/students: Tianyu Zhang, Guoxin Fang, Chengkai Dai, Chenming Wu, Yuming Huang.
- **Sylvain Lefebvre's group** (Inria, MFX team) — CurviSlicer, IceSL, SLA work.
- **Sanjay Joshi's group** (Penn State) — Xinyi Xiao's process-planning work.
- **Matthew Frank's group** (Iowa State) — hybrid AM+SM process planning.
- **Andy Gleadall** (Loughborough) — FullControl, direct-G-code design.
- **Gershon Elber** (Technion) — accessibility, 5-axis machining geometry.
- **Sanjay Sarma** (MIT) — historical machining/AM work.
- **Lin Lu's group** (Shandong / Peking U) — VASCO and computational fabrication.
- **Aibuild + 5AXISWORKS** — industry sponsors of S³-Slicer; commercial development partner.
