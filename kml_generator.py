import simplekml


def generate_kml(photo_data):
    """
    Generate a KML document from a list of photo GPS data.

    Args:
        photo_data: A list of dicts with keys 'name', 'lat', 'lon'.
                    Only entries with non-None lat/lon are included.

    Returns:
        A KML string ready for download.
    """
    kml = simplekml.Kml()

    for photo in photo_data:
        if photo["lat"] is not None and photo["lon"] is not None:
            point = kml.newpoint(name=photo["name"])
            # simplekml uses (lon, lat) order
            point.coords = [(photo["lon"], photo["lat"])]
            code = photo.get("code", "")
            if code:
                point.description = f"[{code}] {photo['name']} — {photo['lat']:.6f}, {photo['lon']:.6f}"
            else:
                point.description = f"{photo['name']} — {photo['lat']:.6f}, {photo['lon']:.6f}"

    return kml.kml()
