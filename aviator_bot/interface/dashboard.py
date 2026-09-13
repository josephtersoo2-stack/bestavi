from __future__ import annotations

import queue
import re
import threading
from dataclasses import replace
from pathlib import Path

from aviator_bot.bot.controller import BotController
from aviator_bot.bot.paper import PaperTradingController
from aviator_bot.browser.controller import DryRunAdapter, PlaywrightAdapter
from aviator_bot.browser.observer import GameSnapshot, PlaywrightObserver
from aviator_bot.config.settings import BotSettings, load_settings
from aviator_bot.config.site_profiles import SITE_NAMES, profile
from aviator_bot.database.history import SQLiteHistory
from aviator_bot.strategy.engine import calculate_loss_multiplier


def run_dashboard(settings_path: str | Path) -> None:
    try:
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout, QLabel,
                                     QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout,
                                     QWidget, QFileDialog)
    except ImportError as exc:
        raise RuntimeError("PyQt6 is not installed; install requirements.txt") from exc

    settings = load_settings(settings_path)
    events: queue.Queue[object] = queue.Queue()
    controller: BotController | PaperTradingController | None = None
    observer: PlaywrightObserver | None = None
    observer_thread: threading.Thread | None = None
    observer_stop = threading.Event()
    observer_history: SQLiteHistory | None = None
    last_observed_multiplier: float | None = None
    last_observed_phase: str | None = None
    prepared_adapter: PlaywrightAdapter | None = None

    class Window(QMainWindow):

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Aviator Assistant")
            self.resize(620, 480)
            self.status = QLabel("Idle")
            self.observer_status = QLabel("Observer: disconnected")
            self.balance = QLabel("Balance: --")
            self.phase = QLabel("Phase: --")
            self.current_multiplier = QLabel("Current multiplier: --")
            self.latest_multiplier = QLabel("Latest history multiplier: --")
            self.next_stake = QLabel("Next stake: --")
            self.log = QTextEdit(); self.log.setReadOnly(True)
            self.site = QComboBox(); self.site.addItems(list(SITE_NAMES.values()))
            initial_site = settings.site if settings.site in SITE_NAMES else "ilotbet"
            self.site.setCurrentIndex(list(SITE_NAMES).index(initial_site))
            self.url = QLineEdit(settings.browser.url)
            self.base = QLineEdit(str(settings.base_stake))
            self.strategy = QComboBox(); self.strategy.addItems(["martingale", "exact_recovery", "recovery", "fibonacci", "flat"])
            self.strategy.setCurrentText(settings.strategy)
            self.loss_multiplier = QLineEdit(str(settings.multiplier))
            self.cashout = QLineEdit(str(settings.auto_cashout))
            self.max_stake = QLineEdit(str(settings.max_stake))
            self.max_losses = QLineEdit(str(settings.max_loss_steps))
            self.stop_loss = QLineEdit(str(settings.stop_loss))
            self.profit_target = QLineEdit(str(settings.profit_target))
            self.mode = QComboBox(); self.mode.addItems(["Dry-run simulation", "Paper-trade live page", "Manual-assist (click Bet yourself)", "Live auto-stake (Real bets)"])
            if settings.paper_trade:
                self.mode.setCurrentIndex(1)
            elif settings.dry_run:
                self.mode.setCurrentIndex(0)
            else:
                self.mode.setCurrentIndex(3)
            form = QFormLayout()
            form.addRow("Platform", self.site)
            form.addRow("Game URL", self.url)
            form.addRow("Base stake (NGN)", self.base)
            form.addRow("Strategy", self.strategy)
            form.addRow("Loss multiplier", self.loss_multiplier)
            form.addRow("Auto cashout (x)", self.cashout)
            form.addRow("Maximum stake (NGN)", self.max_stake)
            form.addRow("Maximum loss steps", self.max_losses)
            form.addRow("Stop loss (NGN)", self.stop_loss)
            form.addRow("Profit target (NGN)", self.profit_target)
            form.addRow("Execution mode", self.mode)
            self.site.currentIndexChanged.connect(self.site_changed)
            self.cashout.textChanged.connect(self.cashout_changed)
            self.prepare_btn = QPushButton("1. Prepare Game (Set Auto Cashout & Stake)")
            self.start = QPushButton("2. Authorize & Start Staking")
            self.stop_button = QPushButton("Stop Staking")
            self.stop_button.setEnabled(False)
            self.prepare_btn.clicked.connect(self.prepare_game_ui)
            self.start.clicked.connect(self.start_bot)
            self.stop_button.clicked.connect(self.stop_bot)
            action_layout = QVBoxLayout()
            action_layout.addWidget(self.prepare_btn)
            bet_buttons = QHBoxLayout()
            bet_buttons.addWidget(self.start)
            bet_buttons.addWidget(self.stop_button)
            action_layout.addLayout(bet_buttons)
            self.connect_button = QPushButton("Connect observer")
            self.disconnect_button = QPushButton("Disconnect observer"); self.disconnect_button.setEnabled(False)
            self.connect_button.clicked.connect(self.connect_observer); self.disconnect_button.clicked.connect(self.disconnect_observer)
            observer_buttons = QHBoxLayout(); observer_buttons.addWidget(self.connect_button); observer_buttons.addWidget(self.disconnect_button)
            self.copy_stake = QPushButton("Copy next stake")
            self.copy_stake.clicked.connect(self.copy_next_stake)
            assist_buttons = QHBoxLayout(); assist_buttons.addWidget(self.next_stake); assist_buttons.addWidget(self.copy_stake)
            export_buttons = QHBoxLayout()
            for label, fmt, extension in (("Export TXT", "txt", "txt"), ("Export CSV", "csv", "csv"), ("Export JSON", "json", "json"), ("Export Markdown", "md", "md")):
                button = QPushButton(label)
                button.clicked.connect(lambda _checked=False, f=fmt, ext=extension: self.export_history(f, ext))
                export_buttons.addWidget(button)
            root = QVBoxLayout(); root.addLayout(form); root.addLayout(action_layout); root.addLayout(observer_buttons); root.addLayout(assist_buttons); root.addLayout(export_buttons)
            root.addWidget(self.status); root.addWidget(self.observer_status); root.addWidget(self.balance)
            root.addWidget(self.phase); root.addWidget(self.current_multiplier); root.addWidget(self.latest_multiplier); root.addWidget(self.log)
            widget = QWidget(); widget.setLayout(root); self.setCentralWidget(widget)
            self.timer = QTimer(self); self.timer.timeout.connect(self.drain_events); self.timer.start(100)

        def site_changed(self, index: int) -> None:
            nonlocal settings
            name = list(SITE_NAMES)[index]
            current_url = self.url.text().strip()
            # Replace the selector set while preserving a custom URL only when
            # it belongs to the selected platform.
            next_profile = profile(name, settings.browser)
            default_profile = profile(name)
            if not current_url or (name == "bcgame" and "ilotbet.com" in current_url) or (name == "ilotbet" and "bc.game" in current_url):
                self.url.setText(default_profile.url)
            settings = replace(settings, site=name, browser=next_profile)

        def cashout_changed(self, text: str) -> None:
            try:
                odds = float(text.strip())
                if odds > 1.0 and self.strategy.currentText() == "martingale":
                    suggested = calculate_loss_multiplier(odds)
                    self.loss_multiplier.setText(str(suggested))
            except ValueError:
                pass

        def prepare_game_ui(self) -> None:
            nonlocal controller, settings
            try:
                self.mode.setCurrentIndex(3)
                url = self.url.text().strip()
                if not url:
                    raise ValueError("Enter the current game URL first")
                site_name = list(SITE_NAMES)[self.site.currentIndex()]
                settings = BotSettings(**{**settings.__dict__,
                    "base_stake": float(self.base.text()),
                    "strategy": self.strategy.currentText(),
                    "multiplier": float(self.loss_multiplier.text()),
                    "auto_cashout": float(self.cashout.text()),
                    "max_stake": float(self.max_stake.text()),
                    "max_loss_steps": int(self.max_losses.text()),
                    "stop_loss": float(self.stop_loss.text()),
                    "profit_target": float(self.profit_target.text()),
                    "dry_run": False,
                    "paper_trade": False})
                settings = replace(settings, site=site_name, browser=profile(site_name, settings.browser))
                settings.validate()
                if observer_thread and observer_thread.is_alive():
                    raise ValueError("Disconnect the read-only observer before starting live auto-stake")
                browser_settings = replace(settings, dry_run=False, paper_trade=False, browser=replace(settings.browser, url=url))
                self.prepare_btn.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status.setText("Preparing game UI...")
                self.log.append("Connecting to game page to set Auto tab, Auto Cash Out, and stake...")

                if controller and controller.running and isinstance(controller, BotController):
                    controller.update_settings(browser_settings)
                    self.log.append("Settings updated on running session.")
                else:
                    controller = BotController(settings=browser_settings, adapter=PlaywrightAdapter(browser_settings.browser), on_event=events.put)
                    controller.start(authorized=False)
            except (TypeError, ValueError) as exc:
                self.log.append(f"Configuration error: {exc}")
                self.prepare_btn.setEnabled(True)

        def start_bot(self) -> None:
            nonlocal controller, settings
            try:
                site_name = list(SITE_NAMES)[self.site.currentIndex()]
                mode_idx = self.mode.currentIndex()
                settings = BotSettings(**{**settings.__dict__,
                    "base_stake": float(self.base.text()),
                    "strategy": self.strategy.currentText(),
                    "multiplier": float(self.loss_multiplier.text()),
                    "auto_cashout": float(self.cashout.text()),
                    "max_stake": float(self.max_stake.text()),
                    "max_loss_steps": int(self.max_losses.text()),
                    "stop_loss": float(self.stop_loss.text()),
                    "profit_target": float(self.profit_target.text()),
                    "dry_run": mode_idx == 0,
                    "paper_trade": mode_idx in (1, 2)})
                settings = replace(settings, site=site_name, browser=profile(site_name, settings.browser))
                settings.validate()

                if controller and controller.running and isinstance(controller, BotController):
                    controller.update_settings(settings)
                    controller.authorize()
                    self.start.setEnabled(False)
                    self.stop_button.setEnabled(True)
                    self.status.setText("Live auto-staking running")
                    self.log.append(f"Resuming live staking | Base Stake: {settings.base_stake:.2f} NGN | Auto Cashout: {settings.auto_cashout:.2f}x | Loss Multiplier: {settings.multiplier}x")
                    return

                if mode_idx == 0:
                    controller = BotController(settings, DryRunAdapter(), on_event=events.put)
                elif mode_idx == 3:
                    if observer_thread and observer_thread.is_alive():
                        raise ValueError("Disconnect the read-only observer before starting live auto-stake")
                    url = self.url.text().strip()
                    if not url:
                        raise ValueError("Enter the current game URL first")
                    browser_settings = replace(settings, dry_run=False, paper_trade=False, browser=replace(settings.browser, url=url))
                    controller = BotController(settings=browser_settings, adapter=PlaywrightAdapter(browser_settings.browser), on_event=events.put)
                else:
                    if observer_thread and observer_thread.is_alive():
                        raise ValueError("Disconnect the read-only observer before starting another live-page mode")
                    url = self.url.text().strip()
                    if not url:
                        raise ValueError("Enter the current game URL first")
                    browser_settings = replace(settings, browser=replace(settings.browser, url=url))
                    paper_browser = replace(browser_settings.browser,
                                            user_data_dir=f"{browser_settings.browser.user_data_dir}_paper")
                    controller = PaperTradingController(settings=browser_settings,
                                                        observer=PlaywrightObserver(paper_browser),
                                                        on_event=events.put,
                                                        on_snapshot=lambda snapshot: events.put(("snapshot", snapshot)))
                controller.start(authorized=True); self.start.setEnabled(False); self.stop_button.setEnabled(True)
                if mode_idx == 3:
                    self.status.setText("Live auto-staking running")
                elif mode_idx == 2:
                    self.status.setText("Manual-assist running")
                elif mode_idx == 1:
                    self.status.setText("Paper-trading running")
                else:
                    self.status.setText("Simulation running")
            except (TypeError, ValueError) as exc:
                self.log.append(f"Configuration error: {exc}")

        def stop_bot(self) -> None:
            if controller and isinstance(controller, BotController):
                controller.pause_staking()
            elif controller:
                controller.stop()
            self.start.setEnabled(True)
            self.prepare_btn.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status.setText("Staking Paused (Extracting Results)")
            self.log.append("Staking stopped by user. Live result extraction is still active.")



        def copy_next_stake(self) -> None:
            value = self.next_stake.text().replace("Next stake: ", "").replace(" NGN", "").strip()
            if value != "--":
                QApplication.clipboard().setText(value)
                self.log.append(f"Copied next stake: {value} NGN")

        def connect_observer(self) -> None:
            nonlocal observer, observer_thread, observer_history, last_observed_multiplier, last_observed_phase
            if observer_thread and observer_thread.is_alive():
                return
            url = self.url.text().strip()
            if not url:
                self.log.append("Observer error: enter the current game URL first")
                return
            observer = PlaywrightObserver(replace(settings.browser, url=url))
            observer_history = SQLiteHistory(settings.database_path)
            observer_stop.clear(); last_observed_multiplier = None; last_observed_phase = None

            def worker() -> None:
                try:
                    observer.connect()
                    events.put(("observer_connected", None))
                    observer.observe(
                        observer_stop.is_set,
                        lambda snapshot: events.put(("snapshot", snapshot)),
                        on_status=lambda status: events.put(("observer_status", status)),
                    )
                except Exception as exc:
                    events.put(("observer_error", str(exc)))
                finally:
                    observer.close()
                    events.put(("observer_stopped", None))

            observer_thread = threading.Thread(target=worker, name=f"{settings.site}-observer", daemon=True)
            observer_thread.start()
            self.connect_button.setEnabled(False); self.disconnect_button.setEnabled(True); self.observer_status.setText("Observer: connecting")

        def disconnect_observer(self) -> None:
            observer_stop.set()
            self.disconnect_button.setEnabled(False); self.observer_status.setText("Observer: stopping")

        def export_history(self, fmt: str, extension: str) -> None:
            site_name = list(SITE_NAMES)[self.site.currentIndex()]
            default_name = f"{site_name}_crash_history.{extension}"
            path, _ = QFileDialog.getSaveFileName(self, f"Export {site_name} history", default_name,
                                                   f"*.{extension}")
            if not path:
                return
            history = SQLiteHistory(settings.database_path)
            try:
                content = history.export_observations(fmt, site=site_name)
                Path(path).write_text(content, encoding="utf-8")
                self.log.append(f"Exported {site_name} observations to {path}")
            except (OSError, ValueError) as exc:
                self.log.append(f"Export error: {exc}")
            finally:
                history.close()

        def drain_events(self) -> None:
            nonlocal last_observed_multiplier, last_observed_phase, observer_history
            while True:
                try: msg = events.get_nowait()
                except queue.Empty: break
                if isinstance(msg, tuple) and msg[0] == "snapshot":
                    snapshot: GameSnapshot = msg[1]
                    if snapshot.login_required:
                        self.observer_status.setText("Observer: login required")
                    else:
                        self.observer_status.setText("Observer: connected (read-only)")
                    self.balance.setText(f"Balance: {snapshot.balance:.2f} NGN" if snapshot.balance is not None else "Balance: --")
                    self.phase.setText(f"Phase: {snapshot.phase}")
                    self.current_multiplier.setText(f"Current multiplier: {snapshot.current_multiplier:.2f}x" if snapshot.current_multiplier is not None else "Current multiplier: --")
                    self.latest_multiplier.setText(f"Latest history multiplier: {snapshot.last_multiplier:.2f}x" if snapshot.last_multiplier is not None else "Latest history multiplier: --")
                    # A round is finalized when the observer returns to the
                    # BETTING phase. Record that boundary even if two rounds
                    # happen to finish at the same multiplier.
                    is_new_round = (
                        snapshot.phase == "BETTING"
                        and snapshot.last_multiplier is not None
                        and last_observed_phase != "BETTING"
                    )
                    if is_new_round:
                        if observer_history:
                            observer_history.record_observation(snapshot.phase, snapshot.last_multiplier, snapshot.balance,
                                                               snapshot.observed_at, site=settings.site)
                    last_observed_multiplier = snapshot.last_multiplier
                    last_observed_phase = snapshot.phase
                    continue
                if isinstance(msg, tuple) and msg[0] == "log":
                    self.log.append(str(msg[1]))
                    continue
                if isinstance(msg, str):
                    if msg.startswith("Status: "):
                        self.status.setText(msg.replace("Status: ", ""))
                        continue
                    if msg.startswith("extracted_result: "):
                        try:
                            val = float(msg.replace("extracted_result: ", ""))
                            self.latest_multiplier.setText(f"Latest history multiplier: {val:.2f}x")
                        except ValueError:
                            pass
                        self.observer_status.setText("Observer: connected (Live Extractor Active)")
                        if controller and hasattr(controller, "current_stake"):
                            self.next_stake.setText(f"Next stake: {controller.current_stake:.2f} NGN")
                        if controller and hasattr(controller, "risk") and controller.risk.balance:
                            self.balance.setText(f"Balance: {controller.risk.balance:,.2f} NGN")
                        continue
                    if msg == "prepare_done":
                        self.prepare_btn.setEnabled(True)
                        self.observer_status.setText("Observer: connected (Live Extractor Active)")
                        if controller and hasattr(controller, "current_stake"):
                            self.next_stake.setText(f"Next stake: {controller.current_stake:.2f} NGN")
                        if controller and hasattr(controller, "risk") and controller.risk.balance:
                            self.balance.setText(f"Balance: {controller.risk.balance:,.2f} NGN")
                        continue
                    self.log.append(msg)
                    if controller and hasattr(controller, "current_stake"):
                        self.next_stake.setText(f"Next stake: {controller.current_stake:.2f} NGN")
                    if controller and hasattr(controller, "risk") and controller.risk.balance:
                        self.balance.setText(f"Balance: {controller.risk.balance:,.2f} NGN")
                    planned = re.search(r"Paper bet planned:\s*([0-9]+(?:\.[0-9]+)?)", msg)
                    if planned:
                        self.next_stake.setText(f"Next stake: {float(planned.group(1)):.2f} NGN")
                    if msg.startswith("Paper-trading observer connected"):
                        self.observer_status.setText("Observer: connected (paper, read-only)")
                    elif msg == "Paper trading stopped":
                        self.observer_status.setText("Observer: disconnected")
                    if msg == "Bot stopped":
                        self.start.setEnabled(True)
                        self.stop_button.setEnabled(False)
                        self.status.setText("Stopped")

        def closeEvent(self, event) -> None:  # noqa: N802 - Qt callback name
            if controller:
                controller.close()
            observer_stop.set()
            if observer_thread and observer_thread.is_alive():
                observer_thread.join(timeout=2.0)
            if observer_history:
                observer_history.close()
            event.accept()

    app = QApplication.instance() or QApplication([])
    window = Window(); window.show(); app.exec()
