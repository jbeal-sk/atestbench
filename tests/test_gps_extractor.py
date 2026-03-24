import io
import struct

import pytest
from PIL import Image

from gps_extractor import extract_gps, extract_metadata, extract_gps_from_files


def _make_image_bytes(exif_data=None):
    """Create a minimal JPEG image in memory, optionally with EXIF data."""
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    if exif_data is not None:
        img.save(buf, format="JPEG", exif=exif_data)
    else:
        img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _build_exif_with_datetime(datetime_original=None, datetime_tag=None):
    """Build EXIF bytes with optional DateTimeOriginal (36867) and DateTime (306)."""
    img = Image.new("RGB", (10, 10), color="blue")
    exif = img.getexif()
    if datetime_original is not None:
        exif[36867] = datetime_original
    if datetime_tag is not None:
        exif[306] = datetime_tag
    return exif.tobytes()


class TestExtractGps:
    def test_no_exif(self):
        buf = _make_image_bytes()
        result = extract_gps(buf)
        assert result == {"lat": None, "lon": None}

    def test_non_image_graceful(self):
        buf = io.BytesIO(b"not an image at all")
        result = extract_gps(buf)
        assert result == {"lat": None, "lon": None}

    def test_returns_dict_with_lat_lon_keys(self):
        buf = _make_image_bytes()
        result = extract_gps(buf)
        assert "lat" in result
        assert "lon" in result


class TestExtractMetadata:
    def test_no_exif_returns_none_datetime(self):
        buf = _make_image_bytes()
        result = extract_metadata(buf)
        assert result["lat"] is None
        assert result["lon"] is None
        assert result["datetime"] is None

    def test_with_datetime_original(self):
        exif_bytes = _build_exif_with_datetime(
            datetime_original="2024:03:15 14:30:22"
        )
        buf = _make_image_bytes(exif_data=exif_bytes)
        result = extract_metadata(buf)
        assert result["datetime"] == "2024:03:15 14:30:22"

    def test_falls_back_to_datetime_tag(self):
        exif_bytes = _build_exif_with_datetime(datetime_tag="2024:01:01 10:00:00")
        buf = _make_image_bytes(exif_data=exif_bytes)
        result = extract_metadata(buf)
        assert result["datetime"] == "2024:01:01 10:00:00"

    def test_datetime_original_takes_precedence(self):
        exif_bytes = _build_exif_with_datetime(
            datetime_original="2024:03:15 14:30:22",
            datetime_tag="2024:01:01 10:00:00",
        )
        buf = _make_image_bytes(exif_data=exif_bytes)
        result = extract_metadata(buf)
        assert result["datetime"] == "2024:03:15 14:30:22"

    def test_non_image_returns_none(self):
        buf = io.BytesIO(b"not an image")
        result = extract_metadata(buf)
        assert result["lat"] is None
        assert result["lon"] is None
        assert result["datetime"] is None

    def test_returns_all_three_keys(self):
        buf = _make_image_bytes()
        result = extract_metadata(buf)
        assert set(result.keys()) == {"lat", "lon", "datetime"}


class _FakeFile:
    """Minimal file-like object simulating st.file_uploader output."""

    def __init__(self, name, data):
        self.name = name
        self._buf = io.BytesIO(data)

    def read(self, *args):
        return self._buf.read(*args)

    def seek(self, pos):
        return self._buf.seek(pos)

    def tell(self):
        return self._buf.tell()


class TestExtractGpsFromFiles:
    def test_empty_list(self):
        assert extract_gps_from_files([]) == []

    def test_includes_datetime_key(self):
        img = Image.new("RGB", (10, 10), color="green")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        data = buf.getvalue()

        fake = _FakeFile("test.jpg", data)
        results = extract_gps_from_files([fake])
        assert len(results) == 1
        assert "datetime" in results[0]
        assert "name" in results[0]
        assert "lat" in results[0]
        assert "lon" in results[0]

    def test_multiple_files(self):
        files = []
        for name in ["a.jpg", "b.jpg"]:
            img = Image.new("RGB", (10, 10))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            files.append(_FakeFile(name, buf.getvalue()))

        results = extract_gps_from_files(files)
        assert len(results) == 2
        assert results[0]["name"] == "a.jpg"
        assert results[1]["name"] == "b.jpg"

    def test_file_pointer_reset(self):
        """After extraction, file pointer should be at 0 for re-reading."""
        img = Image.new("RGB", (10, 10))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        fake = _FakeFile("test.jpg", buf.getvalue())

        extract_gps_from_files([fake])
        assert fake.tell() == 0
