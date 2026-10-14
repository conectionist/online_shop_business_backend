"""Text normalization used to match customer names and notes across orders."""

import re
import unicodedata
from typing import Optional


def normalize_romanian(text: Optional[str]) -> str:
    if text is None:
        return ""
    # Lowercase and strip diacritics via NFD decomposition
    lowered = text.strip().lower()
    normalized = unicodedata.normalize('NFD', lowered)
    without_marks = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_marks


def normalize_name_for_matching(text: Optional[str]) -> str:
    """Normalize names for matching:

    - Trim leading/trailing spaces
    - Lowercase and remove diacritics (Romanian included)
    - Collapse any internal whitespace runs to a single space
    """
    if text is None:
        return ""
    base = normalize_romanian(text)
    # Collapse all Unicode whitespace to single ASCII space
    collapsed = re.sub(r"\s+", " ", base)
    return collapsed.strip()
