import streamlit as st
import pandas as pd

from gps_extractor import extract_gps_from_files
from kml_generator import generate_kml

st.set_page_config(page_title="Photo GPS → Google Earth KML", page_icon="🌍")

st.title("🌍 Photo GPS → Google Earth KML")
st.write(
    "Upload photos with GPS metadata to extract their coordinates and download a "
    "KML file you can import into [Google Earth Web](https://earth.google.com/web)."
)

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

# Extract GPS data from all uploaded files
with st.spinner("Extracting GPS data from photos…"):
    photo_data = extract_gps_from_files(uploaded_files)

# Build a results DataFrame
rows = []
for p in photo_data:
    if p["lat"] is not None and p["lon"] is not None:
        status = "✅ GPS found"
    else:
        status = "❌ No GPS data"
    rows.append(
        {
            "Photo": p["name"],
            "Latitude": p["lat"],
            "Longitude": p["lon"],
            "Status": status,
        }
    )

df = pd.DataFrame(rows)

st.subheader("Results")
st.dataframe(df, use_container_width=True)

# Stats
valid = [p for p in photo_data if p["lat"] is not None and p["lon"] is not None]
invalid = [p for p in photo_data if p["lat"] is None or p["lon"] is None]

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

st.success(f"{len(valid)} photo(s) with valid GPS coordinates will be included in the KML file.")

# Map preview
st.subheader("Map Preview")
map_df = pd.DataFrame(
    [{"lat": p["lat"], "lon": p["lon"]} for p in valid]
)
st.map(map_df)

# KML download
kml_string = generate_kml(valid)

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
