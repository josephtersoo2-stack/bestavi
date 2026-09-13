"""Built-in selector profiles for supported crash-game sites.

Profiles are intentionally read-only/paper-trading oriented.  The live adapter
still requires explicit selectors, but the dashboard and CLI use these profiles
to observe the right DOM on each site.
"""

from __future__ import annotations

from dataclasses import replace

from .settings import BrowserSelectors


SITE_NAMES = {"ilotbet": "iLOTBET", "bcgame": "BC.Game"}


def profile(name: str, base: BrowserSelectors | None = None) -> BrowserSelectors:
    key = name.strip().lower().replace(".", "")
    current = base or BrowserSelectors()
    if key in {"bcgame", "bc"}:
        return replace(
            current,
            url=current.url or "https://bc.game/game/crash",
            user_data_dir="data/browser_profile_bcgame",
            iframe_selector="",
            betting_window_selector="#game-full-container button.button-brand",
            stake_input_selector="#NumberField-cl-7 input",
            bet_button_selector="#game-full-container button.button-brand",
            auto_tab_selector='#game-full-container button:has-text("Auto")',
            auto_cashout_switch_selector='#game-full-container input[type="checkbox"], #game-full-container .switch',
            auto_cashout_selector="#NumberField-cl-9 input",
            multiplier_selector="#game-full-container .z-20 .font-extrabold",
            round_result_selector="#crash-banner .font-extrabold",
            # The canvas is always mounted, so phase is inferred from the
            # overlay text (numeric multiplier vs. "Crashed") and Bet button.
            live_phase_selector="",
            crashed_phase_selector="#game-full-container .z-20 .font-extrabold",
            history_multiplier_selector="#crash-banner .font-extrabold",
            login_selector='#game-full-container button:has-text("Log In")',
        )
    return replace(
        current,
        user_data_dir=current.user_data_dir or "data/browser_profile",
        iframe_selector="iframe#iframe",
        betting_window_selector=".bet-button, .bet-button-container, .bet-area-right, .awaiting",
        stake_input_selector=".bet-amount-input",
        bet_button_selector=".bet-button",
        auto_tab_selector=".common-tabs-container .tab-item:nth-child(2), .navigation-switcher .tab:nth-child(2), button:has-text('Auto'), .tab-item:has-text('Auto')",
        auto_cashout_switch_selector=".auto-area-right .common-switch, .auto-area-right .switch, app-cash-out-switcher .input-switch, .cash-out-switcher .input-switch",
        auto_cashout_selector=".auto-area-right input.cash-out-odds-input, .cash-out-odds-input, input.cash-out-odds-input, app-cash-out-switcher input",
        multiplier_selector=".odds-box-value, .odds-live-bg, .odds-box",
        round_result_selector=".odds-box-value, .history-odds-item",
        live_phase_selector=".odds-live-bg, .odds-box-value",
        history_multiplier_selector=".history-odds-item",
    )

