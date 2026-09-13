from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Any
from .enums import GameCategory
from .selectors import BaseGameSelectors


class BaseGameAddon(ABC):
    """Abstract interface for any game type hosted within a platform."""

    def __init__(self, selectors: BaseGameSelectors | None = None) -> None:
        self.selectors = selectors or self.default_selectors()

    @property
    @abstractmethod
    def game_id(self) -> str:
        """Unique identifier for this game within the platform, e.g. 'aviator', 'crash', 'limbo'."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human readable title, e.g. 'Aviator (Spribe)', 'BC Crash'."""
        pass

    @property
    def aliases(self) -> tuple[str, ...]:
        """Optional backwards-compatible alias identifiers for this game."""
        return ()

    @property
    @abstractmethod
    def category(self) -> GameCategory:
        """Game category: CRASH, LIMBO, DICE, etc."""
        pass

    @abstractmethod
    def default_selectors(self) -> BaseGameSelectors:
        """Return the default CSS / text selectors for this game."""
        pass

    @abstractmethod
    def prepare_game(self, page_or_root: Any, base_stake: float, auto_cashout: float) -> bool:
        """Configure the in-game auto cash out, auto tab, and base stake amount."""
        pass

    @abstractmethod
    def wait_for_betting_window(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> bool:
        """Block until the game is open for receiving new bets before the round starts."""
        pass

    @abstractmethod
    def place_bet(self, page_or_root: Any, stake: float, auto_cashout: float) -> None:
        """Place the wager before countdown expiration."""
        pass

    @abstractmethod
    def wait_for_result(self, page_or_root: Any, stop_requested: Callable[[], bool]) -> float | None:
        """Monitor live round until completion and return the final crash / multiplier result."""
        pass

    @abstractmethod
    def extract_recent_multipliers(self, page_or_root: Any, count: int = 10) -> list[float]:
        """Scrape recent completed round badges from the game ribbon."""
        pass
