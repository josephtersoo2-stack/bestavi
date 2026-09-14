from __future__ import annotations

import math
import random
import time
from typing import Callable, Any

from aviator_bot.platforms.base.enums import GameCategory
from aviator_bot.platforms.base.selectors import BaseGameSelectors
from aviator_bot.platforms.base.game_base import BaseGameAddon
from aviator_bot.browser.detector import parse_multiplier


class ILotBetAviatorGame(BaseGameAddon):
    """Best Aviator crash game hosted on iLotBet inside iframe#iframe."""

    @property
    def game_id(self) -> str:
        return "best_aviator"

    @property
    def aliases(self) -> tuple[str, ...]:
        return ("aviator",)

    @property
    def display_name(self) -> str:
        return "Best Aviator (iLotBet)"

    @property
    def category(self) -> GameCategory:
        return GameCategory.CRASH

    def default_selectors(self) -> BaseGameSelectors:
        return BaseGameSelectors(
            game_url="https://www.ilotbet.com/pc/iframe",
            iframe_selector="iframe#iframe",
            container_selector=".bet-box",
            stake_input_selector=".bet-amount-input",
            bet_button_selector=".bet-button",
            auto_tab_selector=".common-tabs-container .tab-item:nth-child(2), .navigation-switcher .tab:nth-child(2), button:has-text('Auto'), .tab-item:has-text('Auto')",
            auto_cashout_switch_selector=".auto-area-right .common-switch, .auto-area-right .switch, app-cash-out-switcher .input-switch, .cash-out-switcher .input-switch",
            auto_cashout_selector=".auto-area-right input.cash-out-odds-input, .cash-out-odds-input, input.cash-out-odds-input, app-cash-out-switcher input",
            multiplier_selector=".odds-box-value, .odds-live-bg, .odds-box",
            round_result_selector=".odds-box-value, .history-odds-item",
            history_multiplier_selector=".history-odds-item, .bubble-multiplier, app-stats-item .bubble-multiplier",
        )

    def prepare_game(self, page_or_root: Any, base_stake: float, auto_cashout: float) -> bool:
        """Set up in-game Auto tab, toggle Auto Cash Out switch ON, fill odds target, and set base stake."""
        try:
            # 1. Resolve bet card container
            card = page_or_root.locator(".bet-box").first if hasattr(page_or_root, "locator") else page_or_root

            # 2. Select Auto tab
            auto_tab = None
            for sel in [
                ".common-tabs-container .tab-item",
                "button:has-text('Auto')",
                ".tab-item:has-text('Auto')",
                ".tab:has-text('Auto')",
            ]:
                try:
                    candidates = card.locator(sel)
                    cnt = candidates.count() if hasattr(candidates, "count") else 0
                    if cnt >= 2 and "tab-item" in sel:
                        auto_tab = candidates.nth(1)
                        break
                    elif cnt >= 1:
                        auto_tab = candidates.first
                        break
                except Exception:
                    continue

            if auto_tab and auto_tab.is_visible():
                cls = auto_tab.get_attribute("class") or ""
                if "active" not in cls and "selected" not in cls:
                    auto_tab.click()
                    time.sleep(0.3)

            # 3. Toggle Auto Cash Out switch ON
            co_switch = None
            for sel in [
                ".auto-area-right .common-switch",
                ".auto-area-right .switch",
                "app-cash-out-switcher .input-switch",
                "app-cash-out-switcher app-switcher",
                ".cash-out-switcher .input-switch",
                ".cash-out-switcher app-switcher",
                ":has-text('Auto Cash Out') .common-switch",
                ":has-text('Auto Cash Out') .input-switch",
            ]:
                try:
                    sw = card.locator(sel).first
                    if sw.is_visible():
                        co_switch = sw
                        break
                except Exception:
                    continue

            if co_switch:
                cls = co_switch.get_attribute("class") or ""
                if "off" in cls or not any(x in cls for x in ["on", "active", "checked"]):
                    co_switch.click()
                    time.sleep(0.3)

            # 4. Turn Auto Bet switch OFF
            for sel in [
                ".auto-area-left .common-switch",
                ".auto-area-left .switch",
                "app-auto-bet-switcher .input-switch",
                ":has-text('Auto Bet') .common-switch",
            ]:
                try:
                    ab = card.locator(sel).first
                    if ab.is_visible():
                        ab_cls = ab.get_attribute("class") or ""
                        if "off" not in ab_cls and any(x in ab_cls for x in ["on", "active", "checked"]):
                            ab.click()
                            time.sleep(0.2)
                        break
                except Exception:
                    continue

            # 5. Fill target auto cashout odds (e.g. 1.50 or 1.33)
            target_str = f"{auto_cashout:.4f}".rstrip('0')
            if target_str.endswith('.'):
                target_str += '00'
            elif len(target_str.split('.')[1]) == 1:
                target_str += '0'
            for inp_sel in [
                ".auto-area-right input.cash-out-odds-input",
                ".auto-area-right input",
                "input.cash-out-odds-input",
                "app-cash-out-switcher input",
                ".cash-out-switcher input",
            ]:
                try:
                    inp = card.locator(inp_sel).first
                    if inp.is_visible():
                        val = inp.input_value() if hasattr(inp, "input_value") else ""
                        if val != target_str:
                            inp.click()
                            inp.fill(target_str)
                        break
                except Exception:
                    continue

            # 6. Fill base stake input (Ceiling Rule: ILOTBET does not accept decimal stakes)
            if not float(base_stake).is_integer():
                base_stake = float(math.ceil(base_stake))
            formatted_stake = f"{int(base_stake)}"
            try:
                stake_inp = card.locator(self.selectors.stake_input_selector).first
                if stake_inp.is_visible():
                    stake_inp.click()
                    stake_inp.fill(formatted_stake)
            except Exception:
                pass

            return True
        except Exception:
            return False

    def wait_for_betting_window(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> bool:
        """Wait for live flight to finish and the BET button to become available."""
        card = page_or_root.locator(".bet-box").first if hasattr(page_or_root, "locator") else page_or_root

        # 1. Wait until live plane finishes flight
        while not stop_requested():
            try:
                odds = page_or_root.locator(self.selectors.multiplier_selector).first
                if not (odds.is_visible() if hasattr(odds, "is_visible") else False):
                    break
            except Exception:
                break
            time.sleep(0.1)

        # 2. Wait for BET button to be ready for the new round
        while not stop_requested():
            try:
                btn = card.locator(self.selectors.bet_button_selector).first
                btn_visible = btn.is_visible() if hasattr(btn, "is_visible") else False
                odds = page_or_root.locator(self.selectors.multiplier_selector).first
                odds_visible = odds.is_visible() if hasattr(odds, "is_visible") else False
                if btn_visible and not odds_visible:
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def place_bet(self, page_or_root: Any, stake: float, auto_cashout: float) -> None:
        """Fill stake input and click BET button."""
        card = page_or_root.locator(".bet-box").first if hasattr(page_or_root, "locator") else page_or_root
        # Ceiling Rule: ILOTBET blocks decimal staking. Always round UP to next whole integer.
        if not float(stake).is_integer():
            stake = float(math.ceil(stake))
        formatted = f"{int(stake)}"

        # Human-like delay
        time.sleep(random.uniform(0.15, 0.35))

        inp = card.locator(self.selectors.stake_input_selector).first
        try:
            curr = inp.input_value() if hasattr(inp, "input_value") else ""
            if curr != formatted:
                inp.click()
                inp.fill("")
                inp.press_sequentially(formatted, delay=random.randint(30, 60))
        except Exception:
            try:
                inp.fill(formatted)
            except Exception:
                pass

        btn = card.locator(self.selectors.bet_button_selector).first
        btn.click()

    def wait_for_result(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> float | None:
        """Wait for the round flight to start, monitor multiplier, and catch the crash."""
        seen_flying = False
        last_multiplier: float | None = None
        start_time = time.monotonic()

        # Phase 1: Wait for plane takeoff (multiplier element visible)
        while not stop_requested():
            try:
                odds = page_or_root.locator(self.selectors.multiplier_selector).first
                if odds.is_visible():
                    txt = odds.inner_text().strip()
                    parsed = parse_multiplier(txt)
                    if parsed is not None and parsed >= 1.0:
                        last_multiplier = parsed
                    seen_flying = True
                    break
            except Exception:
                pass
            if time.monotonic() - start_time > 60.0:
                break
            time.sleep(0.15)

        # Phase 2: Track until plane crashes (multiplier disappears)
        while not stop_requested():
            try:
                odds = page_or_root.locator(self.selectors.multiplier_selector).first
                if odds.is_visible():
                    txt = odds.inner_text().strip()
                    parsed = parse_multiplier(txt)
                    if parsed is not None and parsed >= 1.0:
                        last_multiplier = parsed
                    seen_flying = True
                else:
                    if seen_flying:
                        break
            except Exception:
                if seen_flying:
                    break
            if time.monotonic() - start_time > 180.0:
                break
            time.sleep(0.15)

        # Small cooldown
        time.sleep(random.uniform(0.8, 1.2))

        # Read the finalized crash value from top history ribbon badge
        try:
            hist = page_or_root.locator(".history-odds-item").first
            if hist.is_visible():
                badge_text = hist.inner_text().strip()
                p = parse_multiplier(badge_text)
                if p is not None:
                    last_multiplier = p
        except Exception:
            pass

        return last_multiplier or 1.0 if not stop_requested() else None

    def extract_recent_multipliers(self, page_or_root: Any, count: int = 10) -> list[float]:
        """Scrape completed round badges from top history ribbon."""
        try:
            loc = page_or_root.locator(".pills, .history-odds-item, .history-item, .bubble-multiplier, app-stats-item .bubble-multiplier")
            total = loc.count() if hasattr(loc, "count") else 0
            results = []
            for i in range(min(total, count)):
                elem = loc.nth(i)
                if elem.is_visible():
                    txt = elem.inner_text().strip()
                    m = parse_multiplier(txt)
                    if m is not None:
                        results.append(m)
            return results
        except Exception:
            return []
