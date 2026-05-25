# AGENTS.md — Orientation for Claude Code / Codex

This project is a literature corpus for building a **5-axis additive manufacturing slicer and path planner**, with emphasis on **continuous fiber reinforcement (CFRTP)**. This file tells an automated agent how to use the corpus *without* reading every PDF.

---

## What to read, in what order

For most questions you only need **`KNOWLEDGE.md`** and **`SOFTWARE_INDEX.md`** in this directory. They are designed to be self-contained.

```
1. AGENTS.md          ← you are here. Orientation only.
2. KNOWLEDGE.md       ← consolidated technical reference. Read this first.
3. SOFTWARE_INDEX.md  ← every tool/library/repo with license, language, fit.
─────────────────────── (rest are source material, fall back to these only when needed)
4. overview.md            narrative companion to KNOWLEDGE.md (human-authored)
5. bibliography.md        long-form annotated bibliography (135 entries)
6. bibliography.csv       same as a spreadsheet
7. gaps_and_next_steps.md what's *not* in the corpus
8. README.md              project metadata, tag system
9. *.pdf                  primary sources. 32 papers/patents/theses.
                          Filenames are not always descriptive — see the
                          "PDF filename → paper" table in KNOWLEDGE.md.
```

**Default behavior:** answer from `KNOWLEDGE.md` and `SOFTWARE_INDEX.md`. Only consult the bibliography/PDFs when the agent needs a primary-source quote, a specific equation, or details those two files explicitly say they don't include.

---

## Vocabulary glossary (so agent queries match the corpus)

The corpus uses several near-synonyms. Treat them as equivalent unless context says otherwise:

| Preferred term | Synonyms in corpus | Meaning |
|---|---|---|
| **multi-axis AM / MAAM** | 5-axis 3D printing, 6-DOF printing, 5-DOF printing | AM with ≥4 mechanical DOFs |
| **curved-layer slicing** | conformal slicing, non-planar slicing, spatial slicing | layers that aren't horizontal planes |
| **non-planar** | curved-layer, slightly-curved (3-axis), conformal | umbrella term for "not a stack of horizontal planes" |
| **support-free** | SF, supportless | objective: eliminate sacrificial supports |
| **strength reinforcement** | SR, stress-aligned, principal-stress alignment | objective: align material w/ stress |
| **surface quality** | SQ, anti-staircase | objective: smooth outer surface |
| **LPD** | local printing direction, build direction | per-element nozzle/deposit orientation |
| **CFRTP / CFRTPC** | continuous carbon fiber, CCF, continuous fiber composite | continuous-fiber AM polymer composite |
| **CFRP** | continuous fiber reinforced polymer | same family, sometimes thermoset |
| **iso-surface / iso-curve** | level set, iso-value contour | extracted from a scalar field |
| **scalar-field slicing** | G-field method, Dai 2018 paradigm | optimize G(x), slice along iso-surfaces |
| **deformation-based slicing** | mapping-based, CurviSlicer/S³-Slicer paradigm | warp the model, planar-slice, unwarp |
| **3+2-axis** | multi-directional, decomposition-based | print chunks at fixed orientations |
| **CC point** | cutter contact point (machining), printer contact point (AM) | where the tool touches the surface |
| **DAO** | domain of admissible orientation | feasible-orientation set at a CC point |
| **WAAM** | wire-arc AM | metal AM with welding torch + wire feed |
| **DED** | directed energy deposition | metal AM with focused energy + powder/wire |
| **FFF / FDM** | fused filament fabrication, fused deposition modeling | thermoplastic extrusion AM |
| **MAAM** | multi-axis additive manufacturing | superset including 5-axis FDM, robot-arm WAAM, etc. |

---

## How to answer common questions

### "What's the state of the art for X?"

Look up X in `KNOWLEDGE.md` → "Topics index" at the top. The relevant section will name the SOTA paper(s) and tell you the **algorithmic paradigm** (scalar-field vs. deformation vs. decomposition vs. geodesic) and its **trade-offs**.

### "What software / repo should I use for X?"

Open `SOFTWARE_INDEX.md`. It is sorted by use case ("if you want curved-layer slicing on 3-axis hardware…", "if you want stress-aligned multi-axis…"). Every entry has license, language, status, and known caveats.

### "What does paper Y say?"

`bibliography.md` has a 1–3 sentence summary per paper. If you need more, the PDFs are local — but check the "PDF filename → paper" table in `KNOWLEDGE.md` § 1, because filenames like `3550454_3555516.pdf` are ACM DOIs, not titles.

### "Has anyone done Z?"

If `KNOWLEDGE.md` § "Strong / Moderate / Weak coverage" calls Z out as **strong** or **moderate**, the answer is yes — paper names will be in the relevant section. If it's listed as **weak / open**, treat that as "no known mature work" rather than "definitely no work" — see `gaps_and_next_steps.md` for caveats (Chinese-language gap, patent corpus, etc.).

### "Can I implement / use this?"

Three independent questions:

1. **Algorithmic re-use** — algorithms aren't copyrighted. A re-implementation in your own words is fine even from a paywalled paper. See `README.md` "IP tags."
2. **Code re-use** — depends on the license. `SOFTWARE_INDEX.md` flags each repo. GPL/AGPL repos (Rep5x, PrusaSlicer) propagate; MIT/BSD/Apache are permissive; research-code without a license is "ask the author."
3. **Patent freedom-to-operate** — `KNOWLEDGE.md` § 11 lists the patents in the corpus. These are *examples not a complete FTO sweep*. Treat as starting point, not legal advice.

---

## Conventions used in KNOWLEDGE.md and SOFTWARE_INDEX.md

- **Confidence markers**: `[verified]` = directly from the paper text; `[implied]` = my inference from context; `[uncertain]` = needs primary-source check.
- **Citation format**: `[FirstAuthor Year]` or `[ShortName]` matching the bibliography. Full citations are in `bibliography.md`.
- **Code refs**: a code repo will always have a URL and license tag in `SOFTWARE_INDEX.md`. KNOWLEDGE.md just names it.
- **Equations**: rendered inline with LaTeX-style notation (`$x^2$`). Where the corpus PDFs have specific equations worth quoting, KNOWLEDGE.md says so and points to the paper page.
- **"the Manchester group"** = Charlie C.L. Wang's group at the University of Manchester (formerly TU Delft / CUHK). They are by far the most prolific group in this field; >40% of the cited algorithmic AM papers come from them.

---

## Things to *not* assume

- **"5-axis" is overloaded.** In machining it means RRTTT (3 translations + 2 rotations of either tool or table). In AM it can also mean 5-DOF wire printing, 6-DOF robot arm with constrained motion, gantry + rotating bed, etc. The kinematics matter; don't assume them.
- **"Slicer" is overloaded.** Sometimes means just curved-layer generation; sometimes the whole STL → G-code pipeline; sometimes (for S³-Slicer) the deformation framework plus layers plus path generation.
- **Knowledge cutoff:** this corpus was assembled around April 2026. Refresh against the literature for anything published after that — Manchester alone publishes 4–8 multi-axis AM papers per year.
- **Aibuild closed-source.** Aibuild's commercial products (S³-Slicer's industry funder) use **geodesic** slicing — *not* the deformation-based S³-Slicer framework they sponsor academically. The two should not be conflated.
- **WAAM ≠ FDM.** Algorithms transfer at the level of curved-layer slicing and path planning, but bead-shape physics, thermal management, and re-melt zones are very different. Be careful applying FDM-derived rules (e.g., overhang angles) to WAAM and vice versa.
