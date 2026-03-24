"""Tests for affine_transform module (Betty — Affine Transform Engine)."""

import math

import numpy as np
import pytest

from affine_transform import (
    build_affine_transform,
    compute_fourth_corner,
    geo_to_page,
    is_within_bounds,
)


# ── compute_fourth_corner ────────────────────────────────────────────


class TestComputeFourthCorner:
    """Tests for compute_fourth_corner."""

    def test_missing_br(self):
        """TL=(1,1), TR=(1,3), BL=(3,1) → BR should be (3,3)."""
        corners = {"TL": (1, 1), "TR": (1, 3), "BL": (3, 1)}
        result = compute_fourth_corner(corners, "BR")
        assert result == pytest.approx((3, 3))

    def test_missing_tl(self):
        """TR=(1,3), BL=(3,1), BR=(3,3) → TL should be (1,1)."""
        corners = {"TR": (1, 3), "BL": (3, 1), "BR": (3, 3)}
        result = compute_fourth_corner(corners, "TL")
        assert result == pytest.approx((1, 1))

    def test_missing_tr(self):
        """TL=(1,1), BL=(3,1), BR=(3,3) → TR should be (1,3)."""
        corners = {"TL": (1, 1), "BL": (3, 1), "BR": (3, 3)}
        result = compute_fourth_corner(corners, "TR")
        assert result == pytest.approx((1, 3))

    def test_missing_bl(self):
        """TL=(1,1), TR=(1,3), BR=(3,3) → BL should be (3,1)."""
        corners = {"TL": (1, 1), "TR": (1, 3), "BR": (3, 3)}
        result = compute_fourth_corner(corners, "BL")
        assert result == pytest.approx((3, 1))

    def test_non_rectangular_parallelogram(self):
        """Non-rectangular parallelogram: skewed corners."""
        # TL=(0,0), TR=(1,3), BL=(2,1), missing BR → (3,4)
        corners = {"TL": (0, 0), "TR": (1, 3), "BL": (2, 1)}
        result = compute_fourth_corner(corners, "BR")
        assert result == pytest.approx((3, 4))

    def test_floating_point_corners(self):
        """Floating-point coordinates are handled correctly."""
        corners = {
            "TL": (40.712776, -74.005974),
            "TR": (40.712776, -73.935242),
            "BL": (40.660, -74.005974),
        }
        result = compute_fourth_corner(corners, "BR")
        assert result == pytest.approx((40.660, -73.935242))

    def test_invalid_missing_key(self):
        """Invalid missing key raises ValueError."""
        corners = {"TL": (1, 1), "TR": (1, 3), "BL": (3, 1)}
        with pytest.raises(ValueError, match="missing must be one of"):
            compute_fourth_corner(corners, "XX")

    def test_wrong_corner_keys(self):
        """Wrong set of corner keys raises ValueError."""
        corners = {"TL": (1, 1), "TR": (1, 3)}
        with pytest.raises(ValueError, match="corners must contain exactly"):
            compute_fourth_corner(corners, "BR")


# ── build_affine_transform ───────────────────────────────────────────


class TestBuildAffineTransform:
    """Tests for build_affine_transform."""

    def test_simple_rectangle_mapping(self):
        """Known rectangle maps corners back to page points with < 0.01 error."""
        geo = [(0, 0), (0, 100), (100, 0)]
        page = [(0, 0), (500, 0), (0, 800)]

        matrix = build_affine_transform(geo, page)

        for g, p in zip(geo, page):
            result = geo_to_page(g[0], g[1], matrix)
            assert result[0] == pytest.approx(p[0], abs=0.01)
            assert result[1] == pytest.approx(p[1], abs=0.01)

    def test_round_trip_accuracy(self):
        """Transform geo→page has < 0.01 error for all input points."""
        geo = [(40.0, -74.0), (40.0, -73.0), (41.0, -74.0)]
        page = [(72.0, 720.0), (612.0, 720.0), (72.0, 72.0)]

        matrix = build_affine_transform(geo, page)

        for g, p in zip(geo, page):
            result = geo_to_page(g[0], g[1], matrix)
            assert result[0] == pytest.approx(p[0], abs=0.01)
            assert result[1] == pytest.approx(p[1], abs=0.01)

    def test_four_points_overdetermined(self):
        """4 consistent points still produce a valid transform."""
        geo = [(0, 0), (0, 10), (10, 0), (10, 10)]
        page = [(0, 0), (100, 0), (0, 200), (100, 200)]

        matrix = build_affine_transform(geo, page)

        result = geo_to_page(5, 5, matrix)
        assert result[0] == pytest.approx(50.0, abs=0.01)
        assert result[1] == pytest.approx(100.0, abs=0.01)

    def test_collinear_points_raises(self):
        """Collinear geographic points raise ValueError."""
        geo = [(0, 0), (1, 1), (2, 2)]
        page = [(0, 0), (100, 100), (200, 200)]

        with pytest.raises(ValueError, match="collinear"):
            build_affine_transform(geo, page)

    def test_fewer_than_3_points_raises(self):
        """Fewer than 3 point pairs raise ValueError."""
        with pytest.raises(ValueError, match="At least 3"):
            build_affine_transform([(0, 0), (1, 1)], [(0, 0), (1, 1)])

    def test_mismatched_lengths_raises(self):
        """Mismatched list lengths raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            build_affine_transform([(0, 0), (1, 1), (2, 2)], [(0, 0)])

    def test_returns_2x3_array(self):
        """Result is a 2×3 numpy array."""
        geo = [(0, 0), (0, 1), (1, 0)]
        page = [(0, 0), (10, 0), (0, 20)]
        matrix = build_affine_transform(geo, page)
        assert matrix.shape == (2, 3)


# ── geo_to_page ──────────────────────────────────────────────────────


class TestGeoToPage:
    """Tests for geo_to_page."""

    def test_identity_like_transform(self):
        """A hand-crafted affine matrix produces expected output."""
        # x = 1*lon + 0*lat + 0  →  x = lon
        # y = 0*lon + 1*lat + 0  →  y = lat
        matrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        assert geo_to_page(50.0, 30.0, matrix) == pytest.approx((30.0, 50.0))

    def test_translation_only(self):
        """Pure translation: x = lon+10, y = lat+20."""
        matrix = np.array([[1.0, 0.0, 10.0], [0.0, 1.0, 20.0]])
        assert geo_to_page(5.0, 3.0, matrix) == pytest.approx((13.0, 25.0))

    def test_returns_floats(self):
        """Result tuple contains native Python floats."""
        matrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        result = geo_to_page(1.0, 2.0, matrix)
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)


# ── is_within_bounds ─────────────────────────────────────────────────


class TestIsWithinBounds:
    """Tests for is_within_bounds."""

    @pytest.fixture()
    def rectangle_corners(self):
        """A simple axis-aligned rectangle in order (CW)."""
        return [(0, 0), (0, 10), (10, 10), (10, 0)]

    def test_center_inside(self, rectangle_corners):
        """Center of rectangle is inside."""
        assert is_within_bounds(5, 5, rectangle_corners) is True

    def test_outside_point(self, rectangle_corners):
        """Point clearly outside is not within bounds."""
        assert is_within_bounds(20, 20, rectangle_corners) is False

    def test_outside_negative(self, rectangle_corners):
        """Point in negative space is not within bounds."""
        assert is_within_bounds(-5, -5, rectangle_corners) is False

    def test_on_edge(self, rectangle_corners):
        """Point on the edge is treated as inside."""
        assert is_within_bounds(0, 5, rectangle_corners) is True

    def test_on_corner(self, rectangle_corners):
        """Point on a corner is treated as inside."""
        assert is_within_bounds(0, 0, rectangle_corners) is True

    def test_ccw_winding(self):
        """Works correctly with counter-clockwise ordering too."""
        ccw_corners = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert is_within_bounds(5, 5, ccw_corners) is True
        assert is_within_bounds(15, 15, ccw_corners) is False

    def test_non_rectangular_quad(self):
        """Works for a non-rectangular convex quadrilateral."""
        corners = [(0, 2), (2, 5), (5, 3), (3, 0)]
        # Centroid should be inside
        cx = sum(c[0] for c in corners) / 4
        cy = sum(c[1] for c in corners) / 4
        assert is_within_bounds(cx, cy, corners) is True
        # Far away point is outside
        assert is_within_bounds(100, 100, corners) is False

    def test_wrong_number_of_corners(self):
        """Fewer or more than 4 corners raise ValueError."""
        with pytest.raises(ValueError, match="exactly 4"):
            is_within_bounds(0, 0, [(0, 0), (1, 1), (2, 2)])
