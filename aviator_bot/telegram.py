from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from aviator_bot.telegram_bot.service import TelegramBotService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aviator Auto Stake Bot - Telegram Mobile Controller")
    parser.add_argument("--settings", default="config/settings.json", help="Path to settings JSON file")
    args = parser.parse_args()

    settings_path = Path(args.settings)
    if not settings_path.exists():
        logger.error("Settings file not found: %s", settings_path)
        sys.exit(1)

    service = TelegramBotService(settings_path)
    if not service.client.is_configured():
        print("\n=======================================================")
        print(" [!] TELEGRAM BOT TOKEN REQUIRED")
        print("=======================================================")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow the prompts to create your bot.")
        print("3. Copy your API Token (e.g. 123456789:ABCDefgh...)")
        print("4. Paste the token into config/settings.json under 'telegram_token'\n")
        print("Alternatively, enter your token right now:")
        try:
            token = input("Enter Telegram Bot Token: ").strip()
            if token:
                from aviator_bot.config.settings import load_settings, save_settings
                from dataclasses import replace
                curr = load_settings(settings_path)
                updated = replace(curr, telegram_token=token)
                save_settings(updated, settings_path)
                service = TelegramBotService(settings_path)
            else:
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

    print("\n=======================================================")
    print(" [*] TELEGRAM BOT MOBILE CONTROLLER ACTIVE")
    print("=======================================================")
    print("1. Open Telegram on your mobile phone.")
    print("2. Search for your bot and send: /start")
    print("3. You will receive the interactive control panel on your phone!")
    print("=======================================================\n")

    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Telegram bot service...")
        service.stop()


if __name__ == "__main__":
    main()
