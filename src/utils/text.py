"""Text processing utilities."""

import unicodedata
from typing import List, Tuple


def normalize_text(text: str) -> str:
    """Normalize text by removing accents and converting to lowercase.

    Args:
    ----
        text: Text to normalize

    Returns:
    -------
        Normalized text string

    """
    # Convert to lowercase
    text = text.lower()

    # Remove accents/diacritics
    # NFD = Normalization Form Decomposed (separates base chars from accents)
    text = unicodedata.normalize("NFD", text)
    # Filter out combining characters (accents)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    return text.strip()


def fuzzy_match(text: str, patterns: List[str]) -> Tuple[bool, str]:
    """Check if text matches any of the given patterns.

    Args:
    ----
        text: Text to check
        patterns: List of patterns to match against

    Returns:
    -------
        Tuple of (match_found, matched_pattern)

    """
    normalized_text = normalize_text(text)

    for pattern in patterns:
        normalized_pattern = normalize_text(pattern)
        if normalized_pattern in normalized_text:
            return True, pattern

    return False, ""
