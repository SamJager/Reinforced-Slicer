"""M2c.2: marching tets / iso-surface extraction tests.

Property coverage:

* Flat field (f(p) = z): iso-surfaces should be horizontal planes.
* Tilted field (f(p) = z + a·x): iso-surfaces should be tilted planes
  with the right slope.
* Vertex normals point in the +∇f direction.
* Layered extraction returns one iso-surface per layer height with
  correct spacing.
* Empty cases (level outside field range) return an empty IsoSurface
  without crashing.
"""

from __future__ import annotations

import numpy as np
import pytest

from reinforced_slicer.mesh.isosurface import extract_curved_layers, extract_isosurface
from reinforced_slicer.mesh.tet import cube_tet_mesh


def _z_field(mesh) -> np.ndarray:
    return mesh.vertices[:, 2].astype(float)


def _tilted_field(mesh, slope_x: float) -> np.ndarray:
    return (mesh.vertices[:, 2] + slope_x * mesh.vertices[:, 0]).astype(float)


class TestPlanarIsoSurface:
    def test_flat_field_gives_horizontal_plane(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=4)
        field = _z_field(mesh)
        iso = extract_isosurface(mesh, field, level=0.5)

        assert not iso.is_empty()
        assert iso.vertices[:, 2] == pytest.approx(0.5, abs=1e-10)
        # All normals should point in +z.
        assert iso.normals[:, 2] == pytest.approx(1.0, abs=1e-6)

    @pytest.mark.parametrize("level", [0.25, 0.5, 0.75])
    def test_planar_slice_covers_unit_square_area(self, level: float) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=4)
        field = _z_field(mesh)
        iso = extract_isosurface(mesh, field, level=level)

        total_area = 0.0
        for tri in iso.triangles:
            p0, p1, p2 = iso.vertices[tri]
            total_area += 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0))
        assert total_area == pytest.approx(1.0, abs=1e-6)


class TestTiltedIsoSurface:
    def test_tilted_field_gives_tilted_plane(self) -> None:
        # f(p) = z + 0.3 x -> iso at f=c is z = c - 0.3 x, a plane with
        # slope dz/dx = -0.3.
        mesh = cube_tet_mesh(extent=1.0, subdivisions=4)
        slope = 0.3
        field = _tilted_field(mesh, slope_x=slope)
        iso = extract_isosurface(mesh, field, level=0.5)

        # Verify all iso-vertices satisfy z + 0.3 x = 0.5.
        residuals = iso.vertices[:, 2] + slope * iso.vertices[:, 0] - 0.5
        assert np.max(np.abs(residuals)) < 1e-10

        # Normal direction should match grad(f) / |grad(f)| = (slope, 0, 1) / norm.
        expected_normal = np.array([slope, 0.0, 1.0]) / np.sqrt(1.0 + slope**2)
        for n in iso.normals:
            assert n == pytest.approx(expected_normal, abs=1e-6)


class TestLayeredExtraction:
    def test_uniform_layer_heights(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=3)
        field = _z_field(mesh)  # f ranges [0, 1]
        layers = extract_curved_layers(mesh, field, layer_height=0.25)
        # f_min=0, f_max=1, start=0.125 -> levels [0.125, 0.375, 0.625, 0.875]
        assert len(layers) == 4
        z_values = sorted({float(iso.vertices[0, 2]) for iso in layers if not iso.is_empty()})
        assert z_values == pytest.approx([0.125, 0.375, 0.625, 0.875], abs=1e-10)

    def test_explicit_levels_override_defaults(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        field = _z_field(mesh)
        layers = extract_curved_layers(
            mesh, field, layer_height=0.25, levels=np.array([0.1, 0.9])
        )
        assert len(layers) == 2
        assert all(not iso.is_empty() for iso in layers)


class TestEdgeCases:
    def test_level_below_field_returns_empty(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        field = _z_field(mesh)
        iso = extract_isosurface(mesh, field, level=-0.5)
        assert iso.is_empty()

    def test_level_above_field_returns_empty(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        field = _z_field(mesh)
        iso = extract_isosurface(mesh, field, level=10.0)
        assert iso.is_empty()

    def test_wrong_field_shape_rejected(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=1)
        with pytest.raises(ValueError, match="shape"):
            extract_isosurface(mesh, np.zeros(4), level=0.5)


class TestVertexNormalsAreUnit:
    def test_normals_are_unit(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=3)
        field = _tilted_field(mesh, slope_x=0.3)
        iso = extract_isosurface(mesh, field, level=0.5)
        norms = np.linalg.norm(iso.normals, axis=1)
        assert norms == pytest.approx(np.ones(len(norms)), abs=1e-8)
