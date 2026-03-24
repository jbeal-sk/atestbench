from datetime import date

from code_assigner import _LETTERS, _DIGITS


def _code_sort_key(code: str) -> int:
    """Return an integer sort key for an alphanumeric code like 'A1' or 'Z0'."""
    letter = code[0]
    digit = code[1]
    return _LETTERS.index(letter) * len(_DIGITS) + _DIGITS.index(digit)


def generate_markdown_report(photo_data: list[dict]) -> str:
    """
    Generate a markdown report linking each photo's code to its filename
    and capture timestamp.

    Args:
        photo_data: List of dicts, each with keys "name", "lat", "lon",
                    "datetime", and "code".

    Returns:
        A markdown string containing a title, formatted table, and footer
        with the generation date.
    """
    # Sort by code assignment order
    sorted_data = sorted(photo_data, key=lambda p: _code_sort_key(p["code"]))

    lines: list[str] = []
    lines.append("# Photo Location Report")
    lines.append("")
    lines.append("| Code | Filename | Date/Time | Coordinates |")
    lines.append("|------|----------|-----------|-------------|")

    for photo in sorted_data:
        code = photo["code"]
        filename = photo["name"]

        if photo.get("datetime"):
            datetime_str = photo["datetime"]
        else:
            datetime_str = "No date available"

        if photo.get("lat") is not None and photo.get("lon") is not None:
            coords = f"{photo['lat']}, {photo['lon']}"
        else:
            coords = "No GPS"

        lines.append(f"| {code} | {filename} | {datetime_str} | {coords} |")

    lines.append("")
    lines.append(f"Generated on {date.today().isoformat()}")
    lines.append("")

    return "\n".join(lines)
