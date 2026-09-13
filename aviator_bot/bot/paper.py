from __future__ import annotations

import threading
from typing import Callable, Protocol

from aviator_bot.browser.observer import GameSnapshot
from aviator_bot.config.settings import BotSettings
from aviator_bot.database.history import RoundRecord, SQLiteHistory
from aviator_bot.risk.manager import RiskDecision, RiskLimits, RiskManager
from aviator_bot.strategy.engine import make_strategy


class Observer(Protocol):
    def connect(self) -> None: ...
    def observe(self, stop_requested: Callable[[], bool], on_snapshot: Callable[[GameSnapshot], None], **kwargs: object) -> None: ...
    def close(self) -> None: ...


class PaperTradingController:
    """Run strategy and risk logic against live observations without placing bets."""

    def __init__(self, settings: BotSettings, observer: Observer, history: SQLiteHistory | None = None,
                 on_event: Callable[[str], None] | None = None,
                 on_snapshot: Callable[[GameSnapshot], None] | None = None) -> None:
        self.settings = settings
        self.observer = observer
        self.history = history or SQLiteHistory(settings.database_path)
        self.on_event = on_event or (lambda _: None)
        self.on_snapshot = on_snapshot or (lambda _: None)
        self.strategy = make_strategy(settings.strategy, settings.multiplier, settings.auto_cashout)
        self.risk = RiskManager(settings.starting_balance, RiskLimits(settings.max_stake, settings.max_loss_steps,
                                                                      settings.stop_loss, settings.profit_target))
        self.current_stake = settings.base_stake
        self.state = "IDLE"
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._planned_stake: float | None = None
        self._saw_running = False
        self._login_reported = False
        self._last_observed_result: float | None = None
        self._planned_result_baseline: float | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.run, name="paper-trading", daemon=True)
        self._thread.start()

    def stop(self, reason: str = "Paper trading stopped") -> None:
        self.risk.emergency_stop(reason)
        self._stop_event.set()

    def close(self) -> None:
        if self.running:
            self.stop()
            self._thread.join(timeout=2.0)
        self.history.close()

    def run(self) -> None:
        try:
            self.observer.connect()
            self._emit("Paper-trading observer connected; no BET clicks will be made")
            self.observer.observe(self._stop_event.is_set, self._on_snapshot)
        except Exception as exc:
            self.risk.emergency_stop(f"Error: {exc}")
            self._emit(f"Paper-trading error: {exc}")
        finally:
            self.state = "STOPPED"
            self.observer.close()
            self._emit("Paper trading stopped")

    def _on_snapshot(self, snapshot: GameSnapshot) -> None:
        if self._stop_event.is_set():
            return
        self.on_snapshot(snapshot)
        self.state = snapshot.phase
        if snapshot.login_required:
            if not self._login_reported:
                self._emit("Login required: log in manually in the observer browser")
                self._login_reported = True
            return
        if self._login_reported:
            self._emit("Login detected; round tracking resumed")
            self._login_reported = False
        if snapshot.phase == "BETTING" and self._planned_stake is None:
            # Capture the history value belonging to the round we are about
            # to enter; settlement must wait for a different value.
            self._last_observed_result = snapshot.last_multiplier
            self._plan_stake()
        elif self._planned_stake is not None and snapshot.phase == "RUNNING":
            self._saw_running = True
        elif (self._planned_stake is not None and self._saw_running
              and snapshot.phase in {"BETWEEN_ROUNDS", "BETTING"}
              and snapshot.last_multiplier is not None
              and snapshot.last_multiplier != self._planned_result_baseline):
            self._last_observed_result = snapshot.last_multiplier
            self._settle(snapshot.last_multiplier, snapshot.balance)
        self._last_observed_result = snapshot.last_multiplier

    def _settle(self, multiplier: float, balance: float | None) -> None:
        stake = self._planned_stake
        if stake is None:
            return
        won = multiplier >= self.settings.auto_cashout
        if won:
            self.strategy.on_win()
        profit = self.risk.record_result(stake, self.settings.auto_cashout if won else multiplier, won)
        self.history.record(RoundRecord(stake, "Win" if won else "Loss", multiplier,
                                        profit, self.risk.balance or balance or 0.0,
                                        site=self.settings.site))
        self._emit(f"Paper result {multiplier:.2f}x | {'Win' if won else 'Loss'} | {'+' if profit >= 0 else ''}{profit:.2f} NGN")
        self._planned_stake = None
        if self.risk.stopped_reason:
            self._emit(f"Risk stop: {self.risk.stopped_reason}")
            self._stop_event.set()
        else:
            self.current_stake = self.strategy.next_stake(self.settings.base_stake, stake, self.risk.loss_streak)
            # The same BETTING snapshot that reveals the completed round is
            # also the next round's betting window, so plan immediately.
            self._plan_stake()

    def _plan_stake(self) -> None:
        if self.risk.approve_stake(self.current_stake) is RiskDecision.STOP:
            self._emit(f"Risk stop: {self.risk.stopped_reason}")
            self._stop_event.set()
            return
        self._planned_stake = self.current_stake
        self._saw_running = False
        self._planned_result_baseline = self._last_observed_result
        self._emit(f"Paper bet planned: {self._planned_stake:.2f} NGN @ {self.settings.auto_cashout:.2f}x")

    def _emit(self, message: str) -> None:
        self.on_event(message)
