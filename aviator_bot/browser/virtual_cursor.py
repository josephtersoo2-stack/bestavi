from __future__ import annotations

from typing import Any

CURSOR_INJECTION_SCRIPT = """
() => {
    if (document.getElementById('bot-virtual-cursor')) return;
    const cursor = document.createElement('div');
    cursor.id = 'bot-virtual-cursor';
    cursor.style.position = 'fixed';
    cursor.style.top = '150px';
    cursor.style.left = '200px';
    cursor.style.width = '18px';
    cursor.style.height = '18px';
    cursor.style.borderRadius = '50%';
    cursor.style.backgroundColor = 'rgba(255, 59, 48, 0.85)';
    cursor.style.border = '2px solid #ffffff';
    cursor.style.boxShadow = '0 0 12px rgba(255, 59, 48, 0.95)';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = '2147483647';
    cursor.style.transition = 'top 0.45s ease-out, left 0.45s ease-out, transform 0.2s';
    
    const dot = document.createElement('div');
    dot.style.position = 'absolute';
    dot.style.top = '5px';
    dot.style.left = '5px';
    dot.style.width = '4px';
    dot.style.height = '4px';
    dot.style.borderRadius = '50%';
    dot.style.backgroundColor = '#ffffff';
    cursor.appendChild(dot);
    
    document.body.appendChild(cursor);
    
    window.__moveVirtualCursor = (x, y) => {
        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
    };
    window.__pulseVirtualCursor = () => {
        cursor.style.transform = 'scale(1.4)';
        setTimeout(() => { cursor.style.transform = 'scale(1)'; }, 200);
    };
}
"""


def inject_virtual_cursor(page_or_root: Any) -> None:
    """Inject the visual glowing laser cursor into the DOM."""
    try:
        if hasattr(page_or_root, "evaluate"):
            page_or_root.evaluate(CURSOR_INJECTION_SCRIPT)
        elif hasattr(page_or_root, "locator"):
            page_or_root.locator("body").evaluate(CURSOR_INJECTION_SCRIPT)
    except Exception:
        pass


def move_virtual_cursor(page_or_root: Any, x: int, y: int) -> None:
    """Smoothly translate the virtual laser cursor to target screen coordinates."""
    try:
        script = f"() => {{ if (window.__moveVirtualCursor) window.__moveVirtualCursor({x}, {y}); }}"
        if hasattr(page_or_root, "evaluate"):
            page_or_root.evaluate(script)
        elif hasattr(page_or_root, "locator"):
            page_or_root.locator("body").evaluate(script)
    except Exception:
        pass


def pulse_virtual_cursor(page_or_root: Any) -> None:
    """Trigger a click-pulse animation on the virtual cursor."""
    try:
        script = "() => { if (window.__pulseVirtualCursor) window.__pulseVirtualCursor(); }"
        if hasattr(page_or_root, "evaluate"):
            page_or_root.evaluate(script)
        elif hasattr(page_or_root, "locator"):
            page_or_root.locator("body").evaluate(script)
    except Exception:
        pass
