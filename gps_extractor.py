from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import GPSTAGS

# Tag ID for the GPS IFD
_GPS_IFD_TAG = 34853


def _dms_to_decimal(dms, ref):
    """Convert degrees/minutes/seconds to decimal degrees."""
    degrees = dms[0]
    minutes = dms[1]
    seconds = dms[2]

    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600

    if ref in ("S", "W"):
        decimal = -decimal

    return decimal


def extract_gps(image_file):
    """
    Extract GPS coordinates from an image file's EXIF metadata.

    Args:
        image_file: A file-like object (e.g. from st.file_uploader).

    Returns:
        A dict with keys 'lat' and 'lon' (floats), or None for each if not found.
    """
    lat = None
    lon = None

    try:
        image = Image.open(image_file)
        exif_data = image.getexif()

        if not exif_data:
            return {"lat": None, "lon": None}

        # Use get_ifd to retrieve the GPS sub-IFD directly
        raw_gps = exif_data.get_ifd(_GPS_IFD_TAG)
        if not raw_gps:
            return {"lat": None, "lon": None}

        gps_info = {GPSTAGS.get(k, k): v for k, v in raw_gps.items()}

        if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
            lat = _dms_to_decimal(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])

        if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
            lon = _dms_to_decimal(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])

    except (UnidentifiedImageError, OSError, KeyError, TypeError, ValueError):
        pass

    return {"lat": lat, "lon": lon}


def extract_gps_from_files(uploaded_files):
    """
    Extract GPS coordinates from a list of uploaded image files.

    Args:
        uploaded_files: List of file-like objects from st.file_uploader.

    Returns:
        A list of dicts: [{"name": "photo.jpg", "lat": 40.7128, "lon": -74.0060}, ...]
        lat/lon are None when GPS data is not available.
    """
    results = []
    for f in uploaded_files:
        coords = extract_gps(f)
        results.append({"name": f.name, "lat": coords["lat"], "lon": coords["lon"]})
        # Reset file pointer so it can be re-read if needed
        f.seek(0)
    return results



def extract_gps_from_files(uploaded_files):
    """
    Extract GPS coordinates from a list of uploaded image files.

    Args:
        uploaded_files: List of file-like objects from st.file_uploader.

    Returns:
        A list of dicts: [{"name": "photo.jpg", "lat": 40.7128, "lon": -74.0060}, ...]
        lat/lon are None when GPS data is not available.
    """
    results = []
    for f in uploaded_files:
        coords = extract_gps(f)
        results.append({"name": f.name, "lat": coords["lat"], "lon": coords["lon"]})
        # Reset file pointer so it can be re-read if needed
        f.seek(0)
    return results
