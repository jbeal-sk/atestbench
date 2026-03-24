"""End-to-end integration tests for the Photo Map workflow.

Margaret — Testing & Quality Assurance (Phase 5)

These tests verify that all modules work together correctly:
code_assigner → gps_extractor → affine_transform → document_stamper → markdown_report
"""

import io

import fitz
import numpy as np
import pytest
from PIL import Image

from affine_transform import (
    build_affine_transform,
    compute_fourth_corner,
    geo_to_page,
    is_within_bounds,
)
from code_assigner import assign_codes
from document_stamper import stamp_document, stamp_image, stamp_pdf
from kml_generator import generate_kml
from markdown_report import generate_markdown_report


# ── Helpers ──────────────────────────────────────────────────────────


def _make_pdf_bytes(width=612, height=792):
    """Create a minimal single-page PDF in memory."""
    doc = fitz.open()
    doc.new_page(width=width, height=height)
    data = doc.tobytes()
    doc.close()
    return data


def _make_image_bytes(width=400, height=400, fmt="PNG"):
    """Create a minimal image in memory."""
    img = Image.new("RGB", (width, height), color="lightblue")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ── Integration: Full Photo Map Workflow ─────────────────────────────


class TestFullWorkflowPdf:
    """End-to-end test: assign codes → transform → stamp PDF."""

    def test_full_photo_map_workflow_pdf(self):
        """Complete workflow: codes + affine transform + PDF stamping."""
        # Step 1: Simulate photo data (as extract_gps_from_files would return)
        photo_data = [
            {"name": "IMG_001.jpg", "lat": 40.0, "lon": -74.0,
             "datetime": "2024:03:15 14:30:00"},
            {"name": "IMG_002.jpg", "lat": 40.5, "lon": -73.5,
             "datetime": "2024:03:15 14:35:00"},
            {"name": "IMG_003.jpg", "lat": 41.0, "lon": -74.0,
             "datetime": None},
            {"name": "IMG_004.jpg", "lat": None, "lon": None,
             "datetime": "2024:03:15 14:40:00"},
        ]

        # Step 2: Assign codes
        code_map = assign_codes([p["name"] for p in photo_data])
        for p in photo_data:
            p["code"] = code_map[p["name"]]

        assert code_map["IMG_001.jpg"] == "A1"
        assert code_map["IMG_002.jpg"] == "A2"
        assert code_map["IMG_003.jpg"] == "A3"
        assert code_map["IMG_004.jpg"] == "A4"

        # Step 3: Filter photos with GPS
        valid = [p for p in photo_data if p["lat"] is not None and p["lon"] is not None]
        assert len(valid) == 3

        # Step 4: Define corners and compute 4th corner
        corners = {
            "TL": (41.0, -74.0),
            "TR": (41.0, -73.0),
            "BL": (40.0, -74.0),
        }
        fourth = compute_fourth_corner(corners, "BR")
        assert fourth == pytest.approx((40.0, -73.0))

        all_corners = dict(corners)
        all_corners["BR"] = fourth

        # Step 5: Build affine transform
        page_width, page_height = 612, 792
        page_corner_map = {
            "TL": (0.0, 0.0),
            "TR": (page_width, 0.0),
            "BL": (0.0, page_height),
            "BR": (page_width, page_height),
        }

        geo_points = [all_corners["TL"], all_corners["TR"], all_corners["BL"]]
        page_points = [page_corner_map["TL"], page_corner_map["TR"], page_corner_map["BL"]]
        affine_matrix = build_affine_transform(geo_points, page_points)

        # Step 6: Map photos and check bounds
        bounds_corners = [
            all_corners["TL"], all_corners["TR"],
            all_corners["BR"], all_corners["BL"],
        ]

        stamps = []
        for p in valid:
            lat, lon = p["lat"], p["lon"]
            if is_within_bounds(lat, lon, bounds_corners):
                x, y = geo_to_page(lat, lon, affine_matrix)
                stamps.append({"code": p["code"], "x": x, "y": y})

        assert len(stamps) >= 2  # At least some photos should be in bounds

        # Step 7: Stamp PDF
        pdf_bytes = _make_pdf_bytes(width=page_width, height=page_height)
        output_bytes, output_name = stamp_document(pdf_bytes, "site_map.pdf", stamps)

        assert output_name == "site_map_stamped.pdf"

        # Verify output is valid and contains stamp text
        doc = fitz.open(stream=output_bytes, filetype="pdf")
        text = doc[0].get_text()
        doc.close()

        for stamp in stamps:
            assert stamp["code"] in text

    def test_full_photo_map_workflow_image(self):
        """Complete workflow: codes + affine transform + image stamping."""
        photo_data = [
            {"name": "photo1.jpg", "lat": 0.0, "lon": 0.0,
             "datetime": "2024:01:01 12:00:00"},
            {"name": "photo2.jpg", "lat": 5.0, "lon": 5.0,
             "datetime": None},
        ]

        code_map = assign_codes([p["name"] for p in photo_data])
        for p in photo_data:
            p["code"] = code_map[p["name"]]

        corners = {
            "TL": (10.0, 0.0),
            "TR": (10.0, 10.0),
            "BL": (0.0, 0.0),
        }
        fourth = compute_fourth_corner(corners, "BR")
        all_corners = dict(corners)
        all_corners["BR"] = fourth

        page_width, page_height = 400, 400
        page_corner_map = {
            "TL": (0.0, 0.0),
            "TR": (page_width, 0.0),
            "BL": (0.0, page_height),
            "BR": (page_width, page_height),
        }

        geo_points = [all_corners[k] for k in ("TL", "TR", "BL")]
        page_points = [page_corner_map[k] for k in ("TL", "TR", "BL")]
        affine_matrix = build_affine_transform(geo_points, page_points)

        bounds_corners = [
            all_corners["TL"], all_corners["TR"],
            all_corners["BR"], all_corners["BL"],
        ]

        stamps = []
        for p in photo_data:
            if p["lat"] is not None and p["lon"] is not None:
                if is_within_bounds(p["lat"], p["lon"], bounds_corners):
                    x, y = geo_to_page(p["lat"], p["lon"], affine_matrix)
                    stamps.append({"code": p["code"], "x": x, "y": y})

        assert len(stamps) == 2

        img_bytes = _make_image_bytes(width=page_width, height=page_height)
        output_bytes, output_name = stamp_document(img_bytes, "aerial.png", stamps)

        assert output_name == "aerial_stamped.png"
        output_img = Image.open(io.BytesIO(output_bytes))
        assert output_img.size == (page_width, page_height)


class TestFullWorkflowMarkdownReport:
    """Integration: codes + metadata → markdown report."""

    def test_report_from_mixed_data(self):
        """Markdown report includes all photos with correct handling of missing data."""
        photo_data = [
            {"name": "a.jpg", "lat": 40.0, "lon": -74.0,
             "datetime": "2024:03:15 14:30:22"},
            {"name": "b.jpg", "lat": None, "lon": None,
             "datetime": None},
            {"name": "c.jpg", "lat": 41.0, "lon": -73.0,
             "datetime": None},
        ]

        code_map = assign_codes([p["name"] for p in photo_data])
        for p in photo_data:
            p["code"] = code_map[p["name"]]

        report = generate_markdown_report(photo_data)

        assert "# Photo Location Report" in report
        assert "A1" in report
        assert "A2" in report
        assert "A3" in report
        assert "No date available" in report
        assert "No GPS" in report
        assert "40.0, -74.0" in report


class TestFullWorkflowKml:
    """Integration: codes + GPS data → KML with codes in descriptions."""

    def test_kml_includes_codes(self):
        """KML output includes photo codes in point descriptions."""
        photo_data = [
            {"name": "a.jpg", "lat": 40.0, "lon": -74.0, "code": "A1"},
            {"name": "b.jpg", "lat": 41.0, "lon": -73.0, "code": "A2"},
        ]

        kml = generate_kml(photo_data)
        assert "[A1]" in kml
        assert "[A2]" in kml
        assert "a.jpg" in kml
        assert "b.jpg" in kml


# ── Edge Cases: Boundary Conditions ──────────────────────────────────


class TestEdgeCases:
    """Edge-case integration tests."""

    def test_all_photos_outside_bounds(self):
        """When all photos are outside document bounds, no stamps are produced."""
        corners = {
            "TL": (10.0, 10.0),
            "TR": (10.0, 11.0),
            "BL": (9.0, 10.0),
        }
        fourth = compute_fourth_corner(corners, "BR")
        all_corners = dict(corners)
        all_corners["BR"] = fourth

        bounds_corners = [
            all_corners["TL"], all_corners["TR"],
            all_corners["BR"], all_corners["BL"],
        ]

        # Photo is far outside the document bounds
        lat, lon = 0.0, 0.0
        assert is_within_bounds(lat, lon, bounds_corners) is False

    def test_photo_exactly_on_corner(self):
        """A photo at exactly a corner position is within bounds."""
        all_corners = {
            "TL": (10.0, 0.0),
            "TR": (10.0, 10.0),
            "BL": (0.0, 0.0),
            "BR": (0.0, 10.0),
        }

        bounds_corners = [
            all_corners["TL"], all_corners["TR"],
            all_corners["BR"], all_corners["BL"],
        ]

        assert is_within_bounds(10.0, 0.0, bounds_corners) is True

    def test_zero_stamps_produces_valid_output(self):
        """Stamping with no stamps produces a valid document."""
        pdf_bytes = _make_pdf_bytes()
        output_bytes, output_name = stamp_document(pdf_bytes, "map.pdf", [])
        assert output_name == "map_stamped.pdf"
        doc = fitz.open(stream=output_bytes, filetype="pdf")
        assert doc.page_count == 1
        doc.close()

    def test_single_photo_full_workflow(self):
        """Single photo full workflow produces correct output."""
        photo_data = [
            {"name": "solo.jpg", "lat": 5.0, "lon": 5.0,
             "datetime": "2024:06:01 09:00:00"},
        ]

        code_map = assign_codes([p["name"] for p in photo_data])
        assert code_map["solo.jpg"] == "A1"
        photo_data[0]["code"] = "A1"

        corners = {
            "TL": (10.0, 0.0),
            "TR": (10.0, 10.0),
            "BL": (0.0, 0.0),
        }
        fourth = compute_fourth_corner(corners, "BR")
        all_corners = dict(corners)
        all_corners["BR"] = fourth

        geo_points = [all_corners["TL"], all_corners["TR"], all_corners["BL"]]
        page_points = [(0, 0), (400, 0), (0, 400)]
        affine_matrix = build_affine_transform(geo_points, page_points)

        x, y = geo_to_page(5.0, 5.0, affine_matrix)
        assert 0 <= x <= 400
        assert 0 <= y <= 400

        stamps = [{"code": "A1", "x": x, "y": y}]
        img_bytes = _make_image_bytes(width=400, height=400)
        output_bytes, output_name = stamp_document(img_bytes, "map.png", stamps)
        assert output_name == "map_stamped.png"

    def test_260_photos_full_code_assignment(self):
        """260 photos use all available codes A1 through Z0."""
        names = [f"photo_{i:03d}.jpg" for i in range(260)]
        code_map = assign_codes(names)

        assert len(code_map) == 260
        assert code_map[names[0]] == "A1"
        assert code_map[names[259]] == "Z0"

        # All codes are unique
        codes = list(code_map.values())
        assert len(set(codes)) == 260

    def test_app_module_imports(self):
        """Verify all modules imported by app.py can be imported without error."""
        import gps_extractor
        import kml_generator
        import code_assigner
        import markdown_report
        import affine_transform
        import document_stamper

        # Verify key functions exist
        assert callable(gps_extractor.extract_gps_from_files)
        assert callable(kml_generator.generate_kml)
        assert callable(code_assigner.assign_codes)
        assert callable(markdown_report.generate_markdown_report)
        assert callable(affine_transform.compute_fourth_corner)
        assert callable(affine_transform.build_affine_transform)
        assert callable(affine_transform.geo_to_page)
        assert callable(affine_transform.is_within_bounds)
        assert callable(document_stamper.stamp_document)

    def test_no_duplicate_function_in_gps_extractor(self):
        """Verify the duplicate function definition bug in gps_extractor.py is resolved."""
        import inspect
        import gps_extractor

        source = inspect.getsource(gps_extractor)
        # extract_gps_from_files should be defined exactly once
        count = source.count("def extract_gps_from_files(")
        assert count == 1, (
            f"extract_gps_from_files is defined {count} times; expected exactly 1"
        )
