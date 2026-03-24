"""Tests for coordinate_parser module (Frances — Coordinate Format Parser)."""

import pytest

from coordinate_parser import dms_to_decimal, parse_coordinate, validate_parsed_coordinate


# ── dms_to_decimal ───────────────────────────────────────────────────


class TestDmsToDecimal:
    """Tests for dms_to_decimal."""

    def test_basic_north(self):
        """40°42'51.93"N → 40.71442500."""
        result = dms_to_decimal(40, 42, 51.93, "N")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_basic_west(self):
        """74° 2'53.73"W → -(74 + 2/60 + 53.73/3600)."""
        result = dms_to_decimal(74, 2, 53.73, "W")
        expected = -(74 + 2 / 60 + 53.73 / 3600)
        assert result == pytest.approx(expected, abs=1e-6)

    def test_south_negates(self):
        """33°52'7.68"S → -33.8688."""
        result = dms_to_decimal(33, 52, 7.68, "S")
        assert result == pytest.approx(-33.8688, abs=1e-4)

    def test_east_positive(self):
        """2°20'56.0"E → positive."""
        result = dms_to_decimal(2, 20, 56.0, "E")
        assert result > 0

    def test_no_direction_positive(self):
        """Without direction, positive degrees stay positive."""
        result = dms_to_decimal(40, 42, 51.93, None)
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_no_direction_negative_degrees(self):
        """Without direction, negative degrees stay negative."""
        result = dms_to_decimal(-74, 2, 53.73, None)
        expected = -(74 + 2 / 60 + 53.73 / 3600)
        assert result == pytest.approx(expected, abs=1e-6)

    def test_zero_minutes_seconds(self):
        """Exactly 45 degrees, 0 min, 0 sec."""
        assert dms_to_decimal(45, 0, 0, "N") == 45.0

    def test_lowercase_direction(self):
        """Lowercase direction letters are accepted."""
        result = dms_to_decimal(74, 2, 53.73, "w")
        expected = -(74 + 2 / 60 + 53.73 / 3600)
        assert result == pytest.approx(expected, abs=1e-6)

    def test_invalid_minutes_raises(self):
        with pytest.raises(ValueError, match="Minutes"):
            dms_to_decimal(40, 60, 0, "N")

    def test_negative_minutes_raises(self):
        with pytest.raises(ValueError, match="Minutes"):
            dms_to_decimal(40, -1, 0, "N")

    def test_invalid_seconds_raises(self):
        with pytest.raises(ValueError, match="Seconds"):
            dms_to_decimal(40, 0, 60, "N")

    def test_negative_seconds_raises(self):
        with pytest.raises(ValueError, match="Seconds"):
            dms_to_decimal(40, 0, -1, "N")

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError, match="Direction"):
            dms_to_decimal(40, 0, 0, "X")


# ── parse_coordinate ─────────────────────────────────────────────────


class TestParseCoordinateDecimal:
    """Tests for parse_coordinate with decimal input."""

    def test_negative_decimal_longitude(self):
        result = parse_coordinate("-74.04798056", "longitude")
        assert result == pytest.approx(-74.04798056)

    def test_positive_decimal_latitude(self):
        result = parse_coordinate("40.7144", "latitude")
        assert result == pytest.approx(40.7144)

    def test_zero(self):
        result = parse_coordinate("0", "latitude")
        assert result == 0.0

    def test_integer_form(self):
        result = parse_coordinate("90", "latitude")
        assert result == 90.0

    def test_whitespace_stripped(self):
        result = parse_coordinate("  -74.047980  ", "longitude")
        assert result == pytest.approx(-74.047980)

    def test_seven_decimal_places(self):
        result = parse_coordinate("-120.1234567", "longitude")
        assert result == pytest.approx(-120.1234567)


class TestParseCoordinateDmsSymbol:
    """Tests for parse_coordinate with DMS symbol format."""

    def test_north_latitude(self):
        """40°42'51.93"N → 40.71442500."""
        result = parse_coordinate('40°42\'51.93"N', "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_west_longitude(self):
        """74° 2'53.73"W → -(74 + 2/60 + 53.73/3600)."""
        result = parse_coordinate('74° 2\'53.73"W', "longitude")
        expected = -(74 + 2 / 60 + 53.73 / 3600)
        assert result == pytest.approx(expected, abs=1e-6)

    def test_south_latitude(self):
        """33°52'7.68"S → -33.8688."""
        result = parse_coordinate('33°52\'7.68"S', "latitude")
        assert result == pytest.approx(-33.8688, abs=1e-4)


class TestParseCoordinateDmsColon:
    """Tests for parse_coordinate with colon-separated DMS."""

    def test_west_colon(self):
        """74:02:53.73W → -(74 + 2/60 + 53.73/3600)."""
        result = parse_coordinate("74:02:53.73W", "longitude")
        expected = -(74 + 2 / 60 + 53.73 / 3600)
        assert result == pytest.approx(expected, abs=1e-6)

    def test_north_colon(self):
        """40:42:51.93N → 40.71442500."""
        result = parse_coordinate("40:42:51.93N", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_no_direction_colon(self):
        """40:42:51.93 (no direction) → positive decimal."""
        result = parse_coordinate("40:42:51.93", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)


class TestParseCoordinateDmsSpace:
    """Tests for parse_coordinate with space-separated DMS."""

    def test_north_space(self):
        """40 42 51.93 N → 40.71442500."""
        result = parse_coordinate("40 42 51.93 N", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_west_space(self):
        """74 2 53.73 W → -(74 + 2/60 + 53.73/3600)."""
        result = parse_coordinate("74 2 53.73 W", "longitude")
        expected = -(74 + 2 / 60 + 53.73 / 3600)
        assert result == pytest.approx(expected, abs=1e-6)


class TestParseCoordinateErrors:
    """Tests for parse_coordinate error cases."""

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty"):
            parse_coordinate("", "latitude")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            parse_coordinate("   ", "latitude")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unable to parse"):
            parse_coordinate("not a coordinate", "latitude")

    def test_invalid_coord_type_raises(self):
        with pytest.raises(ValueError, match="coord_type"):
            parse_coordinate("40.0", "altitude")

    def test_latitude_out_of_range_positive(self):
        with pytest.raises(ValueError, match="Latitude"):
            parse_coordinate("91.0", "latitude")

    def test_latitude_out_of_range_negative(self):
        with pytest.raises(ValueError, match="Latitude"):
            parse_coordinate("-91.0", "latitude")

    def test_longitude_out_of_range_positive(self):
        with pytest.raises(ValueError, match="Longitude"):
            parse_coordinate("181.0", "longitude")

    def test_longitude_out_of_range_negative(self):
        with pytest.raises(ValueError, match="Longitude"):
            parse_coordinate("-181.0", "longitude")

    def test_dms_out_of_range_latitude(self):
        """DMS that resolves to >90 for latitude raises."""
        with pytest.raises(ValueError, match="Latitude"):
            parse_coordinate("91:00:00N", "latitude")


# ── validate_parsed_coordinate ───────────────────────────────────────


class TestValidateParsedCoordinate:
    """Tests for validate_parsed_coordinate."""

    def test_valid_latitude(self):
        assert validate_parsed_coordinate(45.0, "latitude") is True

    def test_valid_longitude(self):
        assert validate_parsed_coordinate(-120.5, "longitude") is True

    def test_boundary_latitude_90(self):
        assert validate_parsed_coordinate(90.0, "latitude") is True

    def test_boundary_latitude_neg90(self):
        assert validate_parsed_coordinate(-90.0, "latitude") is True

    def test_boundary_longitude_180(self):
        assert validate_parsed_coordinate(180.0, "longitude") is True

    def test_boundary_longitude_neg180(self):
        assert validate_parsed_coordinate(-180.0, "longitude") is True

    def test_zero(self):
        assert validate_parsed_coordinate(0.0, "latitude") is True
        assert validate_parsed_coordinate(0.0, "longitude") is True

    def test_invalid_latitude_raises(self):
        with pytest.raises(ValueError, match="Latitude"):
            validate_parsed_coordinate(90.1, "latitude")

    def test_invalid_longitude_raises(self):
        with pytest.raises(ValueError, match="Longitude"):
            validate_parsed_coordinate(180.1, "longitude")

    def test_invalid_coord_type_raises(self):
        with pytest.raises(ValueError, match="coord_type"):
            validate_parsed_coordinate(0.0, "altitude")
