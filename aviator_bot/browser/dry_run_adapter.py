from __future__ import annotations

import time
from typing import Callable


class DryRunAdapter:
    """Deterministic adapter used for development and simulation without touching a website."""

    def __init__(self, results: list[float] | None = None, delay: float = 0.05) -> None:
        self.results = results or [1.2, 2.1, 1.1, 3.0, 1.8]
        self.delay = delay
        self._index = 0
        self.last_bet: tuple[float, float] | None = None

    def connect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    def reconnect(self) -> bool:
        return True

    def close(self) -> None:
        pass

    def prepare_game(self, base_stake: float, auto_cashout: float) -> bool:
        return True

    def idle_activity(self) -> None:
        pass

    def read_latest_history_multiplier(self) -> float | None:
        return self.results[max(0, self._index - 1) % len(self.results)]

    def read_recent_history_multipliers(self, count: int = 10) -> list[float]:
        return self.results[:count]

    def read_balance(self) -> float | None:
        return 100000.0

    def wait_for_betting_window(self, stop_requested: Callable[[], bool]) -> bool:
        time.sleep(self.delay)
        return not stop_requested()

    def place_bet(self, stake: float, auto_cashout: float) -> None:
        self.last_bet = (stake, auto_cashout)

    def wait_for_result(self, stop_requested: Callable[[], bool]) -> float | None:
        time.sleep(self.delay)
        if stop_requested():
            return None
        result = self.results[self._index % len(self.results)]
        self._index += 1
        return result
