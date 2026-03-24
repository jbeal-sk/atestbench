"""Document Stamper — renders alphanumeric codes onto PDFs and images.

Provides two code paths behind a unified interface:
- PDF: vector text placement via PyMuPDF (fitz)
- Image: raster text placement via Pillow
"""

from io import BytesIO
import os

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

# ── Constants ────────────────────────────────────────────────────────

_PDF_FONT = "Helvetica-Bold"
_PDF_FONTSIZE = 12
_PDF_TEXT_COLOR = (0, 0, 0)  # black
_PDF_BG_COLOR = (1, 1, 1)  # white
_PDF_BG_PADDING = 2  # points of padding around text

_IMG_FONTSIZE = 16
_IMG_TEXT_COLOR = (0, 0, 0)  # black
_IMG_BG_COLOR = (255, 255, 255, 200)  # semi-transparent white
_IMG_BG_PADDING = 3  # pixels of padding around text

_SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def stamp_pdf(pdf_bytes: bytes, stamps: list[dict]) -> bytes:
    """Stamp alphanumeric codes onto page 0 of a PDF document.

    For each stamp, draws a white background rectangle behind the text
    for readability, then inserts the code as vector text.

    Args:
        pdf_bytes: Raw bytes of the source PDF.
        stamps: List of dicts, each with keys ``"code"`` (str),
                ``"x"`` (float), and ``"y"`` (float) in page points.

    Returns:
        Modified PDF as bytes.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    page_rect = page.rect  # (x0, y0, x1, y1) of the page

    for stamp in stamps:
        code = stamp["code"]
        x = stamp["x"]
        y = stamp["y"]

        # Measure text to size the background rectangle
        text_length = fitz.get_text_length(
            code, fontname=_PDF_FONT, fontsize=_PDF_FONTSIZE
        )
        text_height = _PDF_FONTSIZE

        # Clamp position so text stays within page bounds
        x = max(0, min(x, page_rect.width - text_length - _PDF_BG_PADDING))
        y = max(text_height + _PDF_BG_PADDING, min(y, page_rect.height - _PDF_BG_PADDING))

        # Background rectangle (slightly larger than the text)
        bg_rect = fitz.Rect(
            x - _PDF_BG_PADDING,
            y - text_height - _PDF_BG_PADDING,
            x + text_length + _PDF_BG_PADDING,
            y + _PDF_BG_PADDING,
        )

        page.draw_rect(bg_rect, color=None, fill=_PDF_BG_COLOR)

        # Insert text
        page.insert_text(
            fitz.Point(x, y),
            code,
            fontname=_PDF_FONT,
            fontsize=_PDF_FONTSIZE,
            color=_PDF_TEXT_COLOR,
        )

    result = doc.tobytes()
    doc.close()
    return result


def stamp_image(image_bytes: bytes, stamps: list[dict]) -> bytes:
    """Stamp alphanumeric codes onto an image.

    For each stamp, draws a semi-transparent white background rectangle
    behind the text for readability, then draws the code as raster text.

    Args:
        image_bytes: Raw bytes of the source image (PNG/JPEG).
        stamps: List of dicts, each with keys ``"code"`` (str),
                ``"x"`` (float), and ``"y"`` (float) in pixels.

    Returns:
        Modified image as PNG bytes.
    """
    image = Image.open(BytesIO(image_bytes))

    # Ensure we work in RGBA for compositing the semi-transparent background
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Create an overlay for the background rectangles
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Try to load a bold truetype font; fall back to default bitmap font
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", _IMG_FONTSIZE)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", _IMG_FONTSIZE)
        except (OSError, IOError):
            font = ImageFont.load_default()

    img_width, img_height = image.size

    for stamp in stamps:
        code = stamp["code"]
        x = stamp["x"]
        y = stamp["y"]

        # Measure text bounding box
        bbox = overlay_draw.textbbox((0, 0), code, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Clamp position so text stays within image bounds
        x = max(0, min(x, img_width - text_w - _IMG_BG_PADDING * 2))
        y = max(0, min(y, img_height - text_h - _IMG_BG_PADDING * 2))

        # Draw background rectangle on the overlay
        bg_rect = [
            x - _IMG_BG_PADDING,
            y - _IMG_BG_PADDING,
            x + text_w + _IMG_BG_PADDING,
            y + text_h + _IMG_BG_PADDING,
        ]
        overlay_draw.rectangle(bg_rect, fill=_IMG_BG_COLOR)

        # Draw text on the overlay
        overlay_draw.text((x, y), code, fill=(*_IMG_TEXT_COLOR, 255), font=font)

    # Composite overlay onto the original image
    image = Image.alpha_composite(image, overlay)

    # Save as PNG
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def stamp_document(
    file_bytes: bytes, filename: str, stamps: list[dict]
) -> tuple[bytes, str]:
    """Stamp alphanumeric codes onto a document (PDF or image).

    Dispatches to :func:`stamp_pdf` or :func:`stamp_image` based on the
    file extension.

    Args:
        file_bytes: Raw bytes of the source document.
        filename: Original filename, used to determine the file type.
        stamps: List of dicts, each with keys ``"code"`` (str),
                ``"x"`` (float), and ``"y"`` (float).

    Returns:
        A tuple of (output_bytes, output_filename).

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        output_bytes = stamp_pdf(file_bytes, stamps)
        output_filename = os.path.splitext(filename)[0] + "_stamped.pdf"
    elif ext in _SUPPORTED_IMAGE_EXTENSIONS:
        output_bytes = stamp_image(file_bytes, stamps)
        # Image output is always PNG regardless of input format
        output_filename = os.path.splitext(filename)[0] + "_stamped.png"
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported types: .pdf, .png, .jpg, .jpeg"
        )

    return (output_bytes, output_filename)
