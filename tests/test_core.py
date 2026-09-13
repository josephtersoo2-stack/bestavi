import tempfile
import time
import unittest
from pathlib import Path

from aviator_bot.database.history import RoundRecord, SQLiteHistory
from aviator_bot.browser.controller import DryRunAdapter
from aviator_bot.bot.controller import BotController
from aviator_bot.config.settings import BotSettings
from aviator_bot.config.site_profiles import profile
from aviator_bot.browser.observer import GameSnapshot, parse_balance
from aviator_bot.browser.detector import parse_multiplier
from aviator_bot.bot.paper import PaperTradingController
from aviator_bot.risk.manager import RiskDecision, RiskLimits, RiskManager
from aviator_bot.strategy.engine import (
    ExactRecoveryStrategy,
    FibonacciStrategy,
    MartingaleStrategy,
    RecoveryStrategy,
    calculate_loss_multiplier,
    make_strategy,
)


class StrategyTests(unittest.TestCase):
    def test_martingale_resets_after_win_streak_zero(self):
        strategy = MartingaleStrategy(2)
        self.assertEqual(strategy.next_stake(50, 50, 0), 50)
        self.assertEqual(strategy.next_stake(50, 50, 1), 100)
        self.assertEqual(MartingaleStrategy(3).next_stake(50, 50, 1), 150)
        self.assertEqual(MartingaleStrategy(3).next_stake(50, 150, 2), 450)
        self.assertEqual(MartingaleStrategy(3).next_stake(50, 450, 3), 1350)

    def test_calculate_loss_multiplier(self):
        self.assertEqual(calculate_loss_multiplier(1.5), 3.0)
        self.assertEqual(calculate_loss_multiplier(2.0), 2.0)
        self.assertEqual(calculate_loss_multiplier(3.0), 1.5)

    def test_exact_recovery_progression(self):
        strategy = ExactRecoveryStrategy(target_odds=1.5)
        # Base stake
        self.assertEqual(strategy.next_stake(50, 50, 0), 50)
        # Loss 1: accumulated loss = 50 -> (50 + 50) / 0.5 = 200
        self.assertEqual(strategy.next_stake(50, 50, 1), 200)
        # Loss 2: accumulated loss = 50 + 200 = 250 -> (250 + 50) / 0.5 = 600
        self.assertEqual(strategy.next_stake(50, 200, 2), 600)
        strategy.on_win()
        self.assertEqual(strategy.next_stake(50, 600, 0), 50)

    def test_recovery_progression(self):
        strategy = RecoveryStrategy()
        self.assertEqual(strategy.next_stake(50, 50, 1), 75)
        self.assertEqual(strategy.next_stake(50, 75, 2), 112.5)

    def test_fibonacci_progression(self):
        strategy = FibonacciStrategy()
        self.assertEqual(strategy.next_stake(50, 50, 1), 50)
        self.assertEqual(strategy.next_stake(50, 50, 2), 100)
        self.assertEqual(strategy.next_stake(50, 50, 3), 150)


class RiskTests(unittest.TestCase):
    def test_stake_and_profit_limits(self):
        manager = RiskManager(1000, RiskLimits(max_stake=100, max_loss_steps=2, stop_loss=100, profit_target=100))
        self.assertEqual(manager.approve_stake(101), RiskDecision.STOP)
        manager = RiskManager(1000, RiskLimits(max_stake=100, max_loss_steps=2, stop_loss=100, profit_target=100))
        self.assertEqual(manager.record_result(50, 2, True), 50)
        self.assertEqual(manager.balance, 1050)
        self.assertEqual(manager.loss_streak, 0)
        self.assertEqual(manager.record_result(50, 1.2, False), -50)
        self.assertEqual(manager.loss_streak, 1)


class HistoryTests(unittest.TestCase):
    def test_rounds_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.sqlite3"
            with SQLiteHistory(path) as history:
                history.record(RoundRecord(50, "Win", 2.0, 50, 1050))
                self.assertEqual(history.recent(1)[0]["result"], "Win")
                history.record_observation("BETTING", 1.25, 4842.5)
                self.assertEqual(history.recent_observations(1)[0]["phase"], "BETTING")
                history.record_observation("BETTING", 2.5, 1000, site="bcgame")
                self.assertEqual(history.recent_observations(10, site="bcgame")[0]["site"], "bcgame")
                self.assertIn('"site": "bcgame"', history.export_observations("json", site="bcgame"))
                self.assertIn("| Platform |", history.export_observations("md", site="bcgame"))
                self.assertIn("bcgame", history.export_observations("txt", site="bcgame"))


class ControllerTests(unittest.TestCase):
    def test_controller_progresses_and_stops_on_loss_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = BotSettings(max_loss_steps=2, auto_cashout=2.0, database_path=str(Path(tmp) / "history.sqlite3"))
            events = []
            controller = BotController(settings, DryRunAdapter(results=[1.2], delay=0.001), on_event=events.append)
            controller.start()
            deadline = time.time() + 2
            while controller.running and time.time() < deadline:
                time.sleep(0.005)
            self.assertFalse(controller.running)
            self.assertEqual(controller.risk.loss_streak, 2)
            self.assertIn("Maximum losing streak reached", " ".join(events))
            self.assertEqual(len(controller.history.recent(10)), 2)
            controller.history.close()


class ObserverTests(unittest.TestCase):
    def test_bcgame_profile_targets_main_dom(self):
        selectors = profile("bcgame")
        self.assertEqual(selectors.url, "https://bc.game/game/crash")
        self.assertEqual(selectors.iframe_selector, "")
        self.assertEqual(selectors.stake_input_selector, "#NumberField-cl-7 input")
        self.assertIn("crash-banner", selectors.history_multiplier_selector)
        self.assertEqual((selectors.activity_scroll_min_seconds, selectors.activity_scroll_max_seconds), (30.0, 90.0))

    def test_parse_balance(self):
        self.assertEqual(parse_balance("Balance: 4,842.50 NGN"), 4842.50)
        self.assertIsNone(parse_balance("Balance: --"))

    def test_parse_multiplier_supports_bcgame_sign(self):
        self.assertEqual(parse_multiplier("7.80×"), 7.8)

    def test_paper_trading_never_places_bets_and_records_results(self):
        class FakeObserver:
            def connect(self): pass
            def close(self): pass
            def observe(self, stop_requested, on_snapshot, **kwargs):
                snapshots = [
                    GameSnapshot(1000, "BETTING", None, 1.1, False, "1"),
                    GameSnapshot(1000, "RUNNING", 1.5, 1.1, False, "2"),
                    GameSnapshot(950, "BETWEEN_ROUNDS", None, 1.1, False, "2b"),
                    GameSnapshot(950, "BETWEEN_ROUNDS", None, 1.2, False, "3"),
                    GameSnapshot(950, "BETTING", None, 1.2, False, "3b"),
                    GameSnapshot(950, "RUNNING", 2.2, 1.2, False, "4"),
                    GameSnapshot(1050, "BETWEEN_ROUNDS", None, 2.2, False, "5"),
                ]
                for snapshot in snapshots:
                    on_snapshot(snapshot)

        with tempfile.TemporaryDirectory() as tmp:
            settings = BotSettings(auto_cashout=2.0, database_path=str(Path(tmp) / "history.sqlite3"))
            history = SQLiteHistory(settings.database_path)
            paper = PaperTradingController(settings, FakeObserver(), history=history)
            paper.start()
            deadline = time.time() + 2
            while paper.running and time.time() < deadline:
                time.sleep(0.005)
            self.assertEqual(len(history.recent(10)), 2)
            self.assertEqual(history.recent(10)[0]["result"], "Win")
            self.assertEqual(paper.current_stake, settings.base_stake)
            history.close()


class ActionTests(unittest.TestCase):
    def test_setup_auto_cashout_tab_success(self):
        from aviator_bot.browser.actions import setup_auto_cashout_tab, place_bet_on_page

        class MockElement:
            def __init__(self, tag="div", classes="", checked=False, val=""):
                self._tag = tag
                self._classes = classes
                self._checked = checked
                self._val = val
                self.clicked = 0

            def is_visible(self): return True
            def get_attribute(self, attr):
                if attr == "class": return self._classes
                return None
            def evaluate(self, expr): return self._tag
            def is_checked(self): return self._checked
            def click(self):
                self.clicked += 1
                self._classes = (self._classes + " active").strip()
            def input_value(self): return self._val
            def fill(self, text): self._val = text
            def press_sequentially(self, text, delay=0): self._val = text

        class MockCard:
            def __init__(self):
                self.bet_tab = MockElement("div", classes="tab-item active")
                self.auto_tab = MockElement("div", classes="tab-item")
                self.bet_switch = MockElement("div", classes="common-switch off")
                self.cashout_switch = MockElement("div", classes="common-switch off")
                self.stake_inp = MockElement("input", val="")
                self.cashout_inp = MockElement("input", val="")
                self.bet_btn = MockElement("div", classes="bet-button")

            def locator(self, selector):
                card_self = self
                class MockLocator:
                    def __init__(self, elems):
                        self._elems = elems if isinstance(elems, list) else [elems]
                    @property
                    def first(self):
                        return self._elems[0] if self._elems else MockElement(val="")
                    def nth(self, idx):
                        return self._elems[idx] if idx < len(self._elems) else MockElement(val="")
                    def count(self):
                        return len(self._elems)
                    def is_visible(self):
                        return bool(self._elems and self._elems[0].is_visible())
                    def get_attribute(self, attr):
                        return self.first.get_attribute(attr)
                    def evaluate(self, expr):
                        return self.first.evaluate(expr)
                    def is_checked(self):
                        return self.first.is_checked()
                    def click(self):
                        self.first.click()
                    def input_value(self):
                        return self.first.input_value()
                    def fill(self, text):
                        self.first.fill(text)
                    def press_sequentially(self, text, delay=0):
                        self.first.press_sequentially(text, delay)
                    def locator(self, inner_sel):
                        return card_self.locator(inner_sel)

                if "tab-item" in selector:
                    return MockLocator([self.bet_tab, self.auto_tab])
                if "Auto" in selector and "Cash" not in selector and "Bet" not in selector:
                    return MockLocator(self.auto_tab)
                if "auto-area-right" in selector or "cashout" in selector or "cash-out" in selector:
                    if "input" in selector:
                        return MockLocator(self.cashout_inp)
                    return MockLocator(self.cashout_switch)
                if "auto-area-left" in selector:
                    return MockLocator(self.bet_switch)
                if "switch" in selector:
                    return MockLocator(self.cashout_switch)
                if "stake" in selector or "amount" in selector:
                    return MockLocator(self.stake_inp)
                if "odds" in selector or "input" in selector:
                    return MockLocator(self.cashout_inp)
                return MockLocator(self.bet_btn)

        card = MockCard()
        success = setup_auto_cashout_tab(card, ".common-tabs-container .tab-item", ".auto-area-right .common-switch", ".auto-area-right input.cash-out-odds-input", 1.50)
        self.assertTrue(success)
        self.assertEqual(card.auto_tab.clicked, 1)
        self.assertEqual(card.cashout_switch.clicked, 1)
        self.assertEqual(card.bet_switch.clicked, 0)
        self.assertEqual(card.cashout_inp._val, "1.50")

        place_bet_on_page(card, ".bet-amount-input", ".bet-button", 50.0, human_delay=False)
        self.assertEqual(card.stake_inp._val, "50")
        self.assertEqual(card.bet_btn.clicked, 1)


if __name__ == "__main__": unittest.main()




