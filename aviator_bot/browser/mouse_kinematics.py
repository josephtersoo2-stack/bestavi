from __future__ import annotations

import random
from typing import Any
from .virtual_cursor import inject_virtual_cursor, move_virtual_cursor, pulse_virtual_cursor


def calculate_bezier_points(start_x: int, start_y: int, end_x: int, end_y: int, steps: int = 10) -> list[tuple[int, int]]:
    """Compute quadratic Bezier curve coordinates for realistic human hand trajectory."""
    ctrl_x = (start_x + end_x) // 2 + random.randint(-40, 40)
    ctrl_y = (start_y + end_y) // 2 + random.randint(-40, 40)
    points = []
    for i in range(1, steps + 1):
        t = i / steps
        # B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
        x = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * ctrl_x + t ** 2 * end_x)
        y = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * ctrl_y + t ** 2 * end_y)
        points.append((x, y))
    return points


def perform_human_activity(page: Any, root: Any) -> None:
    """Execute human-like micro-activity (mouse wandering, hover, gentle scroll) to defeat idle detectors."""
    try:
        inject_virtual_cursor(page)
        inject_virtual_cursor(root)

        action = random.choice(["mouse_move", "hover_history", "gentle_scroll"])
        if action == "mouse_move":
            vp = page.viewport_size or {"width": 1280, "height": 800}
            w = vp.get("width", 1280)
            h = vp.get("height", 800)
            tx = random.randint(150, max(200, w - 150))
            ty = random.randint(100, max(150, h - 150))
            move_virtual_cursor(root, tx, ty)
            page.mouse.move(tx, ty, steps=random.randint(6, 14))

        elif action == "hover_history":
            pills = root.locator(".history-odds-item, .history-item, .pills")
            count = pills.count() if hasattr(pills, "count") else 0
            if count > 0:
                idx = random.randint(max(0, count - 5), count - 1)
                pill = pills.nth(idx)
                if pill.is_visible():
                    box = pill.bounding_box()
                    if box:
                        px = int(box["x"] + box["width"] / 2)
                        py = int(box["y"] + box["height"] / 2)
                        move_virtual_cursor(root, px, py)
                        pulse_virtual_cursor(root)
                    pill.hover()

        elif action == "gentle_scroll":
            page.evaluate("""() => {
                const max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
                if (max > 0) {
                    const target = Math.floor(Math.random() * Math.min(250, max));
                    window.scrollTo({top: target, behavior: 'smooth'});
                }
            }""")
    except Exception:
        pass
