"""Flexible coordinate format parser.

Accepts decimal degrees and degrees-minutes-seconds (DMS) input and converts
all values to standardised decimal degrees.
"""

import re


def dms_to_decimal(
    degrees: float,
    minutes: float,
    seconds: float,
    direction: str | None = None,
) -> float:
    """Convert degrees-minutes-seconds to decimal degrees.

    Parameters
    ----------
    degrees : float
        Whole degrees (non-negative).
    minutes : float
        Arc-minutes, 0–59.
    seconds : float
        Arc-seconds, 0–59.999…
    direction : str or None
        Compass direction: ``"N"``, ``"S"``, ``"E"``, ``"W"`` or ``None``.
        ``"S"`` and ``"W"`` negate the result.

    Returns
    -------
    float
        Decimal degrees.

    Raises
    ------
    ValueError
        If *minutes* or *seconds* are out of range, or *direction* is invalid.
    """
    if minutes < 0 or minutes >= 60:
        raise ValueError(
            f"Minutes must be >= 0 and < 60, got {minutes}"
        )
    if seconds < 0 or seconds >= 60:
        raise ValueError(
            f"Seconds must be >= 0 and < 60, got {seconds}"
        )
    if direction is not None and direction.upper() not in ("N", "S", "E", "W"):
        raise ValueError(
            f"Direction must be N, S, E, or W, got '{direction}'"
        )

    decimal = abs(degrees) + minutes / 60 + seconds / 3600

    if direction is not None and direction.upper() in ("S", "W"):
        decimal = -decimal
    elif degrees < 0:
        decimal = -decimal

    return decimal


# Regex patterns for DMS formats
# Matches: 74° 2'53.73"W  or  40°42'51.93"N  (degree symbol variant)
_DMS_SYMBOL_RE = re.compile(
    r"""^\s*
    (-?\d+)\s*[°]\s*                  # integer degrees with ° symbol
    (\d+(?:\.\d+)?)\s*[''′]\s*       # minutes with ' or ′
    (\d+(?:\.\d+)?)\s*["″"]\s*      # seconds with " or ″
    ([NSEWnsew])?\s*$                 # optional direction
    """,
    re.VERBOSE,
)

# Matches: 74:02:53.73W  (colon-separated)
_DMS_COLON_RE = re.compile(
    r"""^\s*
    (-?\d+)\s*:\s*                    # integer degrees
    (\d+(?:\.\d+)?)\s*:\s*            # minutes
    (\d+(?:\.\d+)?)\s*                # seconds
    ([NSEWnsew])?\s*$                 # optional direction
    """,
    re.VERBOSE,
)

# Matches: 74 2 53.73 W  (space-separated)
_DMS_SPACE_RE = re.compile(
    r"""^\s*
    (-?\d+)\s+                        # integer degrees
    (\d+(?:\.\d+)?)\s+                # minutes
    (\d+(?:\.\d+)?)\s*                # seconds
    ([NSEWnsew])?\s*$                 # optional direction
    """,
    re.VERBOSE,
)

# Matches plain decimal: -74.04798056  or  40.7144
_DECIMAL_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*$"
)


def parse_coordinate(coord_str: str, coord_type: str) -> float:
    """Parse a coordinate string and return decimal degrees.

    Parameters
    ----------
    coord_str : str
        Coordinate in decimal degrees or DMS format.
    coord_type : str
        ``"latitude"`` or ``"longitude"``.

    Returns
    -------
    float
        Decimal degrees.

    Raises
    ------
    ValueError
        If the string cannot be parsed or the result is out of range.
    """
    if coord_type not in ("latitude", "longitude"):
        raise ValueError(
            f"coord_type must be 'latitude' or 'longitude', got '{coord_type}'"
        )

    coord_str = coord_str.strip()
    if not coord_str:
        raise ValueError("Coordinate string is empty")

    # Try plain decimal first
    m = _DECIMAL_RE.match(coord_str)
    if m:
        value = float(m.group(1))
        validate_parsed_coordinate(value, coord_type)
        return value

    # Try DMS with degree symbol
    m = _DMS_SYMBOL_RE.match(coord_str)
    if m:
        deg, mins, secs, direction = _extract_dms_groups(m)
        value = dms_to_decimal(deg, mins, secs, direction)
        validate_parsed_coordinate(value, coord_type)
        return value

    # Try DMS with colon separator
    m = _DMS_COLON_RE.match(coord_str)
    if m:
        deg, mins, secs, direction = _extract_dms_groups(m)
        value = dms_to_decimal(deg, mins, secs, direction)
        validate_parsed_coordinate(value, coord_type)
        return value

    # Try DMS with space separator
    m = _DMS_SPACE_RE.match(coord_str)
    if m:
        deg, mins, secs, direction = _extract_dms_groups(m)
        value = dms_to_decimal(deg, mins, secs, direction)
        validate_parsed_coordinate(value, coord_type)
        return value

    raise ValueError(
        f"Unable to parse coordinate: '{coord_str}'. "
        f"Accepted formats: decimal degrees (e.g. -74.047980), "
        f"DMS with symbols (e.g. 74°2'53.73\"W), "
        f"DMS with colons (e.g. 74:02:53.73W), "
        f"DMS with spaces (e.g. 74 2 53.73 W)."
    )


def _extract_dms_groups(
    match: re.Match,
) -> tuple[float, float, float, str | None]:
    """Pull numeric groups and optional direction from a regex match."""
    deg = float(match.group(1))
    mins = float(match.group(2))
    secs = float(match.group(3))
    direction = match.group(4).upper() if match.group(4) else None
    return deg, mins, secs, direction


def validate_parsed_coordinate(value: float, coord_type: str) -> bool:
    """Validate that *value* is within the allowed range for *coord_type*.

    Parameters
    ----------
    value : float
        Decimal-degree value to check.
    coord_type : str
        ``"latitude"`` (±90) or ``"longitude"`` (±180).

    Returns
    -------
    bool
        ``True`` when valid.

    Raises
    ------
    ValueError
        If *value* is out of range.
    """
    if coord_type == "latitude":
        if value < -90 or value > 90:
            raise ValueError(
                f"Latitude must be between -90 and 90, got {value}"
            )
    elif coord_type == "longitude":
        if value < -180 or value > 180:
            raise ValueError(
                f"Longitude must be between -180 and 180, got {value}"
            )
    else:
        raise ValueError(
            f"coord_type must be 'latitude' or 'longitude', got '{coord_type}'"
        )
    return True
