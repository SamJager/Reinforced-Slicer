"""Surface and tetrahedral mesh utilities.

State of the tet-meshing backend (as of M2b)
--------------------------------------------

The 3D CurviSlicer (M2c) operates on a ``TetMesh`` (see ``tet.py``).
For development and testing we use ``cube_tet_mesh`` — a hand-built
Kuhn-triangulation of an axis-aligned box, MIT-licensed and zero
external dependencies. To mesh an arbitrary STL into tets, you need a
real tet mesher; none of the production-quality Python options ship
under a permissive licence:

* ``tetgen`` (PyPI, by pyvista) — AGPL, would force the slicer to AGPL
  if vendored.
* ``pygalmesh`` — wraps CGAL (GPL/commercial dual).
* ``meshpy.tet`` — wraps tetgen, inherits AGPL.
* ``wildmeshing`` (TetWild / fTetWild bindings, MIT) — the only
  permissive option, but no Windows wheels for Python 3.12 as of
  M2b; building from source is non-trivial.

When we need to mesh real STLs (M2c integration), the plan is to add a
``[tet-tetgen]`` opt-in extra that pulls in the AGPL ``tetgen`` package
and routes through it via subprocess (mere-aggregation argument) so the
core slicer stays MIT. Users who don't install the extra get the
synthetic-mesh path only.
"""
