"""Tests for document_stamper module (Helen — Document Stamper)."""

import io

import fitz  # PyMuPDF
import pytest
from PIL import Image

from document_stamper import StampStyle, stamp_document, stamp_image, stamp_pdf


# ── Helpers ──────────────────────────────────────────────────────────


def _make_pdf_bytes(width=612, height=792, rotation=0):
    """Create a minimal single-page PDF in memory."""
    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    if rotation:
        page.set_rotation(rotation)
    data = doc.tobytes()
    doc.close()
    return data


def _make_image_bytes(width=200, height=200, fmt="PNG"):
    """Create a minimal image in memory."""
    img = Image.new("RGB", (width, height), color="gray")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ── stamp_pdf ────────────────────────────────────────────────────────


class TestStampPdf:
    """Tests for stamp_pdf."""

    def test_returns_valid_pdf(self):
        """Output is a valid PDF that opens without error."""
        pdf = _make_pdf_bytes()
        stamps = [{"code": "A1", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        assert doc.page_count == 1
        doc.close()

    def test_text_present_in_output(self):
        """Stamped code text is present on the page."""
        pdf = _make_pdf_bytes()
        stamps = [{"code": "B3", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "B3" in text

    def test_multiple_stamps(self):
        """Multiple stamps are all rendered."""
        pdf = _make_pdf_bytes()
        stamps = [
            {"code": "A1", "x": 50.0, "y": 50.0},
            {"code": "A2", "x": 200.0, "y": 200.0},
            {"code": "C5", "x": 300.0, "y": 400.0},
        ]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "A1" in text
        assert "A2" in text
        assert "C5" in text

    def test_zero_stamps_returns_valid_pdf(self):
        """Zero stamps returns the document essentially unchanged."""
        pdf = _make_pdf_bytes()
        result = stamp_pdf(pdf, [])
        doc = fitz.open(stream=result, filetype="pdf")
        assert doc.page_count == 1
        doc.close()

    def test_stamp_near_edge_is_clamped(self):
        """Stamps near page edges are clamped so text remains visible."""
        pdf = _make_pdf_bytes(width=200, height=200)
        # Position far off to the right and bottom
        stamps = [{"code": "Z9", "x": 999.0, "y": 999.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "Z9" in text

    def test_original_content_preserved(self):
        """Existing text content is not destroyed by stamping."""
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)
        page.insert_text(fitz.Point(72, 72), "Original Content", fontsize=14)
        pdf = doc.tobytes()
        doc.close()

        stamps = [{"code": "A1", "x": 300.0, "y": 300.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "Original Content" in text
        assert "A1" in text

    def test_stamp_text_is_red(self):
        """Stamped code text is rendered in red."""
        pdf = _make_pdf_bytes()
        stamps = [{"code": "A1", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        page = doc[0]
        text_dict = page.get_text("dict")
        stamp_color = None
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() == "A1":
                            stamp_color = span["color"]
        doc.close()
        assert stamp_color is not None, "Stamp text 'A1' not found"
        # 0xff0000 is red in PyMuPDF's integer color representation
        assert stamp_color == 0xFF0000


# ── stamp_image ──────────────────────────────────────────────────────


class TestStampImage:
    """Tests for stamp_image."""

    def test_returns_valid_png(self):
        """Output is a valid PNG image."""
        img = _make_image_bytes()
        stamps = [{"code": "A1", "x": 50.0, "y": 50.0}]
        result = stamp_image(img, stamps)
        output_img = Image.open(io.BytesIO(result))
        assert output_img.format == "PNG"

    def test_output_dimensions_preserved(self):
        """Output image has the same dimensions as the input."""
        img = _make_image_bytes(width=300, height=400)
        stamps = [{"code": "A1", "x": 50.0, "y": 50.0}]
        result = stamp_image(img, stamps)
        output_img = Image.open(io.BytesIO(result))
        assert output_img.size == (300, 400)

    def test_zero_stamps_returns_valid_image(self):
        """Zero stamps returns a valid image."""
        img = _make_image_bytes()
        result = stamp_image(img, [])
        output_img = Image.open(io.BytesIO(result))
        assert output_img.size == (200, 200)

    def test_stamp_near_edge_is_clamped(self):
        """Stamps near image edges are clamped within bounds."""
        img = _make_image_bytes(width=100, height=100)
        stamps = [{"code": "Z0", "x": 999.0, "y": 999.0}]
        result = stamp_image(img, stamps)
        # Should not raise; output should be a valid image
        output_img = Image.open(io.BytesIO(result))
        assert output_img.size == (100, 100)

    def test_multiple_stamps(self):
        """Multiple stamps don't cause errors."""
        img = _make_image_bytes(width=400, height=400)
        stamps = [
            {"code": "A1", "x": 10.0, "y": 10.0},
            {"code": "A2", "x": 200.0, "y": 200.0},
            {"code": "C5", "x": 350.0, "y": 350.0},
        ]
        result = stamp_image(img, stamps)
        output_img = Image.open(io.BytesIO(result))
        assert output_img.size == (400, 400)

    def test_jpeg_input_returns_png(self):
        """JPEG input is converted to PNG output."""
        img = _make_image_bytes(fmt="JPEG")
        stamps = [{"code": "A1", "x": 50.0, "y": 50.0}]
        result = stamp_image(img, stamps)
        output_img = Image.open(io.BytesIO(result))
        assert output_img.format == "PNG"

    def test_rgba_input_handled(self):
        """RGBA input images are handled correctly."""
        img = Image.new("RGBA", (200, 200), color=(128, 128, 128, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        stamps = [{"code": "A1", "x": 50.0, "y": 50.0}]
        result = stamp_image(image_bytes, stamps)
        output_img = Image.open(io.BytesIO(result))
        assert output_img.size == (200, 200)


# ── stamp_document ───────────────────────────────────────────────────


class TestStampDocument:
    """Tests for stamp_document (unified interface)."""

    def test_pdf_dispatch(self):
        """PDF filename routes to stamp_pdf and returns PDF."""
        pdf = _make_pdf_bytes()
        stamps = [{"code": "A1", "x": 100.0, "y": 100.0}]
        result_bytes, result_name = stamp_document(pdf, "map.pdf", stamps)
        assert result_name == "map_stamped.pdf"
        # Verify the output is a valid PDF
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        assert doc.page_count == 1
        doc.close()

    def test_png_dispatch(self):
        """PNG filename routes to stamp_image and returns PNG."""
        img = _make_image_bytes(fmt="PNG")
        stamps = [{"code": "A1", "x": 50.0, "y": 50.0}]
        result_bytes, result_name = stamp_document(img, "photo.png", stamps)
        assert result_name == "photo_stamped.png"
        output_img = Image.open(io.BytesIO(result_bytes))
        assert output_img.format == "PNG"

    def test_jpg_dispatch(self):
        """JPG filename routes to stamp_image."""
        img = _make_image_bytes(fmt="JPEG")
        stamps = [{"code": "A1", "x": 50.0, "y": 50.0}]
        result_bytes, result_name = stamp_document(img, "photo.jpg", stamps)
        assert result_name == "photo_stamped.png"

    def test_jpeg_dispatch(self):
        """JPEG filename routes to stamp_image."""
        img = _make_image_bytes(fmt="JPEG")
        stamps = [{"code": "A1", "x": 50.0, "y": 50.0}]
        result_bytes, result_name = stamp_document(img, "photo.jpeg", stamps)
        assert result_name == "photo_stamped.png"

    def test_case_insensitive_extension(self):
        """Extension matching is case-insensitive."""
        pdf = _make_pdf_bytes()
        stamps = [{"code": "A1", "x": 100.0, "y": 100.0}]
        result_bytes, result_name = stamp_document(pdf, "MAP.PDF", stamps)
        assert result_name == "MAP_stamped.pdf"

    def test_unsupported_extension_raises(self):
        """Unsupported file extension raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            stamp_document(b"data", "file.bmp", [])

    def test_unsupported_tiff_raises(self):
        """TIFF is not supported (only pdf, png, jpg, jpeg)."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            stamp_document(b"data", "file.tiff", [])

    def test_no_extension_raises(self):
        """File without extension raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            stamp_document(b"data", "noextension", [])

    def test_empty_stamps_pdf(self):
        """Empty stamp list on PDF returns valid document."""
        pdf = _make_pdf_bytes()
        result_bytes, result_name = stamp_document(pdf, "doc.pdf", [])
        assert result_name == "doc_stamped.pdf"
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        assert doc.page_count == 1
        doc.close()

    def test_empty_stamps_image(self):
        """Empty stamp list on image returns valid image."""
        img = _make_image_bytes()
        result_bytes, result_name = stamp_document(img, "photo.png", [])
        assert result_name == "photo_stamped.png"
        output_img = Image.open(io.BytesIO(result_bytes))
        assert output_img.size == (200, 200)


# ── PDF Rotation ────────────────────────────────────────────────────


class TestStampPdfRotation:
    """Tests for stamp_pdf with rotated pages."""

    def test_rotation_90_text_present(self):
        """Stamp text is present on a page with /Rotate=90."""
        pdf = _make_pdf_bytes(rotation=90)
        stamps = [{"code": "R90", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "R90" in text

    def test_rotation_180_text_present(self):
        """Stamp text is present on a page with /Rotate=180."""
        pdf = _make_pdf_bytes(rotation=180)
        stamps = [{"code": "R180", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "R180" in text

    def test_rotation_270_text_present(self):
        """Stamp text is present on a page with /Rotate=270."""
        pdf = _make_pdf_bytes(rotation=270)
        stamps = [{"code": "R270", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "R270" in text

    def test_rotation_0_unchanged(self):
        """Rotation=0 produces identical behavior to default."""
        pdf = _make_pdf_bytes(rotation=0)
        stamps = [{"code": "X1", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "X1" in text

    def test_rotation_90_stamp_color_is_red(self):
        """Stamp text on a rotated page is still red."""
        pdf = _make_pdf_bytes(rotation=90)
        stamps = [{"code": "A1", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        page = doc[0]
        text_dict = page.get_text("dict")
        stamp_color = None
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() == "A1":
                            stamp_color = span["color"]
        doc.close()
        assert stamp_color is not None, "Stamp text 'A1' not found"
        assert stamp_color == 0xFF0000

    def test_rotation_90_clamping(self):
        """Stamps near edges are clamped on a rotated page."""
        pdf = _make_pdf_bytes(width=200, height=200, rotation=90)
        stamps = [{"code": "CL", "x": 999.0, "y": 999.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        assert "CL" in text


# ── StampStyle ──────────────────────────────────────────────────────


class TestStampStyle:
    """Tests for configurable stamp appearance."""

    def test_default_style_pdf_is_red(self):
        """Default style produces red text on PDF."""
        pdf = _make_pdf_bytes()
        stamps = [{"code": "A1", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps)
        doc = fitz.open(stream=result, filetype="pdf")
        text_dict = doc[0].get_text("dict")
        stamp_color = None
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() == "A1":
                            stamp_color = span["color"]
        doc.close()
        assert stamp_color == 0xFF0000

    def test_custom_style_pdf_color(self):
        """Custom blue text color is applied to PDF stamps."""
        style = StampStyle(text_color=(0.0, 0.0, 1.0))
        pdf = _make_pdf_bytes()
        stamps = [{"code": "B1", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps, style=style)
        doc = fitz.open(stream=result, filetype="pdf")
        text_dict = doc[0].get_text("dict")
        stamp_color = None
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() == "B1":
                            stamp_color = span["color"]
        doc.close()
        assert stamp_color == 0x0000FF

    def test_custom_style_pdf_fontsize(self):
        """Custom font size is applied to PDF stamps."""
        style = StampStyle(fontsize=24)
        pdf = _make_pdf_bytes()
        stamps = [{"code": "F1", "x": 100.0, "y": 100.0}]
        result = stamp_pdf(pdf, stamps, style=style)
        doc = fitz.open(stream=result, filetype="pdf")
        text_dict = doc[0].get_text("dict")
        found_size = None
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() == "F1":
                            found_size = span["size"]
        doc.close()
        assert found_size is not None
        assert abs(found_size - 24) < 1

    def test_custom_style_image_returns_valid(self):
        """Custom style on image stamping produces valid output."""
        style = StampStyle(
            fontsize=20,
            text_color=(0.0, 1.0, 0.0),
            bg_color=(0.0, 0.0, 0.0),
            bg_opacity=0.5,
            padding=5,
        )
        img = _make_image_bytes()
        stamps = [{"code": "S1", "x": 50.0, "y": 50.0}]
        result = stamp_image(img, stamps, style=style)
        output_img = Image.open(io.BytesIO(result))
        assert output_img.size == (200, 200)

    def test_style_passed_through_stamp_document(self):
        """StampStyle is passed through stamp_document to the underlying stamper."""
        style = StampStyle(text_color=(0.0, 0.0, 1.0))
        pdf = _make_pdf_bytes()
        stamps = [{"code": "D1", "x": 100.0, "y": 100.0}]
        result_bytes, _ = stamp_document(pdf, "test.pdf", stamps, style=style)
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        text_dict = doc[0].get_text("dict")
        stamp_color = None
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() == "D1":
                            stamp_color = span["color"]
        doc.close()
        assert stamp_color == 0x0000FF
