from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskDecision(str, Enum):
    ALLOW = "allow"
    STOP = "stop"


@dataclass(frozen=True)
class RiskLimits:
    max_stake: float = 5000.0
    max_loss_steps: int = 5
    stop_loss: float = 10000.0
    profit_target: float = 5000.0


@dataclass
class RiskManager:
    starting_balance: float
    limits: RiskLimits
    balance: float | None = None
    profit_loss: float = 0.0
    loss_streak: int = 0
    stopped_reason: str | None = None

    def __post_init__(self) -> None:
        if self.balance is None:
            self.balance = self.starting_balance

    def approve_stake(self, stake: float) -> RiskDecision:
        if self.stopped_reason:
            return RiskDecision.STOP
        if stake <= 0 or stake > self.limits.max_stake:
            self.stopped_reason = f"Stake {stake:.2f} exceeds configured limits"
            return RiskDecision.STOP
        if self.limits.max_loss_steps and self.loss_streak >= self.limits.max_loss_steps:
            self.stopped_reason = "Maximum losing streak reached"
            return RiskDecision.STOP
        return RiskDecision.ALLOW

    def record_result(self, stake: float, multiplier: float, win: bool | None = None) -> float:
        if multiplier < 1:
            raise ValueError("multiplier must be at least 1")
        # `win` is supplied by the controller when an auto-cashout target is
        # configured. A crash below the target is a full stake loss even when
        # the displayed crash multiplier is greater than 1.0x.
        profit = stake * (multiplier - 1) if (win if win is not None else multiplier > 1) else -stake
        self.profit_loss += profit
        self.balance = (self.balance or 0.0) + profit
        self.loss_streak = 0 if profit > 0 else self.loss_streak + 1
        if self.profit_loss <= -abs(self.limits.stop_loss) and self.limits.stop_loss:
            self.stopped_reason = "Stop-loss reached"
        elif self.profit_loss >= self.limits.profit_target and self.limits.profit_target:
            self.stopped_reason = "Profit target reached"
        return profit

    def emergency_stop(self, reason: str = "Emergency stop") -> None:
        self.stopped_reason = reason
