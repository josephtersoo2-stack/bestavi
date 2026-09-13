from __future__ import annotations

import random
import time
from typing import Callable, Any

from aviator_bot.platforms.base.enums import GameCategory
from aviator_bot.platforms.base.selectors import BaseGameSelectors
from aviator_bot.platforms.base.game_base import BaseGameAddon
from aviator_bot.browser.detector import parse_multiplier


class BCGameCrashGame(BaseGameAddon):
    """BC.Game native Crash game addon."""

    @property
    def game_id(self) -> str:
        return "crash"

    @property
    def display_name(self) -> str:
        return "BC Crash"

    @property
    def category(self) -> GameCategory:
        return GameCategory.CRASH

    def default_selectors(self) -> BaseGameSelectors:
        return BaseGameSelectors(
            game_url="https://bc.game/game/crash",
            iframe_selector="",
            container_selector="#game-full-container",
            stake_input_selector="#NumberField-cl-7 input, input[name='amount'], .game-coininput input",
            bet_button_selector="#game-full-container button.button-brand, button:has-text('Bet')",
            auto_tab_selector='#game-full-container button:has-text("Auto"), .game-tabs button:nth-child(2)',
            auto_cashout_switch_selector='#game-full-container input[type="checkbox"], #game-full-container .switch',
            auto_cashout_selector="#NumberField-cl-9 input, input[name='payout']",
            multiplier_selector="#game-full-container .z-20 .font-extrabold, .game-scale",
            round_result_selector="#crash-banner .font-extrabold, .game-banner",
            history_multiplier_selector="#crash-banner .font-extrabold, .recent-list .item",
            login_selector='#game-full-container button:has-text("Log In")',
        )

    def prepare_game(self, page_or_root: Any, base_stake: float, auto_cashout: float) -> bool:
        """Prepare BC.Game Auto tab and cashout target."""
        try:
            # 1. Switch to Auto tab if available
            auto_btn = page_or_root.locator(self.selectors.auto_tab_selector).first
            if auto_btn.is_visible():
                auto_btn.click()
                time.sleep(0.3)

            # 2. Fill Auto Cashout target
            co_inp = page_or_root.locator(self.selectors.auto_cashout_selector).first
            if co_inp.is_visible():
                co_inp.click()
                co_inp.fill(f"{auto_cashout:.2f}")

            # 3. Fill Base Stake
            stake_inp = page_or_root.locator(self.selectors.stake_input_selector).first
            if stake_inp.is_visible():
                stake_inp.click()
                stake_inp.fill(f"{base_stake:.2f}")

            return True
        except Exception:
            return False

    def wait_for_betting_window(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> bool:
        """Wait for the countdown window before the rocket launches."""
        while not stop_requested():
            try:
                btn = page_or_root.locator(self.selectors.bet_button_selector).first
                if btn.is_visible():
                    txt = btn.inner_text().strip().lower()
                    if "bet" in txt and "cashing" not in txt:
                        return True
            except Exception:
                pass
            time.sleep(0.15)
        return False

    def place_bet(self, page_or_root: Any, stake: float, auto_cashout: float) -> None:
        """Type stake and click Bet button."""
        time.sleep(random.uniform(0.15, 0.35))
        stake_inp = page_or_root.locator(self.selectors.stake_input_selector).first
        if stake_inp.is_visible():
            stake_inp.fill(f"{stake:.2f}")
        btn = page_or_root.locator(self.selectors.bet_button_selector).first
        btn.click()

    def wait_for_result(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> float | None:
        """Wait for round completion and return multiplier."""
        start_time = time.monotonic()
        last_m = None
        while not stop_requested() and time.monotonic() - start_time < 90.0:
            try:
                res_elem = page_or_root.locator(self.selectors.round_result_selector).first
                if res_elem.is_visible():
                    txt = res_elem.inner_text().strip()
                    m = parse_multiplier(txt)
                    if m is not None:
                        last_m = m
                        break
            except Exception:
                pass
            time.sleep(0.2)
        return last_m or 1.0

    def extract_recent_multipliers(self, page_or_root: Any, count: int = 10) -> list[float]:
        """Scrape history ribbon items."""
        try:
            items = page_or_root.locator(self.selectors.history_multiplier_selector)
            cnt = items.count() if hasattr(items, "count") else 0
            results = []
            for i in range(min(cnt, count)):
                el = items.nth(i)
                if el.is_visible():
                    m = parse_multiplier(el.inner_text().strip())
                    if m is not None:
                        results.append(m)
            return results
        except Exception:
            return []
