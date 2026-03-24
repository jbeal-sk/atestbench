import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

from gps_extractor import extract_gps_from_files
from kml_generator import generate_kml
from code_assigner import assign_codes
from markdown_report import generate_markdown_report
from affine_transform import (
    compute_fourth_corner,
    build_affine_transform,
    geo_to_page,
    is_within_bounds,
)
from document_stamper import stamp_document

st.set_page_config(page_title="Photo GPS → Google Earth KML", page_icon="🌍")

st.title("🌍 Photo GPS → Google Earth KML")
st.write(
    "Upload photos with GPS metadata to extract their coordinates and download a "
    "KML file you can import into [Google Earth Web](https://earth.google.com/web), "
    "or stamp photo codes onto a site map."
)

# ── Shared: Photo Upload ─────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Select photos",
    type=["jpg", "jpeg", "tiff", "png"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info(
        "👆 Upload one or more photos taken with a GPS-enabled camera or smartphone. "
        "The app will extract coordinates from EXIF metadata and generate a KML file."
    )
    st.stop()

# ── Shared: Extract GPS + DateTime ───────────────────────────────────
with st.spinner("Extracting GPS data from photos…"):
    photo_data = extract_gps_from_files(uploaded_files)

# ── Shared: Assign Codes ─────────────────────────────────────────────
code_map = assign_codes([p["name"] for p in photo_data])
for p in photo_data:
    p["code"] = code_map[p["name"]]

# Stats used by both tabs
valid = [p for p in photo_data if p["lat"] is not None and p["lon"] is not None]
invalid = [p for p in photo_data if p["lat"] is None or p["lon"] is None]

# ── Tabs ──────────────────────────────────────────────────────────────
tab_kml, tab_photomap = st.tabs(["KML Export", "Photo Map"])

# ══════════════════════════════════════════════════════════════════════
# Tab 1: KML Export (preserves original behaviour, adds code column)
# ══════════════════════════════════════════════════════════════════════
with tab_kml:
    # Build a results DataFrame
    rows = []
    for p in photo_data:
        if p["lat"] is not None and p["lon"] is not None:
            status = "✅ GPS found"
        else:
            status = "❌ No GPS data"
        rows.append(
            {
                "Code": p["code"],
                "Photo": p["name"],
                "Latitude": p["lat"],
                "Longitude": p["lon"],
                "Status": status,
            }
        )

    df = pd.DataFrame(rows)

    st.subheader("Results")
    st.dataframe(df, use_container_width=True)

    if invalid:
        st.warning(
            f"{len(invalid)} photo(s) had no GPS data and will be excluded from the KML file."
        )

    if not valid:
        st.error(
            "None of the uploaded photos contain GPS data. "
            "Please upload photos taken with a GPS-enabled device."
        )
        st.stop()

    st.success(
        f"{len(valid)} photo(s) with valid GPS coordinates will be included in the KML file."
    )

    # Map preview
    st.subheader("Map Preview")
    map_df = pd.DataFrame(
        [{"lat": p["lat"], "lon": p["lon"]} for p in valid]
    )
    st.map(map_df)

    # KML download — include codes in descriptions
    kml_valid = []
    for p in valid:
        kml_valid.append(
            {
                "name": p["name"],
                "lat": p["lat"],
                "lon": p["lon"],
                "code": p["code"],
            }
        )
    kml_string = generate_kml(kml_valid)

    st.subheader("Download KML")
    st.download_button(
        label="📥 Download KML file",
        data=kml_string,
        file_name="photo_locations.kml",
        mime="application/vnd.google-earth.kml+xml",
    )

    st.caption(
        "Import the KML file into Google Earth Web: "
        "☰ Menu → Projects → New Project → Import KML file from computer."
    )

# ══════════════════════════════════════════════════════════════════════
# Tab 2: Photo Map
# ══════════════════════════════════════════════════════════════════════
with tab_photomap:
    # ── Step 1: Photo Table & Markdown Report ────────────────────────
    st.subheader("📋 Photo Table")
    table_rows = []
    for p in photo_data:
        table_rows.append(
            {
                "Code": p["code"],
                "Filename": p["name"],
                "Date/Time": p.get("datetime") or "No date available",
                "Latitude": p["lat"],
                "Longitude": p["lon"],
            }
        )
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

    md_report = generate_markdown_report(photo_data)
    st.download_button(
        label="📥 Download Markdown Report",
        data=md_report,
        file_name="photo_report.md",
        mime="text/markdown",
        key="md_report_download",
    )

    if not valid:
        st.error(
            "None of the uploaded photos contain GPS data. "
            "Cannot place photos on a map without GPS coordinates."
        )
        st.stop()

    st.info(
        f"{len(valid)} photo(s) have GPS data and can be placed on a map."
    )

    # ── Step 2: Base Document Upload ─────────────────────────────────
    st.subheader("🗺️ Upload Base Document")
    base_doc = st.file_uploader(
        "Upload a site map, aerial photo, or survey document",
        type=["pdf", "png", "jpg", "jpeg"],
        key="base_doc_uploader",
    )

    if not base_doc:
        st.info(
            "👆 Upload a PDF or image document that represents your geographic area."
        )
        st.stop()

    # ── Step 3: Define Geographic Extent ─────────────────────────────
    st.subheader("📐 Define Geographic Extent")

    # Corner selection
    corner_options = {
        "Top-Left, Top-Right, Bottom-Left (compute Bottom-Right)": ("TL", "TR", "BL", "BR"),
        "Top-Left, Top-Right, Bottom-Right (compute Bottom-Left)": ("TL", "TR", "BR", "BL"),
        "Top-Left, Bottom-Left, Bottom-Right (compute Top-Right)": ("TL", "BL", "BR", "TR"),
        "Top-Right, Bottom-Left, Bottom-Right (compute Top-Left)": ("TR", "BL", "BR", "TL"),
    }

    selection = st.selectbox(
        "Which 3 corners will you provide?",
        options=list(corner_options.keys()),
    )

    provided_keys = corner_options[selection][:3]
    missing_key = corner_options[selection][3]

    corner_labels = {"TL": "Top-Left", "TR": "Top-Right", "BL": "Bottom-Left", "BR": "Bottom-Right"}

    corners_input = {}
    for key in provided_keys:
        label = corner_labels[key]
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input(
                f"{label} Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=0.0,
                step=0.000001,
                format="%.6f",
                key=f"lat_{key}",
            )
        with col2:
            lon = st.number_input(
                f"{label} Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=0.0,
                step=0.000001,
                format="%.6f",
                key=f"lon_{key}",
            )
        corners_input[key] = (lat, lon)

    # Compute 4th corner
    try:
        fourth = compute_fourth_corner(corners_input, missing_key)
        st.write(
            f"**Computed {corner_labels[missing_key]}:** "
            f"Lat {fourth[0]:.6f}, Lon {fourth[1]:.6f}"
        )
    except ValueError as e:
        st.error(f"Could not compute 4th corner: {e}")
        st.stop()

    # ── Step 4: Stamp & Download ─────────────────────────────────────
    st.subheader("🖊️ Stamp Document")

    if st.button("Stamp Document"):
        # Read base document bytes
        base_bytes = base_doc.read()
        base_doc.seek(0)

        # Determine page dimensions
        ext = base_doc.name.rsplit(".", 1)[-1].lower() if "." in base_doc.name else ""
        if ext == "pdf":
            doc = fitz.open(stream=base_bytes, filetype="pdf")
            page = doc[0]
            page_width = page.rect.width
            page_height = page.rect.height
            doc.close()
        elif ext in ("png", "jpg", "jpeg"):
            img = Image.open(BytesIO(base_bytes))
            page_width, page_height = img.size
        else:
            st.error(f"Unsupported file type: .{ext}")
            st.stop()

        # Build the complete corners dict (all 4 corners)
        all_corners = dict(corners_input)
        all_corners[missing_key] = fourth

        # Map corner keys to page coordinates (document space)
        # TL = (0, 0), TR = (width, 0), BL = (0, height), BR = (width, height)
        page_corner_map = {
            "TL": (0.0, 0.0),
            "TR": (page_width, 0.0),
            "BL": (0.0, page_height),
            "BR": (page_width, page_height),
        }

        # Build geo → page point pairs (use the 3 provided corners)
        geo_points = []
        page_points = []
        for key in provided_keys:
            geo_points.append(all_corners[key])
            page_points.append(page_corner_map[key])

        # Build affine transform
        try:
            affine_matrix = build_affine_transform(geo_points, page_points)
        except ValueError as e:
            st.error(
                f"Cannot build coordinate transform: {e}. "
                "Please check that your corner coordinates are not collinear."
            )
            st.stop()

        # Build ordered corner list for bounds checking (clockwise: TL, TR, BR, BL)
        bounds_corners = [
            all_corners["TL"],
            all_corners["TR"],
            all_corners["BR"],
            all_corners["BL"],
        ]

        # Map each photo's GPS through the transform
        stamps = []
        stamped_count = 0
        outside_count = 0

        for p in valid:
            lat, lon = p["lat"], p["lon"]

            if not is_within_bounds(lat, lon, bounds_corners):
                outside_count += 1
                continue

            x, y = geo_to_page(lat, lon, affine_matrix)
            stamps.append({"code": p["code"], "x": x, "y": y})
            stamped_count += 1

        # Stamp the document
        try:
            output_bytes, output_filename = stamp_document(
                base_bytes, base_doc.name, stamps
            )
        except ValueError as e:
            st.error(f"Stamping failed: {e}")
            st.stop()

        # Status display
        total = len(valid)
        st.success(
            f"{stamped_count} of {total} photos stamped "
            f"({outside_count} outside document bounds)"
        )

        # Download button for stamped document
        if ext == "pdf":
            mime_type = "application/pdf"
        else:
            mime_type = "image/png"

        st.download_button(
            label="📥 Download Stamped Document",
            data=output_bytes,
            file_name=output_filename,
            mime=mime_type,
            key="stamped_doc_download",
        )
