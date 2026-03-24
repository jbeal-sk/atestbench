"""Flexible coordinate format parser.

Frances — Coordinate Format Parser (Phase 6)

Parses latitude/longitude strings in multiple formats and converts
them to standardised decimal degrees:
  • Decimal degrees: ``-74.04798056``, ``40.7144``
  • DMS with degree symbol: ``74° 2'53.73"W``, ``40°42'51.93"N``
  • DMS with colon separator: ``74:02:53.73W``, ``40:42:51.93N``
  • DMS with spaces: ``74 2 53.73 W``, ``40 42 51.93 N``
"""

import re


# ── DMS → decimal ────────────────────────────────────────────────────


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
        Arc-minutes (0–59).
    seconds : float
        Arc-seconds (0–<60).
    direction : str or None
        Compass direction: ``"N"``, ``"S"``, ``"E"``, ``"W"`` or *None*.
        ``"S"`` and ``"W"`` negate the result.

    Returns
    -------
    float
        Decimal degrees.

    Raises
    ------
    ValueError
        If any component is out of range or *direction* is invalid.
    """
    if degrees < 0:
        raise ValueError(f"Degrees must be non-negative, got {degrees}")
    if not (0 <= minutes < 60):
        raise ValueError(f"Minutes must be 0–59, got {minutes}")
    if not (0 <= seconds < 60):
        raise ValueError(f"Seconds must be 0–<60, got {seconds}")

    if direction is not None:
        direction = direction.upper()
        if direction not in ("N", "S", "E", "W"):
            raise ValueError(
                f"Direction must be N, S, E, or W, got '{direction}'"
            )

    decimal = degrees + minutes / 60.0 + seconds / 3600.0

    if direction in ("S", "W"):
        decimal = -decimal

    return decimal


# ── Validation ───────────────────────────────────────────────────────


def validate_parsed_coordinate(value: float, coord_type: str) -> bool:
    """Validate that *value* is within the legal range for *coord_type*.

    Parameters
    ----------
    value : float
        Decimal-degree value.
    coord_type : str
        ``"latitude"`` (±90) or ``"longitude"`` (±180).

    Returns
    -------
    bool
        ``True`` when valid.

    Raises
    ------
    ValueError
        If *value* is out of range or *coord_type* is unrecognised.
    """
    coord_type = coord_type.lower()
    if coord_type == "latitude":
        if not (-90 <= value <= 90):
            raise ValueError(
                f"Latitude must be between -90 and 90, got {value}"
            )
    elif coord_type == "longitude":
        if not (-180 <= value <= 180):
            raise ValueError(
                f"Longitude must be between -180 and 180, got {value}"
            )
    else:
        raise ValueError(
            f"coord_type must be 'latitude' or 'longitude', got '{coord_type}'"
        )
    return True


# ── Main parser ──────────────────────────────────────────────────────

# Regex: DMS with degree/minute/second symbols (°, ', ")
# e.g. 74° 2'53.73"W  or  40°42'51.93"N
_DMS_SYMBOL_RE = re.compile(
    r"^\s*"
    r"(?P<deg>\d+)\s*°\s*"
    r"(?P<min>\d+)\s*[''′]\s*"
    r"(?P<sec>\d+(?:\.\d+)?)\s*[\"″]?\s*"
    r"(?P<dir>[NSEWnsew])?\s*$"
)

# Regex: DMS with colon separators
# e.g. 74:02:53.73W  or  40:42:51.93N
_DMS_COLON_RE = re.compile(
    r"^\s*"
    r"(?P<deg>\d+)\s*:\s*"
    r"(?P<min>\d+)\s*:\s*"
    r"(?P<sec>\d+(?:\.\d+)?)\s*"
    r"(?P<dir>[NSEWnsew])?\s*$"
)

# Regex: DMS with spaces
# e.g. 74 2 53.73 W  or  40 42 51.93 N
_DMS_SPACE_RE = re.compile(
    r"^\s*"
    r"(?P<deg>\d+)\s+"
    r"(?P<min>\d+)\s+"
    r"(?P<sec>\d+(?:\.\d+)?)\s*"
    r"(?P<dir>[NSEWnsew])?\s*$"
)

# Regex: plain decimal degrees (with optional sign)
# e.g. -74.04798056  or  40.71442500
_DECIMAL_RE = re.compile(
    r"^\s*(?P<value>[+-]?\d+(?:\.\d+)?)\s*$"
)


def parse_coordinate(coord_str: str, coord_type: str) -> float:
    """Parse a coordinate string and return decimal degrees.

    Parameters
    ----------
    coord_str : str
        A coordinate in decimal degrees or DMS (symbols / colons / spaces).
    coord_type : str
        ``"latitude"`` or ``"longitude"`` — used for range validation.

    Returns
    -------
    float
        The coordinate in decimal degrees.

    Raises
    ------
    ValueError
        If the format is unrecognised or the value is out of range.
    """
    if not isinstance(coord_str, str) or not coord_str.strip():
        raise ValueError("Coordinate string must be a non-empty string")

    coord_str = coord_str.strip()

    # Try DMS with symbols first
    m = _DMS_SYMBOL_RE.match(coord_str)
    if m:
        value = dms_to_decimal(
            float(m.group("deg")),
            float(m.group("min")),
            float(m.group("sec")),
            m.group("dir"),
        )
        validate_parsed_coordinate(value, coord_type)
        return value

    # Try DMS with colons
    m = _DMS_COLON_RE.match(coord_str)
    if m:
        value = dms_to_decimal(
            float(m.group("deg")),
            float(m.group("min")),
            float(m.group("sec")),
            m.group("dir"),
        )
        validate_parsed_coordinate(value, coord_type)
        return value

    # Try DMS with spaces
    m = _DMS_SPACE_RE.match(coord_str)
    if m:
        value = dms_to_decimal(
            float(m.group("deg")),
            float(m.group("min")),
            float(m.group("sec")),
            m.group("dir"),
        )
        validate_parsed_coordinate(value, coord_type)
        return value

    # Try plain decimal
    m = _DECIMAL_RE.match(coord_str)
    if m:
        value = float(m.group("value"))
        validate_parsed_coordinate(value, coord_type)
        return value

    raise ValueError(
        f"Unrecognised coordinate format: '{coord_str}'. "
        "Accepted formats: decimal degrees (e.g. -74.047980), "
        "DMS with symbols (e.g. 74° 2'53.73\"W), "
        "DMS with colons (e.g. 74:02:53.73W), "
        "DMS with spaces (e.g. 74 2 53.73 W)."
    )
