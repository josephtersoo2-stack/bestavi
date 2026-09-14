from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class BrowserSelectors:
    url: str = ""
    headless: bool = False
    user_data_dir: str = "data/browser_profile"
    reconnect_delay_seconds: float = 1.0
    iframe_selector: str = "iframe#iframe"
    betting_window_selector: str = ""
    stake_input_selector: str = ""
    bet_button_selector: str = ""
    auto_tab_selector: str = ""
    auto_cashout_selector: str = ""
    auto_cashout_switch_selector: str = ""
    multiplier_selector: str = ""
    round_result_selector: str = ""
    # Optional site-specific state selectors used by the read-only observer.
    # When unset, the legacy iLOTBET selectors are used for compatibility.
    live_phase_selector: str = ""
    crashed_phase_selector: str = ""
    history_multiplier_selector: str = ""
    login_selector: str = ""
    activity_scroll_enabled: bool = True
    activity_scroll_min_seconds: float = 30.0
    activity_scroll_max_seconds: float = 90.0
    human_delay_enabled: bool = True
    human_delay_min_seconds: float = 0.5
    human_delay_max_seconds: float = 1.8


@dataclass(frozen=True)
class BotSettings:
    base_stake: float = 50.0
    strategy: str = "martingale"
    multiplier: float = 2.0
    auto_cashout: float = 2.0
    max_loss_steps: int = 5
    max_stake: float = 5000.0
    stop_loss: float = 10000.0
    profit_target: float = 5000.0
    starting_balance: float = 100000.0
    database_path: str = "data/round_history.sqlite3"
    dry_run: bool = True
    paper_trade: bool = False
    ceiling_rule: bool = True
    site: str = "ilotbet"
    telegram_token: str = ""
    telegram_chat_id: str = ""
    telegram_notifications: bool = True
    network_auto_retry: bool = True
    network_retry_delay: int = 10
    network_max_retries: int = 5
    browser: BrowserSelectors = BrowserSelectors()

    def validate(self) -> None:
        if self.base_stake <= 0 or self.max_stake <= 0:
            raise ValueError("base_stake and max_stake must be positive")
        if self.base_stake > self.max_stake:
            raise ValueError("base_stake cannot exceed max_stake")
        if self.multiplier <= 1:
            raise ValueError("multiplier must be greater than 1")
        if self.auto_cashout <= 1:
            raise ValueError("auto_cashout must be greater than 1")
        if self.max_loss_steps < 0:
            raise ValueError("max_loss_steps cannot be negative")
        if self.stop_loss < 0 or self.profit_target < 0:
            raise ValueError("stop_loss and profit_target cannot be negative")
        if self.browser.reconnect_delay_seconds < 0:
            raise ValueError("browser.reconnect_delay_seconds cannot be negative")
        if self.browser.activity_scroll_min_seconds <= 0 or self.browser.activity_scroll_max_seconds < self.browser.activity_scroll_min_seconds:
            raise ValueError("activity scroll interval must be positive with max >= min")
        if self.browser.human_delay_min_seconds < 0 or self.browser.human_delay_max_seconds < self.browser.human_delay_min_seconds:
            raise ValueError("human delay interval must be positive with max >= min")


def load_settings(path: str | Path) -> BotSettings:
    import os
    from dataclasses import replace
    from dotenv import load_dotenv
    load_dotenv(Path(path).resolve().parent.parent / '.env')
    path = Path(path)
    if not path.exists():
        settings = BotSettings()
        settings.validate()
        return settings
    raw = json.loads(path.read_text(encoding="utf-8"))
    browser = BrowserSelectors(**raw.pop("browser", {}))
    env_token = os.getenv("TELEGRAM_BOT_TOKEN")
    env_chat = os.getenv("TELEGRAM_CHAT_ID")
    env_url = os.getenv("GAME_URL")
    if env_token:
        raw["telegram_token"] = env_token
    if env_chat:
        raw["telegram_chat_id"] = env_chat
    if env_url:
        browser = replace(browser, url=env_url.strip())
    settings = BotSettings(browser=browser, **raw)
    settings.validate()
    return settings


def save_settings(settings: BotSettings, path: str | Path) -> None:
    settings.validate()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(settings)
    # Grade-A Zero-leak defense: strip sensitive secrets from plaintext JSON file
    data["telegram_token"] = ""
    if "browser" in data and data["browser"].get("url"):
        # If url has active casino session token, do not write token to disk
        if "content=" in data["browser"]["url"].lower():
            data["browser"]["url"] = "https://www.ilotbet.com/pc/iframe"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
