from __future__ import annotations

import re
from typing import Any

DEFAULT_BALANCE_SELECTORS = [
    ".balance-amount",
    ".balance",
    ".balance-container",
    ".user-balance .amount",
    ".user-balance",
    ".balance-value",
    ".amount-bold",
    ".header-balance .amount",
    ".header-balance",
    "span:has-text('NGN')",
    "span:has-text('₦')",
    "span:has-text('$')",
]


def extract_numeric_balance(page: Any, root: Any, selectors: list[str] | None = None) -> float | None:
    """Scrape balance amount from page or iframe root using candidate selectors and regex."""
    targets = []
    if root is not None:
        targets.append(root)
    if page is not None and page != root:
        targets.append(page)

    check_selectors = selectors or DEFAULT_BALANCE_SELECTORS

    for target in targets:
        for sel in check_selectors:
            try:
                loc = target.locator(sel)
                count = loc.count() if hasattr(loc, "count") else 0
                for i in range(min(count, 3)):
                    elem = loc.nth(i)
                    if elem.is_visible():
                        txt = elem.inner_text().strip()
                        if "won" in txt.lower():
                            continue
                        clean = (
                            txt.replace("Balance:", "")
                            .replace("NGN", "")
                            .replace("₦", "")
                            .replace("$", "")
                            .replace(",", "")
                            .strip()
                        )
                        m = re.search(r"([0-9]+\.?[0-9]*)", clean)
                        if m:
                            val = float(m.group(1))
                            if val > 0:
                                return val
            except Exception:
                pass
    return None
