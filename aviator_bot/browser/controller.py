from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Protocol, Any

from aviator_bot.config.settings import BrowserSelectors
from aviator_bot.platforms.registry import PlatformRegistry
from aviator_bot.platforms.base.game_base import BaseGameAddon

from .dry_run_adapter import DryRunAdapter
from .session_launcher import launch_browser_session
from .dom_waiter import resolve_frame_root
from .balance_extractor import extract_numeric_balance
from .mouse_kinematics import perform_human_activity
from .connection_monitor import is_page_responsive, soft_reload_page


class GameAdapter(Protocol):
    def connect(self) -> None: ...
    def prepare_game(self, base_stake: float, auto_cashout: float) -> bool: ...
    def idle_activity(self) -> None: ...
    def read_latest_history_multiplier(self) -> float | None: ...
    def read_balance(self) -> float | None: ...
    def wait_for_betting_window(self, stop_requested: Callable[[], bool]) -> bool: ...
    def place_bet(self, stake: float, auto_cashout: float) -> None: ...
    def wait_for_result(self, stop_requested: Callable[[], bool]) -> float | None: ...
    def close(self) -> None: ...


@dataclass
class PlaywrightAdapter:
    """Browser adapter delegating game interaction to the active Game Addon."""
    selectors: BrowserSelectors
    platform_id: str = "ilotbet"
    game_id: str = "aviator"
    _playwright: Any = None
    _context: Any = None
    _page: Any = None
    _root: Any = None
    _game_addon: BaseGameAddon | None = None
    _next_activity_time: float = 0.0

    def _get_addon(self) -> BaseGameAddon:
        if self._game_addon is None:
            registry = PlatformRegistry.get_instance()
            self._game_addon = registry.get_game(self.platform_id, self.game_id)
        return self._game_addon

    def connect(self) -> None:
        if self._page is not None and not (hasattr(self._page, "is_closed") and self._page.is_closed()):
            return
        if not self.selectors.url:
            addon = self._get_addon()
            self.selectors.url = addon.selectors.game_url or "https://www.ilotbet.com/pc/iframe"

        self._playwright, self._context, self._page = launch_browser_session(
            user_data_dir=self.selectors.user_data_dir or "data/browser_profile",
            headless=self.selectors.headless,
        )

        current_url = self._page.url or ""
        target_url = self.selectors.url
        if not current_url or current_url == "about:blank" or target_url.split("//")[-1].split("/")[0] not in current_url:
            self._page.goto(target_url)

        addon = self._get_addon()
        iframe_sel = addon.selectors.iframe_selector or self.selectors.iframe_selector
        self._root = resolve_frame_root(self._page, iframe_sel)
        self._next_activity_time = time.monotonic() + random.uniform(2.0, 5.0)

    def prepare_game(self, base_stake: float, auto_cashout: float) -> bool:
        if self._page is None:
            self.connect()
        addon = self._get_addon()
        iframe_sel = addon.selectors.iframe_selector or self.selectors.iframe_selector
        self._root = resolve_frame_root(self._page, iframe_sel)
        return addon.prepare_game(self._root, base_stake, auto_cashout)

    def idle_activity(self) -> None:
        now = time.monotonic()
        if now < self._next_activity_time or not self._page:
            return
        self._next_activity_time = now + random.uniform(8.0, 16.0)
        perform_human_activity(self._page, self._root)

    def read_latest_history_multiplier(self) -> float | None:
        recent = self.read_recent_history_multipliers(1)
        return recent[0] if recent else None

    def read_recent_history_multipliers(self, count: int = 10) -> list[float]:
        if self._root is None:
            return []
        addon = self._get_addon()
        return addon.extract_recent_multipliers(self._root, count)

    def read_balance(self) -> float | None:
        addon = self._get_addon()
        selectors = addon.selectors.balance_selectors if addon else None
        return extract_numeric_balance(self._page, self._root, selectors)

    def wait_for_betting_window(self, stop_requested: Callable[[], bool]) -> bool:
        if self._page is None:
            raise RuntimeError("Adapter is not connected")
        addon = self._get_addon()
        return addon.wait_for_betting_window(self._root, stop_requested)

    def place_bet(self, stake: float, auto_cashout: float) -> None:
        if self._page is None:
            raise RuntimeError("Adapter is not connected")
        addon = self._get_addon()
        addon.place_bet(self._root, stake, auto_cashout)

    def wait_for_result(self, stop_requested: Callable[[], bool]) -> float | None:
        if self._page is None:
            raise RuntimeError("Adapter is not connected")
        addon = self._get_addon()
        return addon.wait_for_result(self._root, stop_requested)

    def is_connected(self) -> bool:
        return is_page_responsive(self._page)

    def reconnect(self) -> bool:
        if self._page is not None and soft_reload_page(self._page):
            addon = self._get_addon()
            iframe_sel = addon.selectors.iframe_selector or self.selectors.iframe_selector
            self._root = resolve_frame_root(self._page, iframe_sel)
            return True
        self.close()
        self.connect()
        return True

    def close(self) -> None:
        if self._context is not None:
            try: self._context.close()
            except Exception: pass
        if self._playwright is not None:
            try: self._playwright.stop()
            except Exception: pass
        self._page = self._context = self._playwright = self._root = None
