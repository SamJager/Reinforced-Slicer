"""Regression tests for the 2D zigzag fill primitive.

Originally we relied on the planar-slicer test (which uses 45°/135°
defaults) to cover ``zigzag_fill``. That hid a rotation-convention bug
at axis-aligned angles (0°/90°) where ``angle=90`` produced *no*
segments because the polygon and the scan-line frame were rotated in
opposite directions. M2c.4 caught it because the curved pipeline
alternates between 0° and 90°. These tests pin down both axis-aligned
angles directly so the bug can't sneak back in.
"""

from __future__ import annotations

import numpy as np
import pytest
from shapely.geometry import Polygon

from reinforced_slicer.pathing.zigzag import zigzag_fill


def _unit_square() -> Polygon:
    return Polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])


def _bbox(pts: np.ndarray) -> tuple[float, float, float, float]:
    return float(pts[:, 0].min()), float(pts[:, 0].max()), float(pts[:, 1].min()), float(pts[:, 1].max())


@pytest.mark.parametrize("angle", [0.0, 45.0, 90.0, 135.0, 180.0, 270.0])
def test_zigzag_produces_paths_at_all_angles(angle: float) -> None:
    paths = zigzag_fill(_unit_square(), spacing=0.2, angle_deg=angle)
    assert paths, f"angle={angle} produced no paths"
    pts = np.vstack(paths)
    assert len(pts) > 5


def test_zigzag_at_zero_is_horizontal_stripes() -> None:
    paths = zigzag_fill(_unit_square(), spacing=0.25, angle_deg=0.0)
    pts = np.vstack(paths)
    x_min, x_max, y_min, y_max = _bbox(pts)
    # Should span the full x extent at multiple distinct y values.
    assert x_min == pytest.approx(0.0, abs=1e-6)
    assert x_max == pytest.approx(1.0, abs=1e-6)
    unique_y = sorted({round(float(y), 6) for y in pts[:, 1]})
    assert len(unique_y) >= 4


def test_zigzag_at_ninety_is_vertical_stripes() -> None:
    paths = zigzag_fill(_unit_square(), spacing=0.25, angle_deg=90.0)
    pts = np.vstack(paths)
    x_min, x_max, y_min, y_max = _bbox(pts)
    assert y_min == pytest.approx(0.0, abs=1e-6)
    assert y_max == pytest.approx(1.0, abs=1e-6)
    unique_x = sorted({round(float(x), 6) for x in pts[:, 0]})
    assert len(unique_x) >= 4


def test_zigzag_returns_points_inside_polygon() -> None:
    poly = _unit_square()
    for angle in (0.0, 30.0, 90.0, 150.0):
        paths = zigzag_fill(poly, spacing=0.2, angle_deg=angle)
        for path in paths:
            x_min, x_max, y_min, y_max = _bbox(path)
            assert x_min >= -1e-6
            assert x_max <= 1.0 + 1e-6
            assert y_min >= -1e-6
            assert y_max <= 1.0 + 1e-6


def test_finer_spacing_means_more_scan_lines() -> None:
    coarse = zigzag_fill(_unit_square(), spacing=0.4, angle_deg=0.0)
    fine = zigzag_fill(_unit_square(), spacing=0.1, angle_deg=0.0)
    assert sum(len(p) for p in fine) > 2 * sum(len(p) for p in coarse)
