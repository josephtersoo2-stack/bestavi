from __future__ import annotations

import re
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from aviator_bot.config.settings import BrowserSelectors
from .detector import parse_multiplier


@dataclass(frozen=True)
class GameSnapshot:
    """Read-only state captured from the Best Aviator iframe."""

    balance: float | None
    phase: str
    current_multiplier: float | None
    last_multiplier: float | None
    login_required: bool
    observed_at: str


def parse_balance(text: str) -> float | None:
    match = re.search(r"balance\s*:\s*([0-9][0-9,]*(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


class PlaywrightObserver:
    """Observe a supported crash-game page without betting or editing controls."""

    def __init__(self, selectors: BrowserSelectors) -> None:
        self.selectors = selectors
        self._playwright: object | None = None
        self._browser: object | None = None
        self._context: object | None = None
        self._page: object | None = None
        self._root: object | None = None

    def connect(self) -> None:
        if not self.selectors.url:
            raise ValueError("browser.url must be configured before observing")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed; install requirements.txt") from exc
        if sys.platform == "win32":
            import asyncio
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass
        self._playwright = sync_playwright().start()
        import os
        profile = Path(self.selectors.user_data_dir).expanduser().resolve()
        profile.mkdir(parents=True, exist_ok=True)
        for lock_name in ("SingletonLock", "SingletonSocket", "SingletonCookie", "lockfile"):
            try: (profile / lock_name).unlink(missing_ok=True)
            except Exception: pass

        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                str(profile), headless=self.selectors.headless
            )
        except Exception as exc:
            if "ProcessSingleton" in str(exc) or "Lock file" in str(exc) or "profile directory" in str(exc):
                alt_profile = profile.parent / f"{profile.name}_obs_{os.getpid()}"
                alt_profile.mkdir(parents=True, exist_ok=True)
                for lock_name in ("SingletonLock", "SingletonSocket", "SingletonCookie", "lockfile"):
                    try: (alt_profile / lock_name).unlink(missing_ok=True)
                    except Exception: pass
                self._context = self._playwright.chromium.launch_persistent_context(
                    str(alt_profile), headless=self.selectors.headless
                )
            else:
                raise
        pages = self._context.pages
        self._page = pages[0] if pages else self._context.new_page()
        if not self._page.url or self._page.url == "about:blank":
            self._page.goto(self.selectors.url)
        self._root = self._page.frame_locator(self.selectors.iframe_selector) if self.selectors.iframe_selector else self._page

    def snapshot(self) -> GameSnapshot:
        if self._root is None:
            raise RuntimeError("Observer is not connected")
        balance_text = self._root.locator("body").inner_text()
        balance = parse_balance(balance_text)
        phase = self._detect_phase()
        current = self._read_multiplier(self.selectors.multiplier_selector)
        history_selector = self.selectors.history_multiplier_selector or ".history-odds-item:last-child"
        history = self._read_multiplier(history_selector)
        # Only a configured login control is authoritative.  iLOTBET can
        # render its balance outside the iframe, so a missing parsed balance
        # must not block round tracking after the user has logged in.
        login_required = self._is_visible(self.selectors.login_selector) if self.selectors.login_selector else False
        return GameSnapshot(balance, phase, current, history, login_required, datetime.now(timezone.utc).isoformat())

    def observe(self, stop_requested: Callable[[], bool], on_snapshot: Callable[[GameSnapshot], None],
                interval: float = 0.25, on_status: Callable[[str], None] | None = None) -> None:
        last: GameSnapshot | None = None
        status = on_status or (lambda _: None)
        reconnecting = False
        next_scroll = time.monotonic() + self._next_scroll_delay()
        while not stop_requested():
            try:
                if self.selectors.activity_scroll_enabled and time.monotonic() >= next_scroll:
                    self._scroll_page()
                    next_scroll = time.monotonic() + self._next_scroll_delay()
                current = self.snapshot()
                if reconnecting:
                    status("connected")
                    reconnecting = False
                if current != last:
                    on_snapshot(current)
                    last = current
                time.sleep(interval)
            except Exception:
                if not reconnecting:
                    status("reconnecting")
                    reconnecting = True
                try:
                    self._recover_page()
                except Exception:
                    status("disconnected")
                    return
                time.sleep(max(interval, self.selectors.reconnect_delay_seconds))

    def _next_scroll_delay(self) -> float:
        return random.uniform(self.selectors.activity_scroll_min_seconds,
                              self.selectors.activity_scroll_max_seconds)

    def _scroll_page(self) -> None:
        """Simulate realistic human actions (mouse moves, safe hover, micro-scrolls) to prevent idle detection."""
        if self._page is None:
            return
        try:
            action_type = random.choice(["mouse_move", "hover_history", "gentle_scroll"])
            if action_type == "mouse_move":
                vp = self._page.viewport_size or {"width": 1280, "height": 800}
                w = vp.get("width", 1280)
                h = vp.get("height", 800)
                target_x = random.randint(150, max(200, w - 150))
                target_y = random.randint(100, max(150, h - 150))
                self._page.mouse.move(target_x, target_y, steps=random.randint(6, 14))
            elif action_type == "hover_history":
                pills = self._root.locator(".history-odds-item, .history-item, .pills")
                count = pills.count() if hasattr(pills, "count") else 0
                if count > 0:
                    idx = random.randint(max(0, count - 5), count - 1)
                    pill = pills.nth(idx)
                    if pill.is_visible():
                        pill.hover()
            elif action_type == "gentle_scroll":
                self._page.evaluate("""() => {
                    const max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
                    if (max > 0) {
                        const target = Math.floor(Math.random() * Math.min(250, max));
                        window.scrollTo({top: target, behavior: 'smooth'});
                    }
                }""")
        except Exception:
            return


    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
        except Exception:
            pass
        try:
            if self._playwright is not None:
                self._playwright.stop()
        except Exception:
            pass
        self._page = self._root = self._context = self._playwright = None

    def _recover_page(self) -> None:
        if self._context is None:
            return
        pages = [page for page in self._context.pages if not page.is_closed()]
        self._page = pages[0] if pages else self._context.new_page()
        self._root = self._page.frame_locator(self.selectors.iframe_selector) if self.selectors.iframe_selector else self._page
        # Do not navigate away from a login redirect; once the user completes
        # login on this persistent page the iframe will be rebound automatically.
        if self._page.url in {"", "about:blank"}:
            self._page.goto(self.selectors.url)

    def _read_multiplier(self, selector: str) -> float | None:
        if not selector or self._root is None:
            return None
        try:
            return parse_multiplier(self._root.locator(selector).last.inner_text())
        except Exception:
            return None

    def _is_visible(self, selector: str) -> bool:
        if not selector or self._root is None:
            return False
        try:
            return self._root.locator(selector).first.is_visible()
        except Exception:
            return False

    def _detect_phase(self) -> str:
        """Infer phase from configured indicators, with BC.Game text fallback."""
        crashed_selector = self.selectors.crashed_phase_selector
        if crashed_selector and self._root is not None:
            try:
                text = self._root.locator(crashed_selector).last.inner_text().strip().lower()
                if "crash" in text or "flew" in text:
                    return "BETWEEN_ROUNDS"
                # BC.Game renders the live multiplier in this same overlay.
                if parse_multiplier(text) is not None:
                    return "RUNNING"
            except Exception:
                pass
        if self.selectors.live_phase_selector and self._is_visible(self.selectors.live_phase_selector):
            return "RUNNING"
        if self._is_visible(self.selectors.betting_window_selector):
            return "BETTING"
        return "BETWEEN_ROUNDS"
