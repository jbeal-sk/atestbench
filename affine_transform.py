"""Affine Transform Engine — geographic ↔ document coordinate mapping.

Provides functions to:
- Compute the 4th corner of a parallelogram from 3 known corners
- Build an affine transformation matrix from geo/page point pairs
- Transform geographic coordinates to page coordinates
- Test whether a point lies within a quadrilateral boundary
"""

import numpy as np


def compute_fourth_corner(corners: dict, missing: str) -> tuple[float, float]:
    """Compute the missing corner of a parallelogram from 3 known corners.

    Uses the parallelogram diagonal-bisection property: D = A + C - B,
    where B is the corner diagonally opposite D.

    Args:
        corners: Dict with 3 of 4 keys ("TL", "TR", "BL", "BR"), each
                 mapping to a (lat, lon) tuple.
        missing: The key that is absent ("TL", "TR", "BL", or "BR").

    Returns:
        (lat, lon) of the missing corner.

    Raises:
        ValueError: If ``missing`` is not one of the four valid keys, if
            ``corners`` does not contain exactly the other three keys, or
            if ``missing`` is already present in ``corners``.
    """
    valid_keys = {"TL", "TR", "BL", "BR"}

    if missing not in valid_keys:
        raise ValueError(
            f"missing must be one of {valid_keys}, got '{missing}'"
        )

    expected = valid_keys - {missing}
    if set(corners.keys()) != expected:
        raise ValueError(
            f"corners must contain exactly {expected}, got {set(corners.keys())}"
        )

    # Diagonal pairs: each missing corner's diagonal opposite
    diagonal_opposites = {
        "TL": "BR",
        "TR": "BL",
        "BL": "TR",
        "BR": "TL",
    }

    # B is the diagonal opposite of the missing corner
    b_key = diagonal_opposites[missing]
    # A and C are the two remaining corners (adjacent to the missing one)
    adjacent = expected - {b_key}
    a_key, c_key = sorted(adjacent)  # deterministic order

    a_lat, a_lon = corners[a_key]
    b_lat, b_lon = corners[b_key]
    c_lat, c_lon = corners[c_key]

    d_lat = a_lat + c_lat - b_lat
    d_lon = a_lon + c_lon - b_lon

    return (d_lat, d_lon)


def build_affine_transform(
    geo_points: list[tuple], page_points: list[tuple]
) -> np.ndarray:
    """Build a 2×3 affine matrix mapping geographic to page coordinates.

    Solves the system:
        x_page = a·lon + b·lat + c
        y_page = d·lon + e·lat + f

    from 3 (or more) point correspondences.

    Args:
        geo_points:  List of (lat, lon) tuples in geographic space.
        page_points: List of (x_page, y_page) tuples in document space,
                     corresponding 1-to-1 with *geo_points*.

    Returns:
        A 2×3 numpy array ``[[a, b, c], [d, e, f]]``.

    Raises:
        ValueError: If fewer than 3 point pairs are given, if the lists
            differ in length, or if the geographic points are collinear
            (degenerate system).
    """
    if len(geo_points) != len(page_points):
        raise ValueError(
            "geo_points and page_points must have the same length"
        )
    if len(geo_points) < 3:
        raise ValueError("At least 3 point pairs are required")

    # Build the coefficient matrix A and result vectors bx, by.
    # Each row of A is [lon, lat, 1].
    n = len(geo_points)
    A = np.zeros((n, 3))
    bx = np.zeros(n)
    by = np.zeros(n)

    for i, (geo, page) in enumerate(zip(geo_points, page_points)):
        lat, lon = geo
        x_page, y_page = page
        A[i] = [lon, lat, 1.0]
        bx[i] = x_page
        by[i] = y_page

    if n == 3:
        # Exact system — use np.linalg.solve
        det = np.linalg.det(A)
        if abs(det) < 1e-10:
            raise ValueError(
                "Geographic points are collinear; cannot build affine transform"
            )
        coeffs_x = np.linalg.solve(A, bx)
        coeffs_y = np.linalg.solve(A, by)
    else:
        # Over-determined system — use least-squares
        coeffs_x, res_x, rank_x, _ = np.linalg.lstsq(A, bx, rcond=None)
        coeffs_y, res_y, rank_y, _ = np.linalg.lstsq(A, by, rcond=None)
        if rank_x < 3 or rank_y < 3:
            raise ValueError(
                "Geographic points are collinear; cannot build affine transform"
            )

    return np.array([coeffs_x, coeffs_y])


def geo_to_page(
    lat: float, lon: float, affine_matrix: np.ndarray
) -> tuple[float, float]:
    """Transform a geographic point to page coordinates.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        affine_matrix: A 2×3 numpy array as returned by
            :func:`build_affine_transform`.

    Returns:
        (x_page, y_page) in document coordinates.
    """
    v = np.array([lon, lat, 1.0])
    result = affine_matrix @ v
    return (float(result[0]), float(result[1]))


def is_within_bounds(
    lat: float, lon: float, corners: list[tuple]
) -> bool:
    """Test whether a point lies inside a convex quadrilateral.

    Uses the cross-product winding method: a point is inside a convex
    polygon if and only if the cross products of consecutive edge vectors
    with the vector to the test point all share the same sign.

    Args:
        lat: Latitude of the test point.
        lon: Longitude of the test point.
        corners: Four (lat, lon) tuples defining the quadrilateral.
                 Must be in order (either clockwise or counter-clockwise).

    Returns:
        True if (lat, lon) is inside or on the boundary of the
        quadrilateral, False otherwise.
    """
    if len(corners) != 4:
        raise ValueError("corners must contain exactly 4 points")

    n = len(corners)
    point = (lat, lon)

    signs = []
    for i in range(n):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % n]

        # Cross product of edge vector with vector to the test point
        cross = (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)

        if abs(cross) > 1e-10:
            signs.append(cross > 0)

    # If all cross products are empty (degenerate polygon), treat as inside
    if not signs:
        return True

    # Point is inside if all cross products share the same sign
    return all(signs) or not any(signs)
