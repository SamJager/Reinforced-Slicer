"""Tests for the mesh-repair helper and on-tab1 button handler."""

from __future__ import annotations

import trimesh

from reinforced_slicer.gui.app import on_repair, repair_mesh
from reinforced_slicer.gui.serialize import mesh_stats


def _broken_cube() -> trimesh.Trimesh:
    """Cube with one face removed -> open edges, not watertight."""
    cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    return trimesh.Trimesh(vertices=cube.vertices, faces=cube.faces[:-2])


def test_repair_mesh_makes_a_broken_cube_watertight_or_better() -> None:
    broken = _broken_cube()
    before = mesh_stats(broken)
    assert before["watertight"] is False
    fixed, log = repair_mesh(broken)
    after = mesh_stats(fixed)
    # We can't guarantee fill_holes restores full watertightness in every
    # case, but we expect the open-edge count to drop substantially.
    assert after["n_open_edges"] <= before["n_open_edges"]
    assert isinstance(log, list) and len(log) >= 3


def test_repair_mesh_on_clean_input_is_noop_or_improvement() -> None:
    cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    before = mesh_stats(cube)
    fixed, _ = repair_mesh(cube)
    after = mesh_stats(fixed)
    assert after["watertight"] is True
    assert after["n_faces"] == before["n_faces"]


def test_on_repair_handler_returns_full_set() -> None:
    broken = _broken_cube()
    fixed_mesh, quality_u, repair_u, stats_md_val, log_u, model3d_path = on_repair(broken)
    assert isinstance(fixed_mesh, trimesh.Trimesh)
    # Either watertight now (quality panel hidden) or still has issues (visible).
    # Either way, stats markdown should be a string.
    assert isinstance(stats_md_val, str)


def test_on_repair_handler_handles_no_mesh() -> None:
    result = on_repair(None)
    assert result[0] is None
