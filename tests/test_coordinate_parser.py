"""Tests for coordinate_parser.py — Frances (Phase 6).

Covers:
  • parse_coordinate with decimal degrees
  • parse_coordinate with DMS (symbols / colons / spaces)
  • dms_to_decimal
  • validate_parsed_coordinate
  • Error handling for invalid inputs
"""

import pytest

from coordinate_parser import (
    dms_to_decimal,
    parse_coordinate,
    validate_parsed_coordinate,
)


# ── dms_to_decimal ───────────────────────────────────────────────────


class TestDmsToDecimal:
    def test_north(self):
        # 40°42'51.93"N → 40.71442500
        result = dms_to_decimal(40, 42, 51.93, "N")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_south(self):
        result = dms_to_decimal(33, 52, 7.68, "S")
        assert result == pytest.approx(-33.8688, abs=1e-4)

    def test_west(self):
        # 74° 2'53.73"W → -(74 + 2/60 + 53.73/3600)
        result = dms_to_decimal(74, 2, 53.73, "W")
        assert result == pytest.approx(-74.048258333, abs=1e-6)

    def test_east(self):
        result = dms_to_decimal(2, 17, 40.2, "E")
        assert result == pytest.approx(2.29450, abs=1e-4)

    def test_no_direction(self):
        result = dms_to_decimal(74, 2, 53.73, None)
        assert result == pytest.approx(74.048258333, abs=1e-6)

    def test_lowercase_direction(self):
        result = dms_to_decimal(40, 42, 51.93, "n")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_zero_values(self):
        assert dms_to_decimal(0, 0, 0.0, "N") == 0.0

    def test_negative_degrees_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            dms_to_decimal(-10, 0, 0, "N")

    def test_minutes_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Minutes"):
            dms_to_decimal(10, 60, 0, "N")

    def test_seconds_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Seconds"):
            dms_to_decimal(10, 0, 60, "N")

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError, match="Direction"):
            dms_to_decimal(10, 0, 0, "X")


# ── validate_parsed_coordinate ────────────────────────────────────────


class TestValidateParsedCoordinate:
    def test_valid_latitude(self):
        assert validate_parsed_coordinate(45.0, "latitude") is True

    def test_valid_longitude(self):
        assert validate_parsed_coordinate(-120.0, "longitude") is True

    def test_latitude_boundary_positive(self):
        assert validate_parsed_coordinate(90.0, "latitude") is True

    def test_latitude_boundary_negative(self):
        assert validate_parsed_coordinate(-90.0, "latitude") is True

    def test_longitude_boundary_positive(self):
        assert validate_parsed_coordinate(180.0, "longitude") is True

    def test_longitude_boundary_negative(self):
        assert validate_parsed_coordinate(-180.0, "longitude") is True

    def test_latitude_out_of_range(self):
        with pytest.raises(ValueError, match="Latitude"):
            validate_parsed_coordinate(91.0, "latitude")

    def test_latitude_out_of_range_negative(self):
        with pytest.raises(ValueError, match="Latitude"):
            validate_parsed_coordinate(-91.0, "latitude")

    def test_longitude_out_of_range(self):
        with pytest.raises(ValueError, match="Longitude"):
            validate_parsed_coordinate(181.0, "longitude")

    def test_longitude_out_of_range_negative(self):
        with pytest.raises(ValueError, match="Longitude"):
            validate_parsed_coordinate(-181.0, "longitude")

    def test_invalid_coord_type(self):
        with pytest.raises(ValueError, match="coord_type"):
            validate_parsed_coordinate(0.0, "altitude")

    def test_zero_latitude(self):
        assert validate_parsed_coordinate(0.0, "latitude") is True

    def test_zero_longitude(self):
        assert validate_parsed_coordinate(0.0, "longitude") is True


# ── parse_coordinate: decimal degrees ─────────────────────────────────


class TestParseCoordinateDecimal:
    def test_positive_decimal_latitude(self):
        assert parse_coordinate("40.71442500", "latitude") == pytest.approx(40.71442500)

    def test_negative_decimal_longitude(self):
        assert parse_coordinate("-74.04798056", "longitude") == pytest.approx(-74.04798056)

    def test_positive_decimal_longitude(self):
        assert parse_coordinate("74.047980", "longitude") == pytest.approx(74.047980)

    def test_negative_decimal_latitude(self):
        assert parse_coordinate("-33.8688", "latitude") == pytest.approx(-33.8688)

    def test_integer_decimal(self):
        assert parse_coordinate("40", "latitude") == 40.0

    def test_zero(self):
        assert parse_coordinate("0.0", "latitude") == 0.0

    def test_whitespace_padded(self):
        assert parse_coordinate("  -74.04798056  ", "longitude") == pytest.approx(-74.04798056)

    def test_seven_decimal_places(self):
        assert parse_coordinate("-120.1234567", "longitude") == pytest.approx(-120.1234567)

    def test_six_decimal_places(self):
        assert parse_coordinate("48.856613", "latitude") == pytest.approx(48.856613)


# ── parse_coordinate: DMS with symbols ────────────────────────────────


class TestParseCoordinateDmsSymbol:
    def test_north_dms(self):
        result = parse_coordinate("40°42'51.93\"N", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_west_dms(self):
        result = parse_coordinate("74° 2'53.73\"W", "longitude")
        assert result == pytest.approx(-74.048258333, abs=1e-6)

    def test_south_dms(self):
        result = parse_coordinate("33°52'7.68\"S", "latitude")
        assert result == pytest.approx(-33.8688, abs=1e-4)

    def test_east_dms(self):
        result = parse_coordinate("2°17'40.2\"E", "longitude")
        assert result == pytest.approx(2.29450, abs=1e-4)

    def test_no_direction_symbol(self):
        # Without compass direction, value is positive
        result = parse_coordinate("40°42'51.93\"", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)


# ── parse_coordinate: DMS with colons ─────────────────────────────────


class TestParseCoordinateDmsColon:
    def test_west_colon(self):
        result = parse_coordinate("74:02:53.73W", "longitude")
        assert result == pytest.approx(-74.048258333, abs=1e-6)

    def test_north_colon(self):
        result = parse_coordinate("40:42:51.93N", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_no_direction_colon(self):
        result = parse_coordinate("74:02:53.73", "longitude")
        assert result == pytest.approx(74.048258333, abs=1e-6)


# ── parse_coordinate: DMS with spaces ─────────────────────────────────


class TestParseCoordinateDmsSpace:
    def test_west_space(self):
        result = parse_coordinate("74 2 53.73 W", "longitude")
        assert result == pytest.approx(-74.048258333, abs=1e-6)

    def test_north_space(self):
        result = parse_coordinate("40 42 51.93 N", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)

    def test_no_direction_space(self):
        result = parse_coordinate("40 42 51.93", "latitude")
        assert result == pytest.approx(40.71442500, abs=1e-6)


# ── parse_coordinate: error handling ──────────────────────────────────


class TestParseCoordinateErrors:
    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_coordinate("", "latitude")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_coordinate("   ", "latitude")

    def test_garbage_raises(self):
        with pytest.raises(ValueError, match="Unrecognised"):
            parse_coordinate("not a coordinate", "latitude")

    def test_latitude_out_of_range_decimal(self):
        with pytest.raises(ValueError, match="Latitude"):
            parse_coordinate("95.0", "latitude")

    def test_longitude_out_of_range_decimal(self):
        with pytest.raises(ValueError, match="Longitude"):
            parse_coordinate("200.0", "longitude")

    def test_none_input_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_coordinate(None, "latitude")

    def test_non_string_input_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_coordinate(123, "latitude")
