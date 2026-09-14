from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol


class Strategy(Protocol):
    name: str
    def next_stake(self, base_stake: float, current_stake: float, loss_streak: int) -> float: ...
    def on_win(self) -> None: ...
    def reset(self) -> None: ...


@dataclass
class FlatStrategy:
    name: str = "flat"
    def next_stake(self, base_stake: float, current_stake: float, loss_streak: int) -> float:
        return base_stake
    def on_win(self) -> None: pass
    def reset(self) -> None: pass


@dataclass
class MartingaleStrategy:
    multiplier: float = 2.0
    name: str = "martingale"
    ceiling_rule: bool = False

    def next_stake(self, base_stake: float, current_stake: float, loss_streak: int) -> float:
        if loss_streak == 0:
            return float(math.ceil(base_stake)) if self.ceiling_rule else base_stake
        raw = current_stake * self.multiplier
        return float(math.ceil(raw)) if self.ceiling_rule else round(raw, 2)

    def on_win(self) -> None: pass
    def reset(self) -> None: pass


@dataclass
class RecoveryStrategy:
    multiplier: float = 1.5
    name: str = "recovery"
    ceiling_rule: bool = False

    def next_stake(self, base_stake: float, current_stake: float, loss_streak: int) -> float:
        if loss_streak == 0:
            return float(math.ceil(base_stake)) if self.ceiling_rule else base_stake
        raw = current_stake * self.multiplier
        return float(math.ceil(raw)) if self.ceiling_rule else round(raw, 2)

    def on_win(self) -> None: pass
    def reset(self) -> None: pass


@dataclass
class ExactRecoveryStrategy:
    """Calculates the exact stake to recover all cumulative losses plus target profit."""
    target_odds: float = 1.5
    name: str = "exact_recovery"
    ceiling_rule: bool = False
    target_profit: float | None = None
    _accumulated_loss: float = field(default=0.0, init=False)

    def next_stake(self, base_stake: float, current_stake: float, loss_streak: int) -> float:
        if loss_streak == 0:
            self._accumulated_loss = 0.0
            return float(math.ceil(base_stake)) if self.ceiling_rule else base_stake
        if self.target_odds <= 1.0:
            return base_stake
        # If we have entered a loss streak, track accumulated loss
        if loss_streak == 1:
            self._accumulated_loss = base_stake
        else:
            self._accumulated_loss += current_stake
        net_odds = self.target_odds - 1.0
        # When ceiling_rule is active, target profit is initial round profit (base_stake * net_odds)
        if self.target_profit is not None:
            profit = self.target_profit
        elif self.ceiling_rule:
            profit = base_stake * net_odds
        else:
            profit = base_stake

        # Required stake to cover accumulated losses and gain target profit:
        next_val = (self._accumulated_loss + profit) / net_odds
        if self.ceiling_rule:
            return float(math.ceil(next_val))
        return round(next_val, 2)

    def on_win(self) -> None:
        self._accumulated_loss = 0.0

    def reset(self) -> None:
        self._accumulated_loss = 0.0


@dataclass
class FibonacciStrategy:
    name: str = "fibonacci"
    _sequence: list[int] = field(default_factory=lambda: [1, 1])
    def next_stake(self, base_stake: float, current_stake: float, loss_streak: int) -> float:
        if loss_streak == 0:
            return base_stake
        while len(self._sequence) <= loss_streak:
            self._sequence.append(self._sequence[-1] + self._sequence[-2])
        return base_stake * self._sequence[loss_streak]
    def on_win(self) -> None: pass
    def reset(self) -> None:
        self._sequence = [1, 1]


def calculate_loss_multiplier(target_odds: float) -> float:
    """Calculate the ideal Martingale loss multiplier for given target cashout odds."""
    if target_odds <= 1.0:
        return 2.0
    return round(target_odds / (target_odds - 1.0), 4)


def make_strategy(name: str, multiplier: float = 2.0, target_odds: float = 1.5, ceiling_rule: bool = False) -> Strategy:
    normalized = name.strip().lower()
    if normalized == "martingale": return MartingaleStrategy(multiplier, ceiling_rule=ceiling_rule)
    if normalized in {"recovery", "1.5x", "one_point_five"}: return RecoveryStrategy(ceiling_rule=ceiling_rule)
    if normalized in {"exact_recovery", "exact", "odds_recovery"}: return ExactRecoveryStrategy(target_odds, ceiling_rule=ceiling_rule)
    if normalized == "fibonacci": return FibonacciStrategy()
    if normalized in {"flat", "fixed"}: return FlatStrategy()
    raise ValueError(f"Unknown strategy: {name}")
