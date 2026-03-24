from datetime import date

import pytest

from markdown_report import generate_markdown_report


class TestGenerateMarkdownReport:
    """Tests for generate_markdown_report."""

    def test_title_present(self):
        """Output starts with the expected markdown title."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": 2.0,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert result.startswith("# Photo Location Report")

    def test_table_header(self):
        """Output contains the expected table header row."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": 2.0,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert "| Code | Filename | Date/Time | Coordinates |" in result

    def test_single_photo_with_all_fields(self):
        """A single photo with all fields produces the correct table row."""
        data = [{"name": "IMG_001.jpg", "lat": 40.7128, "lon": -74.006,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert "| A1 | IMG_001.jpg | 2024:03:15 14:30:22 | 40.7128, -74.006 |" in result

    def test_missing_datetime(self):
        """Photos without datetime show 'No date available'."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": 2.0,
                 "datetime": None, "code": "A1"}]
        result = generate_markdown_report(data)
        assert "No date available" in result

    def test_missing_gps(self):
        """Photos without GPS show 'No GPS' in coordinates."""
        data = [{"name": "a.jpg", "lat": None, "lon": None,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert "No GPS" in result

    def test_missing_lat_only(self):
        """If only lat is None, coordinates show 'No GPS'."""
        data = [{"name": "a.jpg", "lat": None, "lon": 2.0,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert "No GPS" in result

    def test_missing_lon_only(self):
        """If only lon is None, coordinates show 'No GPS'."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": None,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert "No GPS" in result

    def test_footer_generation_date(self):
        """Footer contains the current generation date."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": 2.0,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert f"Generated on {date.today().isoformat()}" in result

    def test_empty_list(self):
        """Empty photo list produces a table with header only plus footer."""
        result = generate_markdown_report([])
        assert "# Photo Location Report" in result
        assert "| Code | Filename | Date/Time | Coordinates |" in result
        assert f"Generated on {date.today().isoformat()}" in result

    def test_sorted_by_code_order(self):
        """Photos are sorted by code assignment order, not alphabetically."""
        data = [
            {"name": "c.jpg", "lat": 1.0, "lon": 2.0,
             "datetime": None, "code": "B1"},
            {"name": "a.jpg", "lat": 1.0, "lon": 2.0,
             "datetime": None, "code": "A1"},
            {"name": "b.jpg", "lat": 1.0, "lon": 2.0,
             "datetime": None, "code": "A2"},
        ]
        result = generate_markdown_report(data)
        lines = result.strip().split("\n")
        # Find data rows (after header and separator)
        data_rows = [l for l in lines if l.startswith("| A") or l.startswith("| B")]
        assert len(data_rows) == 3
        assert "A1" in data_rows[0]
        assert "A2" in data_rows[1]
        assert "B1" in data_rows[2]

    def test_multiple_photos_mixed_data(self):
        """Multiple photos with mixed data availability."""
        data = [
            {"name": "img1.jpg", "lat": 40.0, "lon": -74.0,
             "datetime": "2024:03:15 14:30:22", "code": "A1"},
            {"name": "img2.jpg", "lat": None, "lon": None,
             "datetime": None, "code": "A2"},
            {"name": "img3.jpg", "lat": 41.0, "lon": -73.0,
             "datetime": None, "code": "A3"},
        ]
        result = generate_markdown_report(data)
        assert "| A1 | img1.jpg | 2024:03:15 14:30:22 | 40.0, -74.0 |" in result
        assert "| A2 | img2.jpg | No date available | No GPS |" in result
        assert "| A3 | img3.jpg | No date available | 41.0, -73.0 |" in result

    def test_output_is_valid_markdown_table(self):
        """Output contains proper markdown table delimiters."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": 2.0,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        lines = result.strip().split("\n")
        # Line 0: title, Line 1: blank, Line 2: header, Line 3: separator
        assert lines[2].startswith("|")
        assert lines[3].startswith("|---")

    def test_return_type_is_string(self):
        """Return value is a string."""
        result = generate_markdown_report([])
        assert isinstance(result, str)

    def test_ends_with_newline(self):
        """Output ends with a trailing newline for clean file writing."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": 2.0,
                 "datetime": "2024:03:15 14:30:22", "code": "A1"}]
        result = generate_markdown_report(data)
        assert result.endswith("\n")

    def test_empty_datetime_string_treated_as_missing(self):
        """An empty string datetime is treated as missing."""
        data = [{"name": "a.jpg", "lat": 1.0, "lon": 2.0,
                 "datetime": "", "code": "A1"}]
        result = generate_markdown_report(data)
        assert "No date available" in result
