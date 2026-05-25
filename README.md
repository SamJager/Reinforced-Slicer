# 5-Axis Path Planning & Slicing Literature Compilation

Compiled by Claude on 2026-04-22 for a 5-axis additive manufacturing slicer/path-planner project.

## Project scope

The deliverable target is a **5-axis additive manufacturing** slicer/path-planning system. Because much of the algorithmic foundation for 5-axis path generation comes from CNC machining, this bibliography deliberately includes machining literature alongside AM literature. The ideas to transfer from machining → AM include: cutter contact (CC) point planning, tool orientation optimization, scallop-height and iso-* path topologies, kinematic singularity handling, postprocessor design, and collision/gouging avoidance.

## Files

- **`README.md`** — this file. Explains the schema, the tagging system, and the topic clusters.
- **`bibliography.md`** — the main annotated bibliography, grouped by topic cluster. Each entry has full citation, an access tag, an IP/use tag, and a 1–3 sentence relevance note.
- **`bibliography.csv`** — the same data as a spreadsheet so you can sort, filter, or import into a reference manager.
- **`overview.md`** — a short narrative overview of the field that maps the bibliography to research themes and identifies the “must-read” entry points.
- **`gaps_and_next_steps.md`** — what this compilation does *not* cover well, plus suggested next searches and reference managers.

## Tagging system

Two orthogonal tags per entry: an **access tag** (can I read it?) and an **IP/use tag** (can I borrow algorithms or code?).

### Access tags

| Tag | Meaning |
|---|---|
| `OA` | Open access journal article — free to read, usually CC-licensed for reuse with attribution |
| `Preprint` | arXiv / engrXiv / HAL / institutional preprint — free to read, license varies (often author-retained) |
| `Author-PDF` | Paywalled venue, but author-hosted PDF exists on a personal/lab/repository page |
| `Paywalled` | Behind a journal/publisher paywall; abstract is free |
| `Thesis` | Master's or PhD thesis from a university repository — usually free to read |
| `Industry` | Vendor whitepaper, industry blog, trade press — free to read, marketing-tinted |
| `Patent` | Granted patent or published application — free to read on Google Patents / Espacenet, but legally protected IP |
| `Standard` | Published standard (ISO/ASTM etc.) — usually paid |
| `Code-OSS` | Open-source code repository — license noted in entry |
| `Code-Closed` | Commercial software, no source available |

### IP / use tags

| Tag | Meaning |
|---|---|
| `Reference-only` | Cite the idea, do not copy text/figures/code |
| `Cite-and-paraphrase` | OA or preprint — safe to discuss in detail with citation; do not reproduce figures/text without checking the license |
| `Algorithm-reusable` | The paper describes an algorithm at a level you could re-implement freely; only the *expression* (their text/figures/code) is protected |
| `Code-MIT` / `Code-GPL` / `Code-Apache` / `Code-BSD` / `Code-Proprietary` | Source code is available under the named license — read the LICENSE file before vendoring |
| `Patent-active` | Granted patent that may still be in force (US patents typically last 20 years from filing). **Implementing the claims commercially could infringe.** Get legal advice for any product. |
| `Patent-expired-or-application` | Either expired (free to practice) or only an application (not yet enforceable). Still verify before relying. |

A note on patents: I've flagged anything that looks like it could plausibly read on a 5-axis-AM slicer/path-planner. **Patent claims are interpreted by lawyers, not by Claude.** Before shipping a commercial product, get a freedom-to-operate (FTO) opinion from a patent attorney in your jurisdiction. For research or open-source work, the risk profile is much lower but still nonzero.

A note on algorithms vs. expression (US/EU IP basics, not legal advice): In most jurisdictions, **algorithms and ideas are not copyrightable** — only the specific *expression* (the paper's text, the figures, the source code) is. So if a paper is paywalled, you can still re-implement its algorithm from a description in your own words. What you cannot do is copy the paper's text, figures, or pseudocode verbatim. Patents are the exception: a patented algorithm/method is protected as a *method* regardless of how you express it.

## Topic clusters used in `bibliography.md`

1. **Reviews & surveys** — start here for a fast overview
2. **Foundational multi-axis AM (curved-layer slicing & support-free)** — the core algorithmic literature
3. **Volume / model decomposition for multi-directional printing**
4. **Tool-path generation on curved surfaces (geodesic, vector-field, iso-* methods)**
5. **Stress-aligned & fiber-reinforced multi-axis printing**
6. **Hybrid additive + subtractive manufacturing (5-axis HASM/ASHM)**
7. **Wire-arc & DED multi-axis path planning**
8. **Build orientation & part decomposition (3-axis precursors directly relevant)**
9. **5-axis CNC machining — tool path generation (transferable to AM)**
10. **5-axis CNC machining — kinematics, singularities, postprocessor**
11. **Hardware & open-source 5-axis printers**
12. **Open-source software, slicers, and code repositories**
13. **Patents**
14. **Industry / commercial systems**
15. **Theses & dissertations**
16. **Adjacent: non-planar 3-axis & specialty (concrete, hydrogel, bio)**

## How exhaustive is this?

This compilation is **substantial but not exhaustive**. It covers an estimated 60–90% of the most-cited and most-relevant works as of early 2026. To reach true exhaustiveness you would want to:

1. Run systematic searches on Scopus, Web of Science, and IEEE Xplore using strings like `(("five-axis" OR "5-axis" OR "multi-axis") AND ("additive manufacturing" OR "3D printing") AND ("path planning" OR "slicing" OR "tool path"))`.
2. Snowball forward and backward citations from the four most-cited "anchor" papers: Dai et al. 2018 (Support-Free Volume Printing), Etienne et al. 2019 (CurviSlicer), Fang et al. 2020 (Reinforced FDM), and Zhang et al. 2022 (S³-Slicer).
3. Add Chinese-language literature — there is a large body of work in journals like *Computer Integrated Manufacturing Systems* and from Chinese universities (Huazhong UST, Tsinghua, SJTU) that I did not search for in Chinese.
4. Add USPTO / Espacenet / WIPO patent searches — Google Patents only covers a fraction.

See `gaps_and_next_steps.md` for more.
