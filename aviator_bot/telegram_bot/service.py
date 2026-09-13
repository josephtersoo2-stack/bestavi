from __future__ import annotations

import logging
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import os
from aviator_bot.bot.controller import BotController
from aviator_bot.browser.controller import DryRunAdapter, PlaywrightAdapter
from aviator_bot.config.settings import BotSettings, load_settings, save_settings
from aviator_bot.config.site_profiles import profile
from aviator_bot.database.history import SQLiteHistory
from aviator_bot.strategy.engine import calculate_loss_multiplier
from aviator_bot.security.crypto import sanitize_log_message
from .client import TelegramClient

logger = logging.getLogger(__name__)


def make_main_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "🚀 1. Prepare Game"}, {"text": "▶ 2. Start Staking"}],
            [{"text": "⏸ Stop Staking"}, {"text": "📊 Status & Balance"}],
            [{"text": "📥 Export CSV"}, {"text": "📥 Export TXT"}],
            [{"text": "⚙ Settings"}, {"text": "❓ Help"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }


class TelegramBotService:
    """Telegram Remote Control Service for Aviator Auto Stake Bot."""

    def __init__(self, settings_path: str | Path) -> None:
        self.settings_path = Path(settings_path)
        self.settings: BotSettings = load_settings(self.settings_path)
        self.client = TelegramClient(self.settings.telegram_token)
        self.allowed_chat_id = str(self.settings.telegram_chat_id).strip() if self.settings.telegram_chat_id else ""
        self.pairing_pin = os.getenv("TELEGRAM_PAIRING_PIN", "").strip()
        self.controller: BotController | None = None
        self.history = SQLiteHistory(self.settings.database_path)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._offset = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="telegram-bot", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self.controller and self.controller.running:
            self.controller.stop()
        self.history.close()

    def _notify(self, message: str, reply_markup: dict[str, Any] | None = None) -> None:
        if not self.allowed_chat_id or not self.client.is_configured():
            return
        try:
            clean_msg = sanitize_log_message(message)
            self.client.send_message(self.allowed_chat_id, clean_msg, reply_markup=reply_markup)
        except Exception as exc:
            logger.error("Failed to send Telegram message: %s", sanitize_log_message(str(exc)))

    def _on_controller_event(self, event: str | tuple) -> None:
        if isinstance(event, str):
            if event.startswith("Bet placed:"):
                self._notify(f"🎯 <b>{event}</b>")
            elif event.startswith("Result"):
                is_win = "+" in event
                emoji = "🟢" if is_win else "🔴"
                self._notify(f"{emoji} <b>{event}</b>\nNext stake: <b>{self.controller.current_stake:.2f} NGN</b>" if self.controller else f"{emoji} <b>{event}</b>")
            elif event.startswith("Risk stop:"):
                self._notify(f"⚠️ <b>{event}</b>\nLive staking paused by risk manager.")
            elif event.startswith("Ready! Auto tab selected") or event == "prepare_done":
                bal_val = self.controller.risk.balance if (self.controller and self.controller.risk.balance is not None) else None
                bal_str = f"<b>₦{bal_val:,.2f}</b>" if bal_val is not None else "<b>(Live Synced)</b>"
                self._notify(
                    f"✅ <b>Game Prepared & Observer Active!</b>\n\n"
                    f"• 💰 <b>Account Balance:</b> {bal_str}\n"
                    f"• 🎯 <b>Base Stake:</b> <b>{self.settings.base_stake:.2f} NGN</b>\n"
                    f"• ⚡ <b>Auto Cash Out:</b> <b>{self.settings.auto_cashout:.2f}x</b>\n"
                    f"• ✖️ <b>Loss Multiplier:</b> <b>{self.settings.multiplier}x</b>\n"
                    f"• 📡 <b>Observer:</b> <code>ACTIVE (Extracting & Saving Crash Data)</code>\n\n"
                    f"Tap <b>▶ 2. Start Staking</b> to begin live automated betting.",
                    reply_markup=make_main_keyboard()
                )
            elif event == "Preparing game interface...":
                self._notify("⏳ <b>Setting up game controls (Auto Tab & Cash Out)...</b>")
            elif event == "Connected":
                self._notify("🔌 <b>Connected to game page.</b>")
            elif event.startswith("Notice:"):
                self._notify(f"ℹ️ <b>{event}</b>")
            elif event.startswith("Error:"):
                self._notify(f"❌ <b>{event}</b>")

    def _run_loop(self) -> None:
        logger.info("Telegram Bot loop started.")
        while not self._stop_event.is_set():
            try:
                updates = self.client.get_updates(offset=self._offset, timeout=10)
                for update in updates:
                    self._offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue
                    self._handle_message(message)
            except Exception as exc:
                logger.error("Telegram polling error: %s", sanitize_log_message(str(exc)))
                time.sleep(3)

    def _handle_message(self, message: dict[str, Any]) -> None:
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        text = str(message.get("text", "")).strip()

        # Grade-A Authorization & Pairing Defense
        if not self.allowed_chat_id:
            if self.pairing_pin:
                if text == self.pairing_pin:
                    self.allowed_chat_id = chat_id
                    self.settings = replace(self.settings, telegram_chat_id=chat_id)
                    save_settings(self.settings, self.settings_path)
                    self.client.send_message(
                        chat_id,
                        f"🎉 <b>Authentication Successful!</b>\nYour Chat ID <code>{chat_id}</code> is now paired as administrator.",
                        reply_markup=make_main_keyboard(),
                    )
                    return
                else:
                    self.client.send_message(
                        chat_id,
                        "🔐 <b>Authentication Required</b>\nPlease reply with your 6-digit Security PIN to pair with this bot."
                    )
                    return
            else:
                self.allowed_chat_id = chat_id
                self.settings = replace(self.settings, telegram_chat_id=chat_id)
                save_settings(self.settings, self.settings_path)
                self.client.send_message(
                    chat_id,
                    f"🎉 <b>Telegram Bot Paired!</b>\nYour Chat ID <code>{chat_id}</code> is now the authorized administrator.",
                    reply_markup=make_main_keyboard(),
                )
        elif str(chat_id) != str(self.allowed_chat_id):
            self.client.send_message(chat_id, "⛔ <b>Access Denied</b>. This bot is private.")
            return

        if not text:
            return

        cmd = text.lower()
        if cmd in {"/start", "/menu", "❓ help", "/help"}:
            help_text = (
                "✈️ <b>Aviator Mobile Assistant Bot</b>\n\n"
                "<b>Controls:</b>\n"
                "• <b>🚀 1. Prepare Game</b> - Connects & sets Auto Cash Out / Base Stake\n"
                "• <b>▶ 2. Start Staking</b> - Authorizes live staking cycle\n"
                "• <b>⏸ Stop Staking</b> - Pauses staking safely (keeps extracting data)\n"
                "• <b>📊 Status & Balance</b> - View live state & statistics\n"
                "• <b>📥 Export CSV / TXT</b> - Download latest crash datasets\n\n"
                "<b>Quick Parameter Commands:</b>\n"
                "• <code>/stake 50</code> - Change base stake (NGN)\n"
                "• <code>/cashout 1.50</code> - Change auto cashout odds\n"
                "• <code>/multiplier 3.0</code> - Change loss multiplier\n"
                "• <code>/strategy martingale</code> - Change strategy\n"
                "• <code>/max_losses 5</code> - Max loss streak limit\n"
                "• <code>/stop_loss 10000</code> - Stop loss limit\n"
                "• <code>/profit_target 5000</code> - Profit target\n"
                "• <code>/url &lt;URL&gt;</code> - Update game link"
            )
            self.client.send_message(chat_id, help_text, reply_markup=make_main_keyboard())
            return

        if cmd in {"🚀 1. prepare game", "/prepare"}:
            self._cmd_prepare(chat_id)
            return

        if cmd in {"▶ 2. start staking", "/start_staking", "/stake_start"}:
            self._cmd_start_staking(chat_id)
            return

        if cmd in {"⏸ stop staking", "/stop", "/pause"}:
            self._cmd_stop_staking(chat_id)
            return

        if cmd in {"📊 status & balance", "📊 status", "/status", "/stats"}:
            self._cmd_status(chat_id)
            return

        if cmd in {"📥 export csv", "/export_csv", "/csv"}:
            self._cmd_export(chat_id, "csv")
            return

        if cmd in {"📥 export txt", "/export_txt", "/txt", "/export"}:
            self._cmd_export(chat_id, "txt")
            return

        if cmd in {"⚙ settings", "/settings"}:
            self._cmd_settings(chat_id)
            return

        # Parameter Updates
        if cmd.startswith("/stake"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    val = float(parts[1])
                    self.settings = replace(self.settings, base_stake=val)
                    save_settings(self.settings, self.settings_path)
                    if self.controller and self.controller.running:
                        self.controller.update_settings(self.settings)
                    self.client.send_message(chat_id, f"✅ Base stake updated to <b>{val:.2f} NGN</b>")
                except ValueError:
                    self.client.send_message(chat_id, "❌ Invalid stake value. Example: <code>/stake 50</code>")
            return

        if cmd.startswith("/cashout"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    val = float(parts[1])
                    if val <= 1.0:
                        self.client.send_message(chat_id, "❌ Cashout odds must be greater than 1.00x")
                        return
                    suggested_mult = calculate_loss_multiplier(val)
                    self.settings = replace(self.settings, auto_cashout=val, multiplier=suggested_mult)
                    save_settings(self.settings, self.settings_path)
                    if self.controller and self.controller.running:
                        self.controller.update_settings(self.settings)
                    self.client.send_message(
                        chat_id,
                        f"✅ Auto cashout set to <b>{val:.2f}x</b>\nAuto-adjusted Martingale loss multiplier to <b>{suggested_mult}x</b>",
                    )
                except ValueError:
                    self.client.send_message(chat_id, "❌ Invalid cashout value. Example: <code>/cashout 1.50</code>")
            return

        if cmd.startswith("/multiplier"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    val = float(parts[1])
                    self.settings = replace(self.settings, multiplier=val)
                    save_settings(self.settings, self.settings_path)
                    if self.controller and self.controller.running:
                        self.controller.update_settings(self.settings)
                    self.client.send_message(chat_id, f"✅ Loss multiplier set to <b>{val}x</b>")
                except ValueError:
                    self.client.send_message(chat_id, "❌ Invalid multiplier. Example: <code>/multiplier 3.0</code>")
            return

        if cmd.startswith("/url"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                new_url = parts[1].strip()
                browser_selectors = replace(self.settings.browser, url=new_url)
                self.settings = replace(self.settings, browser=browser_selectors)
                save_settings(self.settings, self.settings_path)
                self.client.send_message(chat_id, f"✅ Game URL updated.")
            return

        self.client.send_message(chat_id, "❓ Unknown command. Tap <b>❓ Help</b> or choose an option below.", reply_markup=make_main_keyboard())

    def _cmd_prepare(self, chat_id: str) -> None:
        try:
            self.settings = load_settings(self.settings_path)
            browser_settings = replace(self.settings, dry_run=self.settings.dry_run, paper_trade=False)
            self.client.send_message(chat_id, "⏳ <b>Connecting browser and preparing game controls...</b>")

            if self.controller and self.controller.running:
                self.controller.update_settings(browser_settings)
            else:
                adapter = DryRunAdapter() if self.settings.dry_run else PlaywrightAdapter(browser_settings.browser)
                self.controller = BotController(settings=browser_settings, adapter=adapter, on_event=self._on_controller_event)
                self.controller.start(authorized=False)
        except Exception as exc:
            self.client.send_message(chat_id, f"❌ <b>Preparation Error:</b> {exc}")

    def _cmd_start_staking(self, chat_id: str) -> None:
        try:
            self.settings = load_settings(self.settings_path)
            if self.controller and self.controller.running:
                self.controller.update_settings(self.settings)
                self.controller.authorize()
                self.client.send_message(
                    chat_id,
                    f"🚀 <b>Live Staking Started!</b>\n"
                    f"• Base Stake: <b>{self.settings.base_stake:.2f} NGN</b>\n"
                    f"• Auto Cashout: <b>{self.settings.auto_cashout:.2f}x</b>\n"
                    f"• Loss Multiplier: <b>{self.settings.multiplier}x</b>\n"
                    f"• Strategy: <b>{self.settings.strategy.upper()}</b>",
                    reply_markup=make_main_keyboard(),
                )
            else:
                adapter = DryRunAdapter() if self.settings.dry_run else PlaywrightAdapter(self.settings.browser)
                self.controller = BotController(settings=self.settings, adapter=adapter, on_event=self._on_controller_event)
                self.controller.start(authorized=True)
                self.client.send_message(chat_id, "🚀 <b>Starting bot and live staking cycle...</b>", reply_markup=make_main_keyboard())
        except Exception as exc:
            self.client.send_message(chat_id, f"❌ <b>Error:</b> {exc}")

    def _cmd_stop_staking(self, chat_id: str) -> None:
        if self.controller and self.controller.running:
            self.controller.pause_staking()
            self.client.send_message(
                chat_id,
                "⏸ <b>Staking Paused!</b>\nLive betting is stopped safely at the end of the round. Continuous data extraction is still active.",
                reply_markup=make_main_keyboard(),
            )
        else:
            self.client.send_message(chat_id, "ℹ️ Bot is not currently staking.", reply_markup=make_main_keyboard())

    def _cmd_status(self, chat_id: str) -> None:
        bal_val = self.controller.risk.balance if (self.controller and self.controller.risk.balance is not None) else None
        state = self.controller.state if self.controller else "IDLE"
        current_stake = f"{self.controller.current_stake:.2f} NGN" if self.controller else f"{self.settings.base_stake:.2f} NGN"
        loss_streak = self.controller.risk.loss_streak if self.controller else 0
        bal_str = f"₦{bal_val:,.2f}" if bal_val is not None else "Not Connected (Tap 🚀 1. Prepare Game)"
        recent_live = self.controller.recent_live_multipliers if (self.controller and self.controller.recent_live_multipliers) else []
        if recent_live:
            multipliers_str = " | ".join(f"<b>{m:.2f}x</b>" for m in recent_live[:8])
        else:
            recent_db = self.history.recent_observations(5, site=self.settings.site)
            multipliers_str = " | ".join(f"{r['multiplier']:.2f}x" for r in recent_db if r.get("multiplier")) or "None yet"

        msg = (
            f"📊 <b>Bot & Account Status</b>\n\n"
            f"• 💰 <b>Account Balance:</b> <b>{bal_str}</b>\n"
            f"• 🚦 <b>State:</b> <code>{state}</code>\n"
            f"• 🎯 <b>Current Next Stake:</b> <b>{current_stake}</b>\n"
            f"• 📉 <b>Current Loss Streak:</b> <b>{loss_streak}</b> / {self.settings.max_loss_steps}\n"
            f"• ⚡ <b>Auto Cashout:</b> <b>{self.settings.auto_cashout:.2f}x</b>\n"
            f"• ✖️ <b>Loss Multiplier:</b> <b>{self.settings.multiplier}x</b>\n"
            f"• 📡 <b>Live Observer:</b> <code>{'ACTIVE (Recording)' if (self.controller and self.controller.running) else 'STANDBY'}</code>\n\n"
            f"📈 <b>Live Game Multipliers:</b>\n{multipliers_str}"
        )
        self.client.send_message(chat_id, msg, reply_markup=make_main_keyboard())

    def _cmd_settings(self, chat_id: str) -> None:
        self.settings = load_settings(self.settings_path)
        msg = (
            f"⚙️ <b>Current Configuration</b>\n\n"
            f"• <b>Platform:</b> <code>{self.settings.site}</code>\n"
            f"• <b>Base Stake:</b> <code>{self.settings.base_stake:.2f} NGN</code>\n"
            f"• <b>Auto Cashout:</b> <code>{self.settings.auto_cashout:.2f}x</code>\n"
            f"• <b>Loss Multiplier:</b> <code>{self.settings.multiplier}x</code>\n"
            f"• <b>Strategy:</b> <code>{self.settings.strategy}</code>\n"
            f"• <b>Max Stake:</b> <code>{self.settings.max_stake:.2f} NGN</code>\n"
            f"• <b>Max Loss Steps:</b> <code>{self.settings.max_loss_steps}</code>\n"
            f"• <b>Stop Loss:</b> <code>{self.settings.stop_loss:.2f} NGN</code>\n"
            f"• <b>Profit Target:</b> <code>{self.settings.profit_target:.2f} NGN</code>\n"
            f"• <b>Mode:</b> <code>{'Dry Run' if self.settings.dry_run else 'Live Real Bets'}</code>\n"
        )
        self.client.send_message(chat_id, msg, reply_markup=make_main_keyboard())

    def _cmd_export(self, chat_id: str, fmt: str) -> None:
        try:
            site = self.settings.site
            content = self.history.export_observations(fmt, site=site, limit=1000)
            data_dir = Path("data")
            data_dir.mkdir(parents=True, exist_ok=True)
            export_path = data_dir / f"{site}_crash_history.{fmt}"
            export_path.write_text(content, encoding="utf-8")

            caption = f"📊 {site.upper()} Aviator Crash Dataset ({fmt.upper()})"
            res = self.client.send_document(chat_id, export_path, caption=caption)
            if not res:
                self.client.send_message(chat_id, f"📄 <b>Dataset Content:</b>\n<pre>{content[:1500]}</pre>")
        except Exception as exc:
            self.client.send_message(chat_id, f"❌ Export failed: {exc}")
