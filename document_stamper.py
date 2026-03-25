"""Document Stamper — renders alphanumeric codes onto PDFs and images.

Provides two code paths behind a unified interface:
- PDF: vector text placement via PyMuPDF (fitz)
- Image: raster text placement via Pillow
"""

from dataclasses import dataclass, field
from io import BytesIO
import os

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

# ── Constants ────────────────────────────────────────────────────────

_PDF_FONT = "Helvetica-Bold"

_SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


@dataclass
class StampStyle:
    """Configurable appearance for document stamps.

    Colors are normalized 0.0–1.0 RGB tuples (converted internally
    to 0–255 for image stamping).
    """

    fontsize: float = 12
    text_color: tuple = (1.0, 0.0, 0.0)  # red
    bg_color: tuple = (1.0, 1.0, 1.0)    # white
    bg_opacity: float = 1.0               # 0.0–1.0
    padding: float = 2                    # points / pixels


_DEFAULT_STYLE = StampStyle()


def stamp_pdf(
    pdf_bytes: bytes, stamps: list[dict], style: StampStyle | None = None
) -> bytes:
    """Stamp alphanumeric codes onto page 0 of a PDF document.

    For each stamp, draws a background rectangle behind the text
    for readability, then inserts the code as vector text.

    Handles PDF pages with non-zero ``/Rotate`` by transforming
    visual-space coordinates into the internal (unrotated) coordinate
    system used by PyMuPDF drawing operations.

    Args:
        pdf_bytes: Raw bytes of the source PDF.
        stamps: List of dicts, each with keys ``"code"`` (str),
                ``"x"`` (float), and ``"y"`` (float) in *visual*
                page points (i.e. post-rotation coordinates).
        style: Optional :class:`StampStyle` controlling appearance.

    Returns:
        Modified PDF as bytes.
    """
    if style is None:
        style = _DEFAULT_STYLE

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    page_rect = page.rect  # visual (post-rotation) rectangle

    # ── Rotation handling ────────────────────────────────────────────
    rotation = page.rotation  # 0, 90, 180, or 270
    derotation_matrix = page.derotation_matrix

    if rotation:
        unrotated_rect = page_rect * derotation_matrix
        unrotated_rect.normalize()
    else:
        unrotated_rect = page_rect

    for stamp in stamps:
        code = stamp["code"]
        x = stamp["x"]
        y = stamp["y"]

        # Measure text to size the background rectangle
        text_length = fitz.get_text_length(
            code, fontname=_PDF_FONT, fontsize=style.fontsize
        )
        text_height = style.fontsize

        # Transform visual-space point to internal (unrotated) space
        if rotation:
            internal_pt = fitz.Point(x, y) * derotation_matrix
            ix, iy = internal_pt.x, internal_pt.y
        else:
            ix, iy = x, y

        # Clamp position so text stays within unrotated page bounds
        ix = max(
            unrotated_rect.x0,
            min(ix, unrotated_rect.x1 - text_length - style.padding),
        )
        iy = max(
            unrotated_rect.y0 + text_height + style.padding,
            min(iy, unrotated_rect.y1 - style.padding),
        )

        # Background rectangle in visual space, then transform
        bg_visual = fitz.Rect(
            x - style.padding,
            y - text_height - style.padding,
            x + text_length + style.padding,
            y + style.padding,
        )
        if rotation:
            bg_rect = bg_visual * derotation_matrix
            bg_rect.normalize()
        else:
            bg_rect = bg_visual

        bg_fill = style.bg_color
        page.draw_rect(bg_rect, color=None, fill=bg_fill)

        # Insert text (rotate so it appears upright in the viewer)
        page.insert_text(
            fitz.Point(ix, iy),
            code,
            fontname=_PDF_FONT,
            fontsize=style.fontsize,
            color=style.text_color,
            rotate=rotation,
        )

    result = doc.tobytes()
    doc.close()
    return result


def stamp_image(
    image_bytes: bytes, stamps: list[dict], style: StampStyle | None = None
) -> bytes:
    """Stamp alphanumeric codes onto an image.

    For each stamp, draws a background rectangle behind the text
    for readability, then draws the code as raster text.

    Args:
        image_bytes: Raw bytes of the source image (PNG/JPEG).
        stamps: List of dicts, each with keys ``"code"`` (str),
                ``"x"`` (float), and ``"y"`` (float) in pixels.
        style: Optional :class:`StampStyle` controlling appearance.

    Returns:
        Modified image as PNG bytes.
    """
    if style is None:
        style = _DEFAULT_STYLE

    image = Image.open(BytesIO(image_bytes))

    # Ensure we work in RGBA for compositing the semi-transparent background
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Create an overlay for the background rectangles
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Convert normalized 0-1 colors to 0-255
    text_rgba = tuple(int(c * 255) for c in style.text_color) + (255,)
    bg_rgba = tuple(int(c * 255) for c in style.bg_color) + (
        int(style.bg_opacity * 255),
    )

    # Try to load a bold truetype font; fall back to default bitmap font
    fontsize = int(style.fontsize)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", fontsize)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize
            )
        except (OSError, IOError):
            font = ImageFont.load_default()

    img_width, img_height = image.size
    pad = int(style.padding)

    for stamp in stamps:
        code = stamp["code"]
        x = stamp["x"]
        y = stamp["y"]

        # Measure text bounding box
        bbox = overlay_draw.textbbox((0, 0), code, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Clamp position so text stays within image bounds
        x = max(0, min(x, img_width - text_w - pad * 2))
        y = max(0, min(y, img_height - text_h - pad * 2))

        # Draw background rectangle on the overlay
        bg_rect = [
            x - pad,
            y - pad,
            x + text_w + pad,
            y + text_h + pad,
        ]
        overlay_draw.rectangle(bg_rect, fill=bg_rgba)

        # Draw text on the overlay
        overlay_draw.text((x, y), code, fill=text_rgba, font=font)

    # Composite overlay onto the original image
    image = Image.alpha_composite(image, overlay)

    # Save as PNG
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def stamp_document(
    file_bytes: bytes,
    filename: str,
    stamps: list[dict],
    style: StampStyle | None = None,
) -> tuple[bytes, str]:
    """Stamp alphanumeric codes onto a document (PDF or image).

    Dispatches to :func:`stamp_pdf` or :func:`stamp_image` based on the
    file extension.

    Args:
        file_bytes: Raw bytes of the source document.
        filename: Original filename, used to determine the file type.
        stamps: List of dicts, each with keys ``"code"`` (str),
                ``"x"`` (float), and ``"y"`` (float).
        style: Optional :class:`StampStyle` controlling appearance.

    Returns:
        A tuple of (output_bytes, output_filename).

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        output_bytes = stamp_pdf(file_bytes, stamps, style=style)
        output_filename = os.path.splitext(filename)[0] + "_stamped.pdf"
    elif ext in _SUPPORTED_IMAGE_EXTENSIONS:
        output_bytes = stamp_image(file_bytes, stamps, style=style)
        # Image output is always PNG regardless of input format
        output_filename = os.path.splitext(filename)[0] + "_stamped.png"
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported types: .pdf, .png, .jpg, .jpeg"
        )

    return (output_bytes, output_filename)
