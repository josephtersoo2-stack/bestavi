from __future__ import annotations

import time
from typing import Any


def resolve_frame_root(page: Any, iframe_selector: str) -> Any:
    """Return the frame locator if iframe_selector is configured, else the root page."""
    if not iframe_selector or not page:
        return page
    try:
        page.wait_for_selector(iframe_selector, timeout=3000)
    except Exception:
        pass
    return page.frame_locator(iframe_selector)


def wait_for_element_visible(root: Any, selector: str, timeout_seconds: float = 15.0) -> bool:
    """Poll safely until an element matching selector is visible or timeout occurs."""
    start = time.monotonic()
    while time.monotonic() - start < timeout_seconds:
        try:
            loc = root.locator(selector).first
            if loc.is_visible():
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False
