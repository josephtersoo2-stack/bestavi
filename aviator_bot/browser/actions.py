import random
import time


def setup_auto_cashout_tab(card_or_page: object, auto_tab_selector: str,
                           switch_selector: str, cashout_selector: str,
                           target_odds: float) -> bool:
    """Ensure the 'Auto' tab is selected, 'Auto Cash Out' switch is toggled ON, and odds are set.
    Also ensures 'Auto Bet' switch is turned OFF so the bot controls staking.
    """
    try:
        # 1. Activate Auto Tab
        auto_tab = None
        for sel in [
            ".common-tabs-container .tab-item",
            "button:has-text('Auto')",
            ".tab-item:has-text('Auto')",
            ".tab:has-text('Auto')",
        ]:
            try:
                candidates = card_or_page.locator(sel)
                count = candidates.count() if hasattr(candidates, "count") else 0
                if count >= 2 and "tab-item" in sel:
                    auto_tab = candidates.nth(1)
                    break
                elif count >= 1:
                    auto_tab = candidates.first
                    break
            except Exception:
                continue

        if auto_tab is not None and auto_tab.is_visible():
            cls = auto_tab.get_attribute("class") or ""
            if "active" not in cls and "selected" not in cls:
                auto_tab.click()
                time.sleep(0.3)

        # 2. Toggle Auto Cash Out switch ON
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
                sw = card_or_page.locator(sel).first
                if sw.is_visible():
                    co_switch = sw
                    break
            except Exception:
                continue

        if co_switch is not None:
            cls = co_switch.get_attribute("class") or ""
            if "off" in cls or not any(x in cls for x in ["on", "active", "checked"]):
                co_switch.click()
                time.sleep(0.3)

        # 3. Ensure Auto Bet switch is OFF
        ab_switch = None
        for sel in [
            ".auto-area-left .common-switch",
            ".auto-area-left .switch",
            "app-auto-bet-switcher .input-switch",
            ":has-text('Auto Bet') .common-switch",
        ]:
            try:
                sw = card_or_page.locator(sel).first
                if sw.is_visible():
                    ab_switch = sw
                    break
            except Exception:
                continue

        if ab_switch is not None:
            ab_cls = ab_switch.get_attribute("class") or ""
            if "off" not in ab_cls and any(x in ab_cls for x in ["on", "active", "checked"]):
                ab_switch.click()
                time.sleep(0.2)

        # 4. Fill Auto Cash Out Odds Target (e.g. 1.50 or 1.33)
        target_str = f"{target_odds:.4f}".rstrip('0')
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
            "input.font-weight-bold",
        ]:
            try:
                inp = card_or_page.locator(inp_sel).first
                if inp.is_visible():
                    val = inp.input_value() if hasattr(inp, "input_value") else ""
                    if val != target_str:
                        inp.click()
                        inp.fill(target_str)
                    break
            except Exception:
                continue

        return True
    except Exception:
        return False


def place_bet_on_page(page: object, stake_selector: str, button_selector: str, stake: float,
                      human_delay: bool = True, min_delay: float = 1.0, max_delay: float = 2.5) -> None:
    """Fill stake input and click BET button with human-simulated keystrokes and reaction timing."""
    if human_delay and max_delay >= min_delay > 0:
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    formatted = f"{int(stake)}" if stake.is_integer() else f"{stake:.2f}"
    input_elem = page.locator(stake_selector).first
    try:
        current_val = input_elem.input_value() if hasattr(input_elem, "input_value") else ""
        if current_val != formatted:
            input_elem.click()
            if human_delay:
                input_elem.fill("")
                input_elem.press_sequentially(formatted, delay=random.randint(35, 75))
                time.sleep(random.uniform(0.15, 0.35))
            else:
                input_elem.fill(formatted)
    except Exception:
        try:
            input_elem.fill(formatted)
        except Exception:
            pass

    button_elem = page.locator(button_selector).first
    try:
        box = button_elem.bounding_box()
        if box:
            bx = int(box["x"] + box["width"] / 2)
            by = int(box["y"] + box["height"] / 2)
            try:
                page.evaluate(f"() => {{ if (window.__moveVirtualCursor) window.__moveVirtualCursor({bx}, {by}); if (window.__pulseVirtualCursor) window.__pulseVirtualCursor(); }}")
            except Exception:
                pass
    except Exception:
        pass

    if human_delay:
        time.sleep(random.uniform(0.15, 0.35))

    button_elem.click()

