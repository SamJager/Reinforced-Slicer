"""M2b: tet mesh primitives — volumes, gradients, cube constructor."""

from __future__ import annotations

import numpy as np
import pytest

from reinforced_slicer.mesh.tet import (
    TetMesh,
    bottom_face_indices,
    cube_tet_mesh,
    grid_vertex_index,
    tet_gradient,
    tet_volume,
    top_face_indices,
)


class TestTetVolume:
    def test_unit_tet_has_one_sixth_volume(self) -> None:
        v = tet_volume(
            np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
        )
        assert v == pytest.approx(1.0 / 6.0)

    def test_volume_is_orientation_invariant(self) -> None:
        p0 = np.array([0.0, 0, 0])
        p1 = np.array([2.0, 0, 0])
        p2 = np.array([0.0, 3, 0])
        p3 = np.array([0.0, 0, 4])
        expected = 2.0 * 3.0 * 4.0 / 6.0
        assert tet_volume(p0, p1, p2, p3) == pytest.approx(expected)
        # Swap two vertices -> sign flips, abs value the same.
        assert tet_volume(p0, p2, p1, p3) == pytest.approx(expected)


class TestTetGradient:
    def test_gradient_round_trips_linear_field(self) -> None:
        # Take a known linear field f(x,y,z) = ax + by + cz + d, sample at
        # tet vertices, reconstruct gradient via tet_gradient — must
        # recover (a, b, c).
        p = [
            np.array([0.0, 0, 0]),
            np.array([1.0, 0, 0]),
            np.array([0.0, 1, 0]),
            np.array([0.0, 0, 1]),
        ]
        a, b, c, d = 2.0, -3.0, 5.0, 7.0
        values = np.array([a * pi[0] + b * pi[1] + c * pi[2] + d for pi in p])
        grad_op = tet_gradient(*p)
        recovered = grad_op @ values
        assert recovered == pytest.approx([a, b, c])

    def test_gradient_columns_sum_to_zero(self) -> None:
        # Sum of barycentric-coordinate gradients is identically zero
        # (Σ λ_i = 1, so ∇Σ = 0).
        rng = np.random.default_rng(0)
        p = [rng.standard_normal(3) for _ in range(4)]
        grad_op = tet_gradient(*p)
        assert grad_op.sum(axis=1) == pytest.approx(np.zeros(3), abs=1e-12)

    def test_degenerate_tet_rejected(self) -> None:
        # Four coplanar vertices -> zero volume -> grad undefined.
        with pytest.raises(ValueError, match="degenerate"):
            tet_gradient(
                np.array([0.0, 0, 0]),
                np.array([1.0, 0, 0]),
                np.array([0.0, 1, 0]),
                np.array([1.0, 1, 0]),
            )


class TestCubeTetMesh:
    def test_single_cell_has_six_tets_summing_to_unit_volume(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=1)
        assert mesh.n_tets == 6
        assert mesh.n_vertices == 8
        total = sum(
            tet_volume(*[mesh.vertices[v] for v in tet]) for tet in mesh.tets
        )
        assert total == pytest.approx(1.0)

    @pytest.mark.parametrize("s", [1, 2, 3, 4])
    def test_subdivided_cube_volume_is_preserved(self, s: int) -> None:
        mesh = cube_tet_mesh(extent=2.0, subdivisions=s)
        assert mesh.n_tets == 6 * s**3
        assert mesh.n_vertices == (s + 1) ** 3
        total = sum(
            tet_volume(*[mesh.vertices[v] for v in tet]) for tet in mesh.tets
        )
        assert total == pytest.approx(2.0**3)

    def test_top_and_bottom_face_indices_match_z_coords(self) -> None:
        mesh = cube_tet_mesh(extent=5.0, subdivisions=3)
        top = top_face_indices(3)
        bottom = bottom_face_indices(3)
        assert np.all(mesh.vertices[top, 2] == pytest.approx(5.0))
        assert np.all(mesh.vertices[bottom, 2] == pytest.approx(0.0))
        # Top and bottom are disjoint and have the right size.
        assert np.intersect1d(top, bottom).size == 0
        assert len(top) == 16
        assert len(bottom) == 16

    def test_grid_vertex_index_is_consistent(self) -> None:
        s = 4
        mesh = cube_tet_mesh(extent=1.0, subdivisions=s)
        step = 1.0 / s
        for i in range(s + 1):
            for j in range(s + 1):
                for k in range(s + 1):
                    idx = grid_vertex_index(i, j, k, s)
                    assert mesh.vertices[idx] == pytest.approx(
                        [i * step, j * step, k * step]
                    )

    def test_displaced_only_moves_in_z(self) -> None:
        mesh = cube_tet_mesh(extent=1.0, subdivisions=2)
        dz = np.linspace(-0.1, 0.1, mesh.n_vertices)
        out = mesh.displaced(dz)
        assert np.all(out.vertices[:, 0] == mesh.vertices[:, 0])
        assert np.all(out.vertices[:, 1] == mesh.vertices[:, 1])
        assert np.all(out.vertices[:, 2] == pytest.approx(mesh.vertices[:, 2] + dz))


class TestValidation:
    def test_wrong_shape_vertices_rejected(self) -> None:
        with pytest.raises(ValueError, match="shape"):
            TetMesh(vertices=np.zeros((5, 2)), tets=np.zeros((1, 4), dtype=int))

    def test_wrong_shape_tets_rejected(self) -> None:
        with pytest.raises(ValueError, match="shape"):
            TetMesh(vertices=np.zeros((5, 3)), tets=np.zeros((1, 3), dtype=int))

    def test_out_of_range_tet_index_rejected(self) -> None:
        with pytest.raises(ValueError, match="out of range"):
            TetMesh(vertices=np.zeros((3, 3)), tets=np.array([[0, 1, 2, 9]]))
