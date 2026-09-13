from __future__ import annotations

import re


def parse_multiplier(text: str) -> float | None:
    """Parse values such as ``2.10x`` from a result element."""
    value = text.strip().lower().replace(",", "")
    if not value:
        return None
    # Operators render the suffix as either ASCII ``x`` or multiplication
    # sign ``×``; some widgets include a short label around the number.
    match = re.search(r"(?<![a-z])([0-9]+(?:\.[0-9]+)?)\s*[x×]?", value)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None
