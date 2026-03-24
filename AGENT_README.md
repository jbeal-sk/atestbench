# Agent Implementation Breakdown

## Scope of Modifications

The existing Photo GPS to KML application is being extended with **Photo Map Stamping** and **Markdown Report** features. This document breaks the implementation into seven discrete agents, each responsible for a self-contained piece of the system. Agents are organized into phases based on their dependencies.

---

## Dependency Graph

```
Phase 1 (parallel):  Dorothy + Betty
Phase 2 (parallel):  Mildred + Helen
Phase 3:             Ruth
Phase 4:             Virginia
Phase 5:             Margaret

Dorothy ──→ Mildred
Betty   ──→ Helen
Dorothy + Mildred + Betty + Helen ──→ Ruth
All ──→ Virginia ──→ Margaret
```

---

## Phase 1: Foundation

### Dorothy — Code Assignment & Metadata Extraction

**Namesake era:** Dorothy was the 2nd most popular girls' name in the 1930s.

**Scope:** Dorothy lays the data foundation. She creates the alphanumeric code assignment system and extends the existing GPS extractor to also pull capture date/time from EXIF metadata. She also fixes a known bug (duplicate function definition in `gps_extractor.py`).

**Files:**
| Action | File |
|--------|------|
| Create | `code_assigner.py` |
| Modify | `gps_extractor.py` |

**Detailed Tasks:**

1. **Create `code_assigner.py`** with function `assign_codes(photo_names: list[str]) -> dict[str, str]`
   - Assigns codes sequentially: A1, A2, ... A9, A0, B1, B2, ... Z9, Z0
   - Returns a dictionary mapping filename to its assigned code
   - Handles edge cases: empty list returns empty dict; more than 260 photos raises ValueError

2. **Modify `gps_extractor.py`**
   - Add function `extract_metadata(image_file) -> dict` that returns `{"lat": float|None, "lon": float|None, "datetime": str|None}`
   - DateTime extraction reads EXIF tag 36867 (`DateTimeOriginal`), falling back to tag 306 (`DateTime`)
   - Update `extract_gps_from_files()` to include `"datetime"` key in each result dict
   - Remove the duplicate definition of `extract_gps_from_files` (currently defined twice, lines ~61-78 and ~82-99)
   - Preserve `extract_gps()` for backward compatibility

**Dependencies:** None. Dorothy starts first.

**Acceptance Criteria:**
- `assign_codes(["a.jpg", "b.jpg", "c.jpg"])` returns `{"a.jpg": "A1", "b.jpg": "A2", "c.jpg": "A3"}`
- `assign_codes([])` returns `{}`
- Code sequence wraps correctly: after A9 comes A0, then B1
- `extract_gps_from_files()` returns dicts with `"datetime"` key
- The duplicate function definition is eliminated
- Existing `extract_gps()` still works unchanged

---

### Betty — Affine Transform Engine

**Namesake era:** Betty was the 5th most popular girls' name in the 1930s.

**Scope:** Betty builds the mathematical core that translates between geographic coordinates (latitude/longitude) and document coordinates (page points or pixels). She handles 4th corner computation, affine matrix construction, coordinate transformation, and bounds checking.

**Files:**
| Action | File |
|--------|------|
| Create | `affine_transform.py` |

**Detailed Tasks:**

1. **`compute_fourth_corner(corners: dict, missing: str) -> tuple[float, float]`**
   - Input: dict with 3 of 4 keys ("TL", "TR", "BL", "BR"), each mapping to (lat, lon); `missing` identifies which key is absent
   - Uses parallelogram property: D = A + C - B, where B is diagonal to D
   - Returns the (lat, lon) of the missing corner

2. **`build_affine_transform(geo_points: list[tuple], page_points: list[tuple]) -> np.ndarray`**
   - Takes 3+ pairs of (lat, lon) and their corresponding (x_page, y_page)
   - Sets up and solves the 6-unknown linear system using `np.linalg.solve`
   - Returns a 2x3 numpy array representing the affine matrix
   - Raises `ValueError` if the system is degenerate (collinear points)

3. **`geo_to_page(lat: float, lon: float, affine_matrix: np.ndarray) -> tuple[float, float]`**
   - Applies the affine matrix to transform a geographic point to page coordinates
   - Returns (x_page, y_page)

4. **`is_within_bounds(lat: float, lon: float, corners: list[tuple]) -> bool`**
   - Point-in-polygon test against the quadrilateral defined by 4 (lat, lon) corners
   - Uses cross-product winding number method (reliable for convex polygons)
   - Returns True if the point is inside or on the boundary

**Dependencies:** None. Betty starts in parallel with Dorothy.

**Acceptance Criteria:**
- Given corners TL=(1,1), TR=(1,3), BL=(3,1), missing BR → computes (3,3)
- Affine transform maps the 3 input geo points back to their page points with error < 0.01
- `is_within_bounds` returns True for the center of a known rectangle and False for a point clearly outside
- `ValueError` raised when 3 corners are collinear
- All functions handle floating-point edge cases gracefully

---

## Phase 2: Generators

### Mildred — Markdown Report Generator

**Namesake era:** Mildred was the 6th most popular girls' name in the 1930s.

**Scope:** Mildred creates the markdown report module that produces a formatted table linking each photo's alphanumeric code to its filename and capture timestamp. The report serves as the legend/key for the stamped photo map.

**Files:**
| Action | File |
|--------|------|
| Create | `markdown_report.py` |

**Detailed Tasks:**

1. **`generate_markdown_report(photo_data: list[dict]) -> str`**
   - Input: list of dicts, each with keys `"name"`, `"lat"`, `"lon"`, `"datetime"`, `"code"`
   - Produces a markdown string with:
     - Title: `# Photo Location Report`
     - Table columns: Code, Filename, Date/Time, Coordinates
     - Photos without datetime shown as "No date available"
     - Photos without GPS shown as "No GPS" in coordinates column
     - Footer with generation date
   - Codes sorted in assignment order (A1, A2, A3...)

**Dependencies:** Dorothy (needs the enriched data structure with datetime and code fields).

**Acceptance Criteria:**
- Output is valid markdown that renders correctly
- Table includes all photos regardless of GPS/datetime availability
- Missing datetime displays "No date available"
- Missing GPS displays "No GPS" in coordinates
- Generation date appears in footer
- Output string is ready for `st.download_button()` consumption

---

### Helen — Document Stamper

**Namesake era:** Helen was the 4th most popular girls' name in the 1930s.

**Scope:** Helen builds the rendering engine that stamps alphanumeric codes onto documents. She handles two code paths — PDF (vector text via PyMuPDF) and images (raster text via Pillow) — behind a unified interface.

**Files:**
| Action | File |
|--------|------|
| Create | `document_stamper.py` |

**Detailed Tasks:**

1. **`stamp_pdf(pdf_bytes: bytes, stamps: list[dict]) -> bytes`**
   - Opens PDF from bytes using `fitz.open(stream=pdf_bytes, filetype="pdf")`
   - For each stamp `{"code": "A1", "x": float, "y": float}`:
     - Draws a small white/light background rectangle behind the text for readability
     - Inserts text using `page.insert_text()` with Helvetica-Bold, 12pt
   - Works on page 0 only
   - Returns modified PDF as bytes

2. **`stamp_image(image_bytes: bytes, stamps: list[dict]) -> bytes`**
   - Opens image using `Image.open(BytesIO(image_bytes))`
   - Creates `ImageDraw.Draw` object
   - For each stamp:
     - Calculates text bounding box for background rectangle sizing
     - Draws white/light background rectangle
     - Draws text in bold, dark color at (x, y)
   - Returns modified image as PNG bytes

3. **`stamp_document(file_bytes: bytes, filename: str, stamps: list[dict]) -> tuple[bytes, str]`**
   - Detects file type from extension (.pdf → PDF path; .png/.jpg/.jpeg → image path)
   - Dispatches to `stamp_pdf` or `stamp_image`
   - Returns (output_bytes, output_filename)
   - Raises `ValueError` for unsupported file types

**Dependencies:** Betty's module provides the page coordinates, but Helen's functions accept pre-computed (x, y) positions — no direct import dependency. Helen can work in parallel with Mildred.

**Acceptance Criteria:**
- PDF output opens in a PDF viewer without corruption
- Image output opens in an image viewer without corruption
- Text is readable against varied backgrounds (light and dark regions)
- Background rectangles provide sufficient contrast
- Stamps near page edges are clamped so text remains fully visible
- Original document content is preserved (not overwritten or degraded)
- Unsupported file types raise clear error

---

## Phase 3: Integration

### Ruth — Streamlit UI Integration

**Namesake era:** Ruth was the 3rd most popular girls' name in the 1930s.

**Scope:** Ruth is the integrator. She restructures `app.py` to add the Photo Map tab alongside the existing KML Export tab, wires together all new modules, and builds the complete user-facing workflow. Ruth touches only `app.py` but depends on every other agent's output.

**Files:**
| Action | File |
|--------|------|
| Modify | `app.py` |

**Detailed Tasks:**

1. **Restructure app with `st.tabs()`**
   - Move photo upload and GPS extraction to top-level (shared between tabs)
   - Add code assignment at top-level after GPS extraction
   - Create two tabs: "KML Export" and "Photo Map"

2. **KML Export tab** (preserve existing behavior)
   - Move existing map preview, results table, and KML download into tab 1
   - Add code column to the results table
   - Include codes in KML point descriptions

3. **Photo Map tab** — build the full workflow:
   - Display enriched photo table (code, filename, datetime, lat, lon)
   - Markdown report download button
   - Base document uploader (accepts .pdf, .png, .jpg, .jpeg)
   - Corner selection: `st.selectbox` to choose which 3 corners to provide
   - 3 sets of `st.number_input` widgets for lat/lon (precision to 6 decimal places)
   - "Compute 4th Corner" display showing the calculated result
   - "Stamp Document" button that:
     - Calls `compute_fourth_corner()`
     - Determines page dimensions (from PDF page rect or image size)
     - Constructs geo-to-page point pairs from corners
     - Calls `build_affine_transform()`
     - Maps each photo's GPS through the transform
     - Filters to within-bounds photos via `is_within_bounds()`
     - Calls `stamp_document()` with the computed stamps
   - Status display: "X of Y photos stamped (Z outside document bounds)"
   - Download button for stamped document

4. **Input validation:**
   - Lat in [-90, 90], lon in [-180, 180]
   - At least one photo must have GPS data
   - Base document must be uploaded before stamping
   - Non-degenerate corner check (catches collinear points with clear error message)

**Dependencies:** Dorothy, Mildred, Betty, Helen (all modules must exist).

**Acceptance Criteria:**
- `streamlit run app.py` launches without errors
- Two tabs visible: "KML Export" and "Photo Map"
- KML Export tab works identically to current behavior (no regression)
- Photo Map tab completes the full workflow: upload → configure → stamp → download
- All error states show clear, user-friendly messages
- Corner coordinate inputs default to 0.0 with appropriate step size (0.000001)
- Stamped document downloads with correct filename and content type

---

## Phase 4: Documentation

### Virginia — Requirements & Documentation

**Namesake era:** Virginia was the 8th most popular girls' name in the 1930s.

**Scope:** Virginia handles all documentation and dependency management. She updates `requirements.txt` with new packages and creates the two documentation files that describe the feature set and implementation structure.

**Files:**
| Action | File |
|--------|------|
| Modify | `requirements.txt` |
| Create | `README_PHOTOMAP.md` |
| Create | `AGENT_README.md` |

**Detailed Tasks:**

1. **Update `requirements.txt`**
   - Add `PyMuPDF>=1.23.0`
   - Add `numpy>=1.24.0`
   - Preserve existing dependencies (streamlit, Pillow, simplekml, pandas)

2. **Create `README_PHOTOMAP.md`**
   - Feature overview and motivation
   - Installation/setup instructions
   - Step-by-step usage guide for both tabs
   - Technical details: affine transform, code assignment scheme, coordinate systems
   - Format comparison (PDF vs. image)
   - Limitations and constraints

3. **Create `AGENT_README.md`**
   - This document — scope of modifications, agent breakdown, dependency graph

**Dependencies:** All other agents (Virginia documents the final state).

**Acceptance Criteria:**
- `pip install -r requirements.txt` succeeds and installs all needed packages
- Both markdown files render correctly with no broken formatting
- README_PHOTOMAP.md covers the complete user workflow
- AGENT_README.md accurately reflects the implementation structure

---

## Phase 5: Validation

### Margaret — Testing & Quality Assurance

**Namesake era:** Margaret was the 7th most popular girls' name in the 1930s.

**Scope:** Margaret is the final gatekeeper. She performs end-to-end testing of the complete system, verifies edge cases, and fixes any integration bugs discovered during testing. Margaret may touch any file to resolve issues.

**Files:**
| Action | File |
|--------|------|
| Create | `tests/` directory with test files (if needed) |
| Modify | Any file (bug fixes only) |

**Detailed Tasks:**

1. **Code assignment tests**
   - 0 photos → empty dict
   - 1 photo → single code "A1"
   - 10 photos → correct sequential codes
   - 260 photos → all codes A1 through Z0 assigned
   - 261 photos → ValueError raised

2. **Metadata extraction tests**
   - Photo with GPS + datetime → all fields populated
   - Photo with GPS, no datetime → datetime is None
   - Photo without GPS → lat and lon are None
   - Non-image file → graceful failure

3. **Affine transform tests**
   - Known rectangle: verify transform maps corners exactly
   - Verify round-trip accuracy (geo → page → geo) with error < 0.01
   - Collinear points → ValueError
   - Point inside bounds → True; point outside → False

4. **Document stamping tests**
   - Stamp a test PDF → output opens in viewer, text present
   - Stamp a test image → output opens in viewer, text visible
   - Zero stamps → document returned unchanged
   - Stamps at edge positions → text clamped within bounds

5. **Integration test**
   - `streamlit run app.py` → app loads with both tabs
   - KML Export tab → no regression from current behavior
   - Full Photo Map workflow → stamp and download succeed

6. **Bug fix duty**
   - Fix any issues found during testing
   - Verify the duplicate function bug in `gps_extractor.py` is resolved

**Dependencies:** All other agents (Margaret tests the integrated system).

**Acceptance Criteria:**
- All test scenarios pass
- No Python errors or unhandled exceptions in normal workflow
- No regression in KML Export functionality
- Stamped documents are valid and visually correct
- Edge cases handled gracefully with user-friendly error messages
