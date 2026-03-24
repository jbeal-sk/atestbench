# Photo GPS → Google Earth KML & Photo Map Stamping

A Streamlit web app that extracts GPS coordinates from photos' EXIF metadata. Two workflows are available:

1. **KML Export** — Generate a downloadable KML file to import into [Google Earth Web](https://earth.google.com/web) and see labeled markers for each photo location.
2. **Photo Map Stamping** — Upload a site map or aerial photo, define its geographic extent, and stamp each photo's alphanumeric code at the correct position on the document.

Each uploaded photo is automatically assigned a unique 2-digit alphanumeric code (A1, A2, … Z0) and a downloadable Markdown report links every code to its filename and capture timestamp.

> For detailed documentation on the Photo Map feature, see [README_PHOTOMAP.md](README_PHOTOMAP.md).
> For the implementation breakdown and agent structure, see [AGENT_README.md](AGENT_README.md).

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Run the app**

```bash
streamlit run app.py
```

Then open the URL shown in your terminal (usually `http://localhost:8501`).

## Usage

### Shared Step: Upload Photos

1. Click **Browse files** and select one or more photos (`.jpg`, `.jpeg`, `.tiff`, `.png`).
2. The app extracts GPS coordinates and capture date/time from each photo's EXIF metadata.
3. Each photo is assigned a unique alphanumeric code (A1, A2, A3, …).

### Tab 1: KML Export

1. A results table shows each photo's code, name, latitude, longitude, and status (✅ GPS found / ❌ no GPS data).
2. An interactive map preview shows all extracted locations.
3. Click **Download KML file** to save `photo_locations.kml` to your computer.

**Importing into Google Earth Web:**

1. Go to [earth.google.com/web](https://earth.google.com/web).
2. Click the **☰ Menu** (top-left hamburger icon).
3. Select **Projects → New Project → Import KML file from computer**.
4. Upload the downloaded `photo_locations.kml` file.
5. Labeled markers will appear on the globe for each photo location.

### Tab 2: Photo Map

1. Review the photo table and download the **Markdown Report** linking each code to its filename and timestamp.
2. Upload a base document (PDF, PNG, or JPG) representing your geographic area.
3. Select which 3 of 4 corners to provide and enter their latitude/longitude coordinates.
4. Click **Stamp Document** — the app maps each photo's GPS position onto the document and stamps its code.
5. Download the stamped document.

For a full walkthrough and technical details, see [README_PHOTOMAP.md](README_PHOTOMAP.md).

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | ≥ 1.30.0 | Web application framework |
| Pillow | ≥ 9.0.0 | EXIF metadata extraction and image stamping |
| simplekml | ≥ 1.3.0 | KML file generation |
| pandas | ≥ 1.5.0 | Data tables in the UI |
| PyMuPDF | ≥ 1.23.0 | PDF text stamping (vector text) |
| numpy | ≥ 1.24.0 | Affine transformation matrix computation |

## Notes

- Photos must contain EXIF GPS metadata. This is typical of photos taken with a **smartphone** or a **GPS-enabled camera**.
- Photos that lack GPS data are flagged in the results table and excluded from the KML file and map stamping.
- Only EXIF metadata is read; full image data is not decoded, so the app handles large batches efficiently.
- For Photo Map stamping, the affine transform assumes the document represents a parallelogram. See [README_PHOTOMAP.md](README_PHOTOMAP.md) for limitations.
