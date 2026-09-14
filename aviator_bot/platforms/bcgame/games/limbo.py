from __future__ import annotations

import random
import time
from typing import Callable, Any

from aviator_bot.platforms.base.enums import GameCategory
from aviator_bot.platforms.base.selectors import BaseGameSelectors
from aviator_bot.platforms.base.game_base import BaseGameAddon
from aviator_bot.browser.detector import parse_multiplier


class BCGameLimboGame(BaseGameAddon):
    """BC.Game Limbo game addon."""

    @property
    def game_id(self) -> str:
        return "limbo"

    @property
    def display_name(self) -> str:
        return "BC Limbo"

    @property
    def category(self) -> GameCategory:
        return GameCategory.LIMBO

    def default_selectors(self) -> BaseGameSelectors:
        return BaseGameSelectors(
            game_url="https://bc.game/game/limbo",
            iframe_selector="",
            container_selector="#game-full-container",
            stake_input_selector="input[name='amount'], .game-coininput input",
            bet_button_selector="#game-full-container button.button-brand",
            auto_tab_selector='#game-full-container button:has-text("Auto")',
            auto_cashout_selector="input[name='payout'], input.target-multiplier",
            multiplier_selector=".limbo-multiplier, .game-scale",
            round_result_selector=".limbo-result, .game-scale",
            history_multiplier_selector=".recent-list .item",
        )

    def prepare_game(self, page_or_root: Any, base_stake: float, auto_cashout: float) -> bool:
        try:
            target_inp = page_or_root.locator(self.selectors.auto_cashout_selector).first
            if target_inp.is_visible():
                target_inp.click()
                t_str = f"{auto_cashout:.4f}".rstrip('0')
                if t_str.endswith('.'):
                    t_str += '00'
                elif len(t_str.split('.')[1]) == 1:
                    t_str += '0'
                target_inp.fill(t_str)
            stake_inp = page_or_root.locator(self.selectors.stake_input_selector).first
            if stake_inp.is_visible():
                stake_inp.click()
                stake_inp.fill(f"{base_stake:.2f}")
            return True
        except Exception:
            return False

    def wait_for_betting_window(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> bool:
        time.sleep(0.1)
        return not stop_requested()

    def place_bet(self, page_or_root: Any, stake: float, auto_cashout: float) -> None:
        time.sleep(random.uniform(0.15, 0.35))
        stake_inp = page_or_root.locator(self.selectors.stake_input_selector).first
        if stake_inp.is_visible():
            stake_inp.fill(f"{stake:.2f}")
        btn = page_or_root.locator(self.selectors.bet_button_selector).first
        btn.click()

    def wait_for_result(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> float | None:
        time.sleep(random.uniform(0.3, 0.6))
        try:
            res_elem = page_or_root.locator(self.selectors.round_result_selector).first
            if res_elem.is_visible():
                m = parse_multiplier(res_elem.inner_text().strip())
                if m is not None:
                    return m
        except Exception:
            pass
        return 1.0

    def extract_recent_multipliers(self, page_or_root: Any, count: int = 10) -> list[float]:
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
