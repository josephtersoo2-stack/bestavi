from __future__ import annotations

import sys
import threading
import time
from enum import Enum
from typing import Callable

from aviator_bot.browser.controller import GameAdapter
from aviator_bot.config.settings import BotSettings
from aviator_bot.database.history import RoundRecord, SQLiteHistory
from aviator_bot.risk.manager import RiskDecision, RiskManager, RiskLimits
from aviator_bot.strategy.engine import make_strategy


class BotState(str, Enum):
    IDLE = "IDLE"
    WAITING_FOR_ROUND = "WAITING_FOR_ROUND"
    BETTING_PHASE = "BETTING_PHASE"
    ROUND_RUNNING = "ROUND_RUNNING"
    READ_RESULT = "READ_RESULT"
    CALCULATE_NEXT_STAKE = "CALCULATE_NEXT_STAKE"
    PLACE_NEXT_BET = "PLACE_NEXT_BET"
    RECONNECTING = "RECONNECTING"
    STOPPED = "STOPPED"


class BotController:
    def __init__(self, settings: BotSettings, adapter: GameAdapter, history: SQLiteHistory | None = None,
                 on_event: Callable[[str | tuple], None] | None = None) -> None:
        self.settings = settings
        self.adapter = adapter
        self.history = history or SQLiteHistory(settings.database_path)
        self.on_event = on_event or (lambda _: None)
        self.state = BotState.IDLE
        self._stop_event = threading.Event()
        self._authorized_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.user_stopped = False
        self.user_paused = False
        self.retry_count = 0
        self.strategy = make_strategy(settings.strategy, settings.multiplier, settings.auto_cashout)
        self.risk = RiskManager(settings.starting_balance if settings.dry_run else 0.0, RiskLimits(settings.max_stake, settings.max_loss_steps,
                                                                      settings.stop_loss, settings.profit_target))
        if not settings.dry_run:
            self.risk.balance = None
        self.current_stake = settings.base_stake
        self.recent_live_multipliers: list[float] = []

    @property
    def running(self) -> bool: return self._thread is not None and self._thread.is_alive()

    @property
    def is_authorized(self) -> bool: return self._authorized_event.is_set()

    def start(self, authorized: bool = True) -> None:
        self.user_stopped = False
        if authorized:
            self.user_paused = False
            self._authorized_event.set()
        else:
            self.user_paused = True
            self._authorized_event.clear()
        if self.running:
            return
        self._stop_event.clear()
        self.retry_count = 0
        self._thread = threading.Thread(target=self.run, name="aviator-bot", daemon=True)
        self._thread.start()

    def update_settings(self, settings: BotSettings) -> None:
        """Update runtime settings dynamically from dashboard inputs without restarting browser."""
        self.settings = settings
        self.strategy = make_strategy(settings.strategy, settings.multiplier, settings.auto_cashout)
        current_bal = self.risk.balance
        self.risk = RiskManager(
            current_bal if current_bal is not None else (settings.starting_balance if settings.dry_run else 0.0),
            RiskLimits(settings.max_stake, settings.max_loss_steps, settings.stop_loss, settings.profit_target)
        )
        if current_bal is not None:
            self.risk.balance = current_bal
        elif not settings.dry_run:
            self.risk.balance = None
        if self.risk.loss_streak == 0:
            self.current_stake = settings.base_stake
        if hasattr(self.adapter, "_auto_cashout_configured"):
            self.adapter._auto_cashout_configured = False

    def authorize(self) -> None:
        """Signal the running thread to begin or resume live staking."""
        self.user_paused = False
        self._authorized_event.set()

    def pause_staking(self) -> None:
        """Pause live staking and return to background result extraction without closing the browser."""
        self.user_paused = True
        self._authorized_event.clear()

    def stop(self, reason: str = "Stopped by user") -> None:
        self.user_stopped = True
        self.risk.emergency_stop(reason)
        self._stop_event.set()
        self._authorized_event.set()

    def close(self) -> None:
        """Release browser and database resources after the worker has stopped."""
        if self.running:
            self.stop("Closed by user")
            self._thread.join(timeout=2.0)
        self.history.close()

    def run(self) -> None:
        if sys.platform == "win32":
            import asyncio
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass

        last_extracted: float | None = None
        self.retry_count = 0

        while not self._stop_event.is_set():
            if self.user_stopped:
                break

            try:
                # 1. Connect if not already connected
                if hasattr(self.adapter, "is_connected") and not self.adapter.is_connected():
                    self._emit(f"Connecting to game adapter...")
                    self.adapter.connect()
                    self._emit("Connected")
                elif not hasattr(self.adapter, "is_connected"):
                    self.adapter.connect()
                    self._emit("Connected")

                # 2. Preparation
                self.state = BotState.IDLE
                self._emit("Preparing game interface...")
                ok = self.adapter.prepare_game(self.settings.base_stake, self.settings.auto_cashout)
                if hasattr(self.adapter, "read_balance"):
                    bal = self.adapter.read_balance()
                    if bal is not None:
                        self.risk.balance = bal

                if hasattr(self.adapter, "read_recent_history_multipliers"):
                    pills = self.adapter.read_recent_history_multipliers(10)
                    if pills:
                        self.recent_live_multipliers = pills

                if ok:
                    self._emit(f"Ready! Auto tab selected, Auto Cash Out set to {self.settings.auto_cashout:.2f}x, Base Stake set to {self.settings.base_stake:.2f} NGN.")
                    self._emit("Click '2. Authorize & Start Staking' when you are ready to begin.")
                    self._emit("Status: Prepared: Ready to Authorize")
                else:
                    self._emit("Notice: Please confirm the in-game Auto Cash Out switch before authorizing.")
                    self._emit("Status: Prepared (check game)")
                self._emit("prepare_done")

                # Successful connection and preparation: reset retry count
                self.retry_count = 0

                # 3. Main Observation / Betting Loop
                while not self._stop_event.is_set():
                    if self.user_stopped:
                        break

                    # --- Non-Staking Idle / Observation Mode ---
                    if not self._authorized_event.is_set():
                        self.state = BotState.IDLE
                        self._emit("Status: Staking Paused (Extracting Results)")
                        while not self._authorized_event.is_set() and not self._stop_event.is_set():
                            if self.user_stopped:
                                break
                            if hasattr(self.adapter, "read_recent_history_multipliers"):
                                pills = self.adapter.read_recent_history_multipliers(10)
                                if pills:
                                    self.recent_live_multipliers = pills
                                    m = pills[0]
                                    if m != last_extracted:
                                        last_extracted = m
                                        self.history.record_observation("FINISHED", m, None, site=self.settings.site)
                                        self.history.append_dataset_file(self.settings.site, m)
                                        self._emit(f"extracted_result: {m:.2f}")
                                        self._emit(f"[Live Extractor] Round result saved: {m:.2f}x")
                            elif hasattr(self.adapter, "read_latest_history_multiplier"):
                                m = self.adapter.read_latest_history_multiplier()
                                if m is not None and m != last_extracted:
                                    last_extracted = m
                                    self.history.record_observation("FINISHED", m, None, site=self.settings.site)
                                    self.history.append_dataset_file(self.settings.site, m)
                                    self._emit(f"extracted_result: {m:.2f}")
                                    self._emit(f"[Live Extractor] Round result saved: {m:.2f}x")
                            if hasattr(self.adapter, "read_balance"):
                                bal = self.adapter.read_balance()
                                if bal is not None:
                                    self.risk.balance = bal
                            if hasattr(self.adapter, "idle_activity"):
                                self.adapter.idle_activity()
                            self._authorized_event.wait(timeout=0.5)

                        if self._stop_event.is_set() or self.user_stopped:
                            break
                        self._emit("Status: Live auto-staking running")
                        self._emit(f"Live staking active | Stake: {self.current_stake:.2f} NGN | Auto Cashout: {self.settings.auto_cashout:.2f}x | Loss Multiplier: {self.settings.multiplier}x")

                    # --- Live Staking Cycle ---
                    self.state = BotState.WAITING_FOR_ROUND
                    if not self.adapter.wait_for_betting_window(lambda: self._stop_event.is_set() or not self._authorized_event.is_set()):
                        continue
                    if not self._authorized_event.is_set() or self._stop_event.is_set() or self.user_stopped:
                        continue

                    self.state = BotState.BETTING_PHASE
                    self.state = BotState.CALCULATE_NEXT_STAKE
                    decision = self.risk.approve_stake(self.current_stake)
                    if decision is RiskDecision.STOP:
                        self._emit(f"Risk stop: {self.risk.stopped_reason}")
                        self._stop_event.set()
                        break

                    self.state = BotState.PLACE_NEXT_BET
                    self.adapter.place_bet(self.current_stake, self.settings.auto_cashout)
                    self._emit(f"Bet placed: {self.current_stake:.2f} NGN")
                    self.state = BotState.ROUND_RUNNING

                    result = self.adapter.wait_for_result(self._stop_event.is_set)
                    if result is None:
                        break

                    self.state = BotState.READ_RESULT
                    won = result >= self.settings.auto_cashout
                    if won:
                        self.strategy.on_win()
                    profit = self.risk.record_result(self.current_stake, self.settings.auto_cashout if won else result, won)
                    self.history.record(RoundRecord(self.current_stake, "Win" if won else "Loss", result, profit, self.risk.balance or 0.0, site=self.settings.site))

                    # Also record observation and append to LLM dataset
                    self.history.record_observation("FINISHED", result, None, site=self.settings.site)
                    self.history.append_dataset_file(self.settings.site, result)
                    last_extracted = result
                    self._emit(f"extracted_result: {result:.2f}")
                    self._emit(f"Result {result:.2f}x | {'+' if profit >= 0 else ''}{profit:.2f} NGN")

                    if self.risk.stopped_reason:
                        self._emit(f"Risk stop: {self.risk.stopped_reason}")
                        self._stop_event.set()
                        break

                    self.current_stake = self.strategy.next_stake(self.settings.base_stake, self.current_stake, self.risk.loss_streak)

            except Exception as exc:
                # If user manually stopped or paused, or auto retry is disabled, DO NOT RETRY
                if self.user_stopped or self.user_paused or not self.settings.network_auto_retry:
                    import traceback
                    tb = traceback.format_exc()
                    self.risk.emergency_stop(f"Error: {exc}")
                    self._emit(f"Error: {exc}")
                    self._emit(("log", f"Traceback:\n{tb}"))
                    self._emit(("status", f"Error: {exc}"))
                    break

                self.retry_count += 1
                if self.retry_count > self.settings.network_max_retries:
                    self._emit(f"[Network] Max retries ({self.settings.network_max_retries}) exceeded. Permanently stopping bot.")
                    self._emit(("status", f"Network failure: exceeded {self.settings.network_max_retries} retries"))
                    self.risk.emergency_stop(f"Network max retries exceeded: {exc}")
                    break

                self.state = BotState.RECONNECTING
                self._emit(("status", f"Reconnecting ({self.retry_count}/{self.settings.network_max_retries}) in {self.settings.network_retry_delay}s..."))
                self._emit(f"[Network] Connection issue: {exc}. Retrying in {self.settings.network_retry_delay}s (Attempt {self.retry_count}/{self.settings.network_max_retries})...")

                # Interruptible wait for retry delay (checking stop_event, user_stopped & user_paused every 0.5s)
                slept = 0.0
                cancelled = False
                while slept < self.settings.network_retry_delay:
                    if self._stop_event.is_set() or self.user_stopped or self.user_paused:
                        self._emit("[Network] Auto-retry cancelled due to manual stop or pause.")
                        cancelled = True
                        break
                    time.sleep(0.5)
                    slept += 0.5

                if cancelled:
                    if self.user_paused and not self.user_stopped:
                        self.state = BotState.IDLE
                        self._emit("Status: Staking Paused by user")
                    break

                # Attempt reconnect via adapter
                self._emit(f"[Network] Reconnecting adapter now (Attempt {self.retry_count}/{self.settings.network_max_retries})...")
                try:
                    if hasattr(self.adapter, "reconnect"):
                        self.adapter.reconnect()
                    else:
                        self.adapter.connect()
                except Exception as rec_err:
                    self._emit(f"[Network] Reconnect attempt {self.retry_count} failed: {rec_err}")
                    # Outer loop will continue to next retry
                    continue

        # Final cleanup on exit
        self.state = BotState.STOPPED
        if self._stop_event.is_set() or self.user_stopped:
            try:
                self.adapter.close()
            except Exception:
                pass
        self._emit("Bot stopped")

    def _emit(self, message: str | tuple) -> None:
        self.on_event(message)



