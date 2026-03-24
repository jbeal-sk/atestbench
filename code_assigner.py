import string

# Code sequence: A1, A2, ..., A9, A0, B1, B2, ..., Z9, Z0
_LETTERS = string.ascii_uppercase
_DIGITS = [str(d) for d in range(1, 10)] + ["0"]  # 1-9 then 0

MAX_CODES = len(_LETTERS) * len(_DIGITS)  # 26 * 10 = 260


def assign_codes(photo_names: list[str]) -> dict[str, str]:
    """
    Assign sequential alphanumeric codes to a list of photo filenames.

    Codes follow the pattern: A1, A2, ... A9, A0, B1, B2, ... Z9, Z0
    providing up to 260 unique codes.

    Args:
        photo_names: List of photo filename strings.

    Returns:
        A dictionary mapping each filename to its assigned code.

    Raises:
        ValueError: If more than 260 photo names are provided.
    """
    if len(photo_names) > MAX_CODES:
        raise ValueError(
            f"Cannot assign codes to {len(photo_names)} photos. "
            f"Maximum supported is {MAX_CODES}."
        )

    result = {}
    for index, name in enumerate(photo_names):
        letter = _LETTERS[index // len(_DIGITS)]
        digit = _DIGITS[index % len(_DIGITS)]
        result[name] = f"{letter}{digit}"

    return result
