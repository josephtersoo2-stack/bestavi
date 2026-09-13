from __future__ import annotations

import logging
from typing import Any
from .base_agent import BaseAgent, AgentEvaluation
from ..config import AIConfig

logger = logging.getLogger("aviator_bot.ai.agents.risk_guardian")


class RiskGuardianAgent(BaseAgent):
    """Capital Preservation Officer: Safeguards bankroll, enforces drawdown limits & stop losses."""

    @property
    def agent_id(self) -> str:
        return "risk_guardian"

    @property
    def name(self) -> str:
        return "Capital Risk Guardian"

    @property
    def role(self) -> str:
        return "Capital Preservation Officer"

    def evaluate(
        self,
        telemetry: dict[str, Any],
        config: AIConfig | None = None,
    ) -> AgentEvaluation:
        bankroll = telemetry.get("bankroll_data", {})
        balance = bankroll.get("balance")
        base_stake = float(bankroll.get("base_stake") or 50.0)
        current_stake = float(bankroll.get("current_stake") or base_stake)
        loss_streak = int(bankroll.get("loss_streak") or 0)
        max_loss_steps = int(telemetry.get("max_loss_steps") or 5)
        max_stake = float(telemetry.get("max_stake") or 5000.0)
        stop_loss = float(telemetry.get("stop_loss") or 10000.0)
        profit_target = float(telemetry.get("profit_target") or 5000.0)
        session_profit = float(telemetry.get("session_profit") or 0.0)

        # Proximity calculations
        remaining_loss_steps = max(0, max_loss_steps - loss_streak)
        stake_to_max_ratio = (current_stake / max_stake) if max_stake > 0 else 0.0
        stop_loss_proximity = (abs(session_profit) / stop_loss) if (session_profit < 0 and stop_loss > 0) else 0.0

        metrics = {
            "balance": balance,
            "current_stake": current_stake,
            "max_stake": max_stake,
            "loss_streak": loss_streak,
            "max_loss_steps": max_loss_steps,
            "remaining_loss_steps": remaining_loss_steps,
            "session_profit": session_profit,
            "stop_loss_proximity_pct": round(stop_loss_proximity * 100, 1),
        }

        recommendations = []
        if session_profit <= -stop_loss:
            directive = "PAUSE_STAKING"
            sentiment = "CRITICAL"
            confidence = 98.0
            reasoning = f"Emergency stop: Session drawdown reached stop-loss limit of NGN {stop_loss:.2f}. Staking must cease."
            recommendations.append("Trigger emergency bot stop")
            recommendations.append("Protect remaining bankroll capital")
        elif session_profit >= profit_target:
            directive = "PAUSE_STAKING"
            sentiment = "BULLISH"
            confidence = 95.0
            reasoning = f"Profit target achieved: Session profit reached NGN {session_profit:.2f} (Target: NGN {profit_target:.2f}). Lock in profits."
            recommendations.append("Pause staking to secure session winnings")
            recommendations.append("Take profit and reset session counters")
        elif remaining_loss_steps <= 1 and loss_streak > 0:
            directive = "PAUSE_STAKING"
            sentiment = "CRITICAL"
            confidence = 92.0
            reasoning = (
                f"Loss streak alert: Active loss streak is at {loss_streak}/{max_loss_steps} steps. "
                f"Next wager would risk breaching max loss limit. Autonomous defense requires pausing."
            )
            recommendations.append("Pause staking before escalating to final step")
            recommendations.append("Reset staking progression back to base stake")
        elif stake_to_max_ratio >= 0.8:
            directive = "CAUTION"
            sentiment = "BEARISH"
            confidence = 80.0
            reasoning = f"High stake exposure: Current stake (NGN {current_stake:.2f}) is {stake_to_max_ratio * 100:.0f}% of max allowed stake (NGN {max_stake:.2f})."
            recommendations.append("Enforce stake ceiling or step down progression")
        elif loss_streak == 0 and current_stake <= base_stake:
            directive = "BET"
            sentiment = "BULLISH"
            confidence = 85.0
            reasoning = f"Bankroll is completely secure. Zero active loss streak, stake at base NGN {base_stake:.2f}."
            recommendations.append("Proceed with nominal risk allocation")
        else:
            directive = "BET"
            sentiment = "NEUTRAL"
            confidence = 70.0
            reasoning = f"Risk exposure is within nominal tolerances. {remaining_loss_steps} steps remaining until limit."
            recommendations.append("Monitor next round outcome closely")

        return AgentEvaluation(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            directive=directive,
            confidence=confidence,
            sentiment=sentiment,
            reasoning=reasoning,
            metrics=metrics,
            recommendations=recommendations,
        )
