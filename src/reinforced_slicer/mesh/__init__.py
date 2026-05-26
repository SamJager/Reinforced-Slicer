"""Surface and tetrahedral mesh utilities.

Tet meshing backend
-------------------

The 3D CurviSlicer (M2c) operates on a ``TetMesh`` (see ``tet.py``).
``tetmesh_backends.tetrahedralize_surface`` dispatches to whichever
backend is installed:

* **gmsh** (LGPL) — the real mesher. Installed via the ``[tet]`` extra
  (``pip install reinforced-slicer[tet]``). gmsh is a separate Python
  wheel that we dynamically link to, so the LGPL stays compartmental:
  this project remains MIT, and users can swap gmsh out for any other
  LGPL-compatible mesher.
* **shoebox** (always available) — Kuhn-triangulation of the input's
  AABB. Wrong for non-box parts but useful as a development fallback
  and for stress-testing the slicer's behaviour on synthetic geometry.

Backends we considered but didn't adopt:

* ``tetgen`` (PyPI, by pyvista) — AGPL; rules itself out for shipping
  with an MIT slicer.
* ``pygalmesh`` — wraps CGAL (GPL).
* ``meshpy.tet`` — wraps tetgen, inherits AGPL.
* ``wildmeshing`` (TetWild / fTetWild, MIT) — the most attractive
  pure-permissive option, but no Windows wheels for Python 3.12 at the
  time of writing. Worth revisiting later.
"""

from reinforced_slicer.mesh.isosurface import (
    IsoSurface,
    extract_curved_layers,
    extract_isosurface,
)
from reinforced_slicer.mesh.tetmesh_backends import (
    TetMeshResult,
    available_backends,
    tetrahedralize_surface,
)

__all__ = [
    "IsoSurface",
    "TetMeshResult",
    "available_backends",
    "extract_curved_layers",
    "extract_isosurface",
    "tetrahedralize_surface",
]
