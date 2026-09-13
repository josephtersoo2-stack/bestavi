from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aviator_bot.config.settings import BotSettings, save_settings
from aviator_bot.telegram_bot.client import TelegramClient
from aviator_bot.telegram_bot.service import TelegramBotService, make_main_keyboard


class TelegramTests(unittest.TestCase):

    def test_telegram_client_configuration(self):
        client = TelegramClient("123456:ABC-DEF")
        self.assertTrue(client.is_configured())
        self.assertEqual(client.base_url, "https://api.telegram.org/bot123456:ABC-DEF")

        unconfigured = TelegramClient("")
        self.assertFalse(unconfigured.is_configured())
        self.assertIsNone(unconfigured.send_message("123", "test"))

    def test_main_keyboard_structure(self):
        kb = make_main_keyboard()
        self.assertIn("keyboard", kb)
        self.assertTrue(kb["resize_keyboard"])
        buttons = [btn["text"] for row in kb["keyboard"] for btn in row]
        self.assertIn("🚀 1. Prepare Game", buttons)
        self.assertIn("▶ 2. Start Staking", buttons)
        self.assertIn("⏸ Stop Staking", buttons)
        self.assertIn("📥 Export CSV", buttons)

    def test_telegram_service_pairing_and_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings = BotSettings(
                telegram_token="TEST_TOKEN",
                database_path=str(Path(tmp) / "history.sqlite3"),
                dry_run=True
            )
            save_settings(settings, settings_path)

            service = TelegramBotService(settings_path)
            service.allowed_chat_id = ""
            service.pairing_pin = ""
            try:
                # Mock TelegramClient.send_message
                sent_messages = []
                service.client.send_message = MagicMock(side_effect=lambda cid, text, **kwargs: sent_messages.append((cid, text)))
                service.client.send_document = MagicMock(return_value={"ok": True})

                # 1. Pairing on first message
                service._handle_message({"chat": {"id": "999888"}, "text": "/start"})
                self.assertEqual(service.allowed_chat_id, "999888")
                self.assertIn("Paired", sent_messages[0][1])

                # 2. Status command
                service._handle_message({"chat": {"id": "999888"}, "text": "📊 Status & Balance"})
                self.assertTrue(any("Status" in msg[1] for msg in sent_messages))

                # 3. Dynamic parameter update (/stake 150)
                service._handle_message({"chat": {"id": "999888"}, "text": "/stake 150"})
                self.assertEqual(service.settings.base_stake, 150.0)

                # 4. Dynamic cashout update (/cashout 1.50)
                service._handle_message({"chat": {"id": "999888"}, "text": "/cashout 1.50"})
                self.assertEqual(service.settings.auto_cashout, 1.50)
                self.assertEqual(service.settings.multiplier, 3.0)

                # 5. Export command
                service._handle_message({"chat": {"id": "999888"}, "text": "📥 Export CSV"})
                service.client.send_document.assert_called()
            finally:
                service.stop()


if __name__ == "__main__":
    unittest.main()
