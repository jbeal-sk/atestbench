"""Tests for kml_generator module."""

import pytest

from kml_generator import generate_kml


class TestGenerateKml:
    """Tests for generate_kml."""

    def test_returns_kml_string(self):
        """Output is a valid KML string."""
        data = [{"name": "a.jpg", "lat": 40.0, "lon": -74.0}]
        result = generate_kml(data)
        assert isinstance(result, str)
        assert "<kml" in result

    def test_single_point(self):
        """A single photo with GPS creates one KML point."""
        data = [{"name": "photo.jpg", "lat": 40.7128, "lon": -74.006}]
        result = generate_kml(data)
        assert "photo.jpg" in result
        assert "-74.006" in result

    def test_skips_none_lat_lon(self):
        """Photos without GPS data are excluded from KML output."""
        data = [
            {"name": "good.jpg", "lat": 40.0, "lon": -74.0},
            {"name": "bad.jpg", "lat": None, "lon": None},
        ]
        result = generate_kml(data)
        assert "good.jpg" in result
        assert "bad.jpg" not in result

    def test_empty_list(self):
        """Empty photo list produces a valid KML with no points."""
        result = generate_kml([])
        assert "<kml" in result

    def test_code_included_in_description(self):
        """When code is present, it appears in the KML point description."""
        data = [{"name": "a.jpg", "lat": 40.0, "lon": -74.0, "code": "A1"}]
        result = generate_kml(data)
        assert "[A1]" in result

    def test_code_absent_still_works(self):
        """When code key is absent, KML is generated without error."""
        data = [{"name": "a.jpg", "lat": 40.0, "lon": -74.0}]
        result = generate_kml(data)
        assert "a.jpg" in result

    def test_multiple_points_with_codes(self):
        """Multiple photos with codes all appear in KML."""
        data = [
            {"name": "a.jpg", "lat": 40.0, "lon": -74.0, "code": "A1"},
            {"name": "b.jpg", "lat": 41.0, "lon": -73.0, "code": "A2"},
            {"name": "c.jpg", "lat": 42.0, "lon": -72.0, "code": "A3"},
        ]
        result = generate_kml(data)
        assert "[A1]" in result
        assert "[A2]" in result
        assert "[A3]" in result

    def test_skips_none_lat_only(self):
        """Photo with None lat is excluded."""
        data = [{"name": "a.jpg", "lat": None, "lon": -74.0}]
        result = generate_kml(data)
        assert "a.jpg" not in result

    def test_skips_none_lon_only(self):
        """Photo with None lon is excluded."""
        data = [{"name": "a.jpg", "lat": 40.0, "lon": None}]
        result = generate_kml(data)
        assert "a.jpg" not in result
