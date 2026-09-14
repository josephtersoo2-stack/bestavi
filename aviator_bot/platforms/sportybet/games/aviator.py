from __future__ import annotations

import random
import time
from typing import Callable, Any

from aviator_bot.platforms.base.enums import GameCategory
from aviator_bot.platforms.base.selectors import BaseGameSelectors
from aviator_bot.platforms.base.game_base import BaseGameAddon
from aviator_bot.browser.detector import parse_multiplier


class SportyBetAviatorGame(BaseGameAddon):
    """Spribe Aviator game hosted on SportyBet."""

    @property
    def game_id(self) -> str:
        return "aviator"

    @property
    def display_name(self) -> str:
        return "SportyBet Aviator"

    @property
    def category(self) -> GameCategory:
        return GameCategory.CRASH

    def default_selectors(self) -> BaseGameSelectors:
        return BaseGameSelectors(
            game_url="https://www.sportybet.com/ng/games/aviator",
            iframe_selector="iframe#game-frame, iframe[src*='spribe'], iframe#iframe",
            container_selector=".bet-box",
            stake_input_selector=".bet-amount-input",
            bet_button_selector=".bet-button",
            auto_tab_selector=".common-tabs-container .tab-item:nth-child(2), button:has-text('Auto')",
            auto_cashout_switch_selector=".auto-area-right .common-switch, .auto-area-right .switch",
            auto_cashout_selector=".auto-area-right input.cash-out-odds-input",
            multiplier_selector=".odds-box-value, .odds-live-bg",
            round_result_selector=".odds-box-value, .history-odds-item",
            history_multiplier_selector=".history-odds-item, .bubble-multiplier",
        )

    def prepare_game(self, page_or_root: Any, base_stake: float, auto_cashout: float) -> bool:
        try:
            card = page_or_root.locator(".bet-box").first if hasattr(page_or_root, "locator") else page_or_root
            auto_tab = card.locator("button:has-text('Auto'), .tab-item:has-text('Auto')").first
            if auto_tab.is_visible():
                auto_tab.click()
                time.sleep(0.3)

            co_switch = card.locator(".auto-area-right .common-switch, .auto-area-right .switch").first
            if co_switch.is_visible():
                cls = co_switch.get_attribute("class") or ""
                if "off" in cls or "checked" not in cls:
                    co_switch.click()
                    time.sleep(0.3)

            target_inp = card.locator(".auto-area-right input.cash-out-odds-input").first
            if target_inp.is_visible():
                t_str = f"{auto_cashout:.4f}".rstrip('0')
                if t_str.endswith('.'):
                    t_str += '00'
                elif len(t_str.split('.')[1]) == 1:
                    t_str += '0'
                target_inp.fill(t_str)

            stake_inp = card.locator(self.selectors.stake_input_selector).first
            if stake_inp.is_visible():
                stake_inp.fill(f"{base_stake:.2f}")

            return True
        except Exception:
            return False

    def wait_for_betting_window(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> bool:
        card = page_or_root.locator(".bet-box").first if hasattr(page_or_root, "locator") else page_or_root
        while not stop_requested():
            try:
                btn = card.locator(self.selectors.bet_button_selector).first
                odds = page_or_root.locator(self.selectors.multiplier_selector).first
                if btn.is_visible() and not odds.is_visible():
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def place_bet(self, page_or_root: Any, stake: float, auto_cashout: float) -> None:
        card = page_or_root.locator(".bet-box").first if hasattr(page_or_root, "locator") else page_or_root
        time.sleep(random.uniform(0.15, 0.35))
        stake_inp = card.locator(self.selectors.stake_input_selector).first
        if stake_inp.is_visible():
            stake_inp.fill(f"{stake:.2f}")
        btn = card.locator(self.selectors.bet_button_selector).first
        btn.click()

    def wait_for_result(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> float | None:
        seen = False
        last_m = None
        start = time.monotonic()
        while not stop_requested() and time.monotonic() - start < 120.0:
            try:
                odds = page_or_root.locator(self.selectors.multiplier_selector).first
                if odds.is_visible():
                    txt = odds.inner_text().strip()
                    m = parse_multiplier(txt)
                    if m is not None:
                        last_m = m
                    seen = True
                elif seen:
                    break
            except Exception:
                if seen:
                    break
            time.sleep(0.15)
        return last_m or 1.0

    def extract_recent_multipliers(self, page_or_root: Any, count: int = 10) -> list[float]:
        try:
            items = page_or_root.locator(self.selectors.history_multiplier_selector)
            cnt = items.count() if hasattr(items, "count") else 0
            res = []
            for i in range(min(cnt, count)):
                el = items.nth(i)
                if el.is_visible():
                    m = parse_multiplier(el.inner_text().strip())
                    if m is not None:
                        res.append(m)
            return res
        except Exception:
            return []
