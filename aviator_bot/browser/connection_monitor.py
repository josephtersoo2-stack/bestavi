from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("aviator_bot.browser.connection_monitor")


def is_page_responsive(page: Any) -> bool:
    """Verify if the browser page is open and ready."""
    if page is None:
        return False
    try:
        if hasattr(page, "is_closed") and page.is_closed():
            return False
        state = page.evaluate("() => document.readyState")
        return bool(state)
    except Exception:
        return False


def soft_reload_page(page: Any) -> bool:
    """Attempt a non-destructive tab reload without tearing down the browser context."""
    if page is None:
        return False
    try:
        if hasattr(page, "is_closed") and page.is_closed():
            return False
        page.reload(wait_until="domcontentloaded", timeout=15000)
        return True
    except Exception as exc:
        logger.debug("Soft reload failed: %s", exc)
        return False
