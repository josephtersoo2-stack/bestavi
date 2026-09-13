from __future__ import annotations

import json
import re
from typing import Any


def clean_json_text(raw: str) -> str:
    """Strip markdown code blocks and surrounding whitespace."""
    text = raw.strip()
    if text.startswith("```"):
        # Remove first line if it contains ```json
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_json(raw: str) -> dict[str, Any]:
    """Safely extract and parse JSON object from LLM response text."""
    cleaned = clean_json_text(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: search for first { and last }
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return {"error": "Could not parse JSON response", "raw": raw}
