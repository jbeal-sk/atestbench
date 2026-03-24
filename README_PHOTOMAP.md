# Photo Map Stamping & Markdown Report

## Overview

This feature extends the existing Photo GPS to Google Earth KML application with two new capabilities:

1. **Photo Code Assignment & Markdown Report** — Each uploaded photo is assigned a unique 2-digit alphanumeric code (e.g., "A1", "B3"). A downloadable markdown report links each code to its filename and capture date/time.

2. **Photo Map Stamping** — Upload a site map, aerial photo, or survey document (PDF or image). Define its geographic extent by providing coordinates for 3 corners. The app computes the 4th corner, maps each photo's GPS location onto the document, and stamps the alphanumeric code at the correct position.

The result: a document with labeled points showing exactly where each photo was taken, cross-referenced to the markdown report for full details.

---

## New Dependencies

| Package | Purpose |
|---------|---------|
| PyMuPDF (fitz) | Vector text placement on existing PDFs |
| numpy | Affine transformation matrix computation |

Install with:
```bash
pip install -r requirements.txt
```

---

## Application Workflow

The app now has two tabs: **KML Export** (original functionality) and **Photo Map** (new).

### Shared Step: Upload Photos

Both tabs share the same photo upload at the top of the app. Upload one or more geotagged photos (.jpg, .jpeg, .tiff, .png). The app extracts:
- GPS coordinates (latitude/longitude) from EXIF data
- Capture date/time from EXIF `DateTimeOriginal`
- Assigns a unique 2-digit alphanumeric code to each photo

### Tab 1: KML Export (Unchanged)

The original workflow: preview locations on an interactive map, download a KML file for Google Earth. Photo codes now appear in KML point descriptions for cross-referencing.

### Tab 2: Photo Map

#### Step 1 — Review Photo Table & Download Report

A table displays all uploaded photos with their assigned codes, GPS coordinates, and capture timestamps. Download the **Markdown Report** for a portable reference document.

The markdown report format:

```markdown
# Photo Location Report

| Code | Filename        | Date/Time           |
|------|-----------------|---------------------|
| A1   | IMG_001.jpg     | 2024-03-15 14:30:22 |
| A2   | IMG_002.jpg     | 2024-03-15 14:32:10 |
| A3   | IMG_003.jpg     | No date available   |

Generated on 2026-03-24
```

#### Step 2 — Upload Base Document

Upload the document that represents your geographic area:
- **PDF** — Site maps, survey plats, engineering drawings. Codes are stamped as vector text (scalable, searchable).
- **PNG / JPG** — Aerial photos, satellite imagery, scanned maps. Codes are stamped as raster text.

#### Step 3 — Define Geographic Extent

Select which 3 of the 4 corners you will provide:
- Top-Left, Top-Right, Bottom-Left
- Top-Left, Top-Right, Bottom-Right
- Top-Left, Bottom-Left, Bottom-Right
- Top-Right, Bottom-Left, Bottom-Right

Enter the latitude and longitude for each selected corner. The app computes the 4th corner using the parallelogram property (D = A + C - B) and displays it for verification.

**Corner labeling convention:**
```
Top-Left ─────── Top-Right
    │                 │
    │    Document     │
    │                 │
Bottom-Left ──── Bottom-Right
```

#### Step 4 — Stamp & Download

Click **"Stamp Document"**. The app:

1. Builds an affine transformation mapping geographic coordinates to page/pixel coordinates
2. Tests each photo's GPS position against the document's geographic bounds
3. Stamps the alphanumeric code at the mapped position for every photo within bounds
4. Reports how many photos were stamped vs. excluded (outside bounds)

Download the stamped document. PDF output retains vector text; image output is PNG.

---

## Technical Details

### Alphanumeric Code Assignment

Codes use one letter (A-Z) followed by one digit (1-9, then 0):
```
A1, A2, A3, ... A9, A0, B1, B2, ... Z9, Z0
```
This provides 260 unique codes — sufficient for any practical photo batch.

### Affine Coordinate Transformation

The mapping from geographic space (lat/lon) to document space (page points or pixels) is an affine transformation:

```
x_page = a * lon + b * lat + c
y_page = d * lon + e * lat + f
```

Three known corner correspondences (geographic coordinates paired with their page positions) fully determine the six unknowns. The system is solved via numpy's linear algebra routines.

**Document coordinate systems:**
- **PDF (PyMuPDF):** Origin at top-left, y increases downward, units in points (1/72 inch)
- **Images (Pillow):** Origin at top-left, y increases downward, units in pixels

Both use top-left origin, so the affine transform works identically for both formats.

### 4th Corner Computation

Given three corners A, B, C of a parallelogram where B is the corner diagonally opposite the unknown corner D:

```
D_lat = A_lat + C_lat - B_lat
D_lon = A_lon + C_lon - B_lon
```

This leverages the property that diagonals of a parallelogram bisect each other.

### Bounds Checking

A point-in-polygon test determines whether each photo's GPS coordinates fall within the quadrilateral defined by the 4 corners. Photos outside the bounds are excluded from stamping but still appear in the markdown report.

### PDF vs. Image: Format Considerations

| Aspect | PDF | Image |
|--------|-----|-------|
| Text type | Vector (scalable) | Raster (fixed resolution) |
| Text searchability | Yes | No |
| File size impact | Minimal increase | Moderate increase |
| Quality at zoom | Perfect at any zoom | Degrades at high zoom |
| Library | PyMuPDF (fitz) | Pillow |

**Recommendation:** Use PDF when available. Vector text remains crisp at any zoom level and is searchable/selectable.

---

## Limitations

- **Single page only:** For multi-page PDFs, only the first page is stamped.
- **Parallelogram assumption:** The 4th corner is computed assuming the document represents a parallelogram (which includes rectangles). Trapezoidal or perspective-distorted documents would require a projective transform (not supported).
- **Small area approximation:** The affine transform treats lat/lon as a Cartesian grid. This is accurate for areas up to a few kilometers. For very large areas, distortion from Earth's curvature may affect placement accuracy.
- **EXIF dependency:** Photos must contain EXIF GPS tags (typically from smartphones or GPS-enabled cameras). Photos without GPS data receive codes but cannot be placed on the map.

---

## File Structure

```
atestbench/
├── app.py                          # Streamlit UI with KML Export and Photo Map tabs
├── gps_extractor.py                # EXIF GPS + DateTime extraction
├── kml_generator.py                # KML file generation
├── code_assigner.py                # 2-digit alphanumeric code assignment
├── markdown_report.py              # Markdown report generation
├── affine_transform.py             # Geographic-to-page coordinate mapping
├── document_stamper.py             # PDF and image text stamping
├── requirements.txt                # Python dependencies
├── README.md                       # Project overview and setup
├── README_PHOTOMAP.md              # This file — Photo Map feature documentation
├── AGENT_README.md                 # Implementation agent breakdown
└── tests/
    ├── __init__.py
    ├── test_affine_transform.py    # Affine transform unit tests
    ├── test_code_assigner.py       # Code assignment unit tests
    ├── test_document_stamper.py    # Document stamper unit tests
    ├── test_gps_extractor.py       # GPS/metadata extraction unit tests
    └── test_markdown_report.py     # Markdown report unit tests
```
