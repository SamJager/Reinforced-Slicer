# Gaps in this Compilation & Next Steps

## What this compilation does *not* cover well

I want to be honest about the limitations of this compilation. It is substantial but not exhaustive (probably 60–90% of the most relevant work). The biggest specific gaps:

### 1. Chinese-language literature (high-confidence gap)

There is a large body of Chinese-language work on multi-axis AM, particularly from Huazhong University of Science and Technology (HUST), Tsinghua, Shanghai Jiao Tong, Northwestern Polytechnical, and Xi'an Jiaotong. Journals like *Computer Integrated Manufacturing Systems* (《计算机集成制造系统》), *Journal of Mechanical Engineering* (《机械工程学报》), and *China Mechanical Engineering* (《中国机械工程》) publish highly relevant work that does not appear in English search results unless authors also publish in *CAD*, *CAM*, *CIRP Annals*, *J. Manuf. Sys.*, etc. I did not search Chinese databases (CNKI, Wanfang) and I did not search in Chinese.

### 2. Patent corpus (medium-confidence gap)

I included 5 representative patents from Google Patents but didn't do a systematic patent landscape. For a real FTO analysis you would want to search:

- **USPTO** (https://www.uspto.gov/patents/search) for granted US patents
- **Espacenet** (https://worldwide.espacenet.com/) for European and worldwide
- **WIPO PATENTSCOPE** (https://patentscope.wipo.int/) for international applications
- **CNIPA** for Chinese patents

Suggested search-string templates:
- `"five-axis" OR "5-axis" OR "multi-axis" AND ("additive manufacturing" OR "3D printing" OR "fused deposition")`
- `"non-planar" AND ("slicing" OR "tool path" OR "toolpath")`
- `"curved layer" AND ("3D printing" OR "additive")`
- `"rotating build platform" OR "tilting bed" 3D printing`
- `"variable nozzle orientation" AND deposition`

Companies whose patent portfolios are most relevant:
- Stratasys, EOS, GE Aviation, Optomec, Sciaky (DED)
- Mazak, DMG Mori, Hybrid Manufacturing Technologies (hybrid AM/SM)
- Aibuild, 5AXISWORKS (multi-axis software)
- Open5x originators (Imperial College / Hong et al.) — likely no patents, but check
- Shapeways, Carbon, Formlabs (resin-side)

### 3. Standards (low coverage, possibly minor gap)

ASTM F42 / ISO TC 261 standards for AM exist but mostly cover terminology, processes, and qualification — not algorithmic path planning. Worth a quick scan for vocabulary and any normative requirements that affect your software:

- **ISO/ASTM 52900** — terminology
- **ISO/ASTM 52910** — design for AM
- **ISO/ASTM 52915** — AMF file format
- **ISO/ASTM 52941** — qualification of LPBF systems
- The 3MF Consortium specs (https://3mf.io/) for the 3MF file format, which is the modern replacement for STL and the format that would carry orientation/curved-layer metadata to a multi-axis slicer.

### 4. Commercial software documentation (low coverage)

Beyond what I cited, the following commercial tools have public documentation worth skimming:

- **Autodesk Netfabb** (build prep, has DED toolpath support)
- **Materialise Magics** (file repair, build prep)
- **Siemens NX AM** (5-axis hybrid CAM)
- **Hexagon (formerly Vero) Edgecam / VISI** (5-axis CAM with AM modules)
- **PowerMill Additive** (5-axis DED)
- **AdaOne** (large-scale robotic AM)

Most are closed-source but their technical whitepapers and feature lists are useful as benchmarks for what your slicer should do.

### 5. Specific topics I touched lightly

- **Closed-loop / in-process correction** — the multi-robot WAAM paper and Bhatt et al. are starts; this is an active and underexplored area.
- **Layer adhesion and inter-layer mechanics in curved-layer printing** — there are physical-experimental papers (separate from algorithmic ones) on how curved layers actually bond. I didn't search hard for these.
- **Multi-material 5-axis** — hinted at in some papers (Reinforced FDM uses dual-material) but a fuller search is warranted if your project is multi-material.
- **Resin-based 5-axis** (DLP/SLA on rotating platforms) — covered in the Liu 2026 multi-axis DLP paper but is a small subliterature.
- **Powder-bed-based 5-axis** — mostly impractical due to powder-bed physics, but some hybrid PBF systems exist (cluster 6).

## Suggested next searches

For each of the gaps above, here are specific searches I'd run if continuing this work:

1. **CNKI** (with translation): "五轴 增材制造 路径规划" (5-axis additive manufacturing path planning)
2. **Google Scholar advanced search** with "Cited by" forward search from each of the Anchor 10 papers — particularly Dai 2018 (likely 200+ citations now) and S³-Slicer.
3. **Semantic Scholar API** to get clean author-citation graphs around the Manchester/Inria groups.
4. **arXiv `cs.GR` and `eess.SY`** for recent preprints (within last 6 months) on slicing/path planning.
5. **dblp.org** for Charlie C.L. Wang, Sylvain Lefebvre, Gershon Elber publication lists.
6. **ProQuest Dissertations and Theses** with subject terms "additive manufacturing" + "five-axis" or "multi-axis."
7. **EThOS** (https://bl.uk/ethos) for UK theses (Manchester, Loughborough, Imperial — all centers of activity).

## Reference managers / how to ingest this

I'd recommend importing `bibliography.csv` into one of:

- **Zotero** (free, OSS) — has a CSV import and tagging system that maps cleanly to my access/IP tags
- **Mendeley** — has CSV import; reference management + PDF library
- **Notion / Obsidian** — if you want the bibliography to live alongside your project notes; both ingest CSV/markdown
- **JabRef** (free, OSS, BibTeX-native) — good if you want to write LaTeX papers eventually

A workflow that I'd suggest:

1. Import `bibliography.csv` into Zotero, mapping:
   - `cluster` → Tag
   - `access_tag` → Tag
   - `ip_use_tag` → Tag
   - `relevance_one_liner` → Notes field
   - `doi_or_url` → URL/DOI
2. Use Zotero's built-in PDF retriever / unpaywall integration to grab open-access PDFs automatically. About 25–30% of the entries will come back with PDFs straight away.
3. For the paywalled ones with `Author-PDF` tag, manually visit the cited URL (usually an author's GitHub.io or institutional page) to get the PDF.
4. For paywalled-only entries, use your institutional library or interlibrary loan.
5. Tag entries you've actually read with a "read" tag, and entries you've cited with "cited."

## Updating this compilation

If you re-run a search in 6 months, the highest-value targets to refresh are:

- Charlie C.L. Wang's group's publication page at Manchester — they publish 4–8 multi-axis AM papers per year
- arXiv cs.GR + cs.CG + eess.SY filtered by the keywords above
- *Additive Manufacturing*, *Computer-Aided Design*, *ACM TOG*, *J. Manuf. Sys.*, *Robotics and CIM* table-of-contents alerts
- Aibuild's blog and engineering pages — often previews new academic-industrial collaborations

## A concrete suggestion for project organization

Based on this literature, if I were starting a 5-axis AM slicer project, I'd structure my work as:

1. **Reproduce CurviSlicer** end-to-end on your hardware. Even though it's 3-axis, the codebase is the most accessible entry into deformation-based slicing and you'll learn the algorithmic primitives. License: check repo, but it's research-grade OSS.
2. **Reproduce a single Dai-2018-style scalar-field slicing example** on a simple part using S³-Slicer's code. Now you understand both schools.
3. **Implement a basic 5-axis postprocessor** using Sørby's IK formulas. Test with a simple known toolpath. Now you have machine motion that respects singularities.
4. **Pick one capability** to build from there — support-free, stress-aligned, or hybrid AM/SM — and read the corresponding sub-literature in depth.

This roadmap lines up with the literature: the field has converged on "compute a curved-layer field, then plan paths on it, then convert to machine motion," and the open questions are about which field to compute, which path topology to use, and how to handle the kinematics-AM coupling cleanly.
