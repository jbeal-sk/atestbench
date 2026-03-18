# Photo GPS → Google Earth KML

A Streamlit web app that extracts GPS coordinates from photos' EXIF metadata and generates a downloadable KML file you can import into [Google Earth Web](https://earth.google.com/web) to see labeled markers for each photo location.

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

1. Click **Browse files** and select one or more photos (`.jpg`, `.jpeg`, `.tiff`, `.png`).
2. The app extracts GPS coordinates from each photo's EXIF metadata.
3. A results table shows each photo's name, latitude, longitude, and status (✅ GPS found / ❌ no GPS data).
4. An interactive map preview shows all extracted locations.
5. Click **Download KML file** to save `photo_locations.kml` to your computer.

## Importing into Google Earth Web

1. Go to [earth.google.com/web](https://earth.google.com/web).
2. Click the **☰ Menu** (top-left hamburger icon).
3. Select **Projects → New Project → Import KML file from computer**.
4. Upload the downloaded `photo_locations.kml` file.
5. Labeled markers will appear on the globe for each photo location.

## Notes

- Photos must contain EXIF GPS metadata. This is typical of photos taken with a **smartphone** or a **GPS-enabled camera**.
- Photos that lack GPS data are flagged in the results table and excluded from the KML file.
- Only EXIF metadata is read; full image data is not decoded, so the app handles large batches efficiently.
