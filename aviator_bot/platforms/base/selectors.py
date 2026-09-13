from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BaseGameSelectors:
    """Standard locator configuration for a platform game addon."""
    game_url: str = ""
    iframe_selector: str = ""
    container_selector: str = ""
    stake_input_selector: str = ""
    bet_button_selector: str = ""
    auto_tab_selector: str = ""
    auto_cashout_switch_selector: str = ""
    auto_cashout_selector: str = ""
    multiplier_selector: str = ""
    round_result_selector: str = ""
    history_multiplier_selector: str = ""
    balance_selectors: list[str] = field(default_factory=lambda: [
        ".balance-amount",
        ".balance",
        ".balance-container",
        ".user-balance .amount",
        ".user-balance",
        ".balance-value",
        ".amount-bold",
        ".header-balance .amount",
        ".header-balance",
        "span:has-text('NGN')",
        "span:has-text('₦')",
        "span:has-text('$')",
    ])
    login_selector: str = ""
    extra: dict[str, str] = field(default_factory=dict)
