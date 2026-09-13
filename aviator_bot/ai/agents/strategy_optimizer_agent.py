from __future__ import annotations

import logging
from typing import Any
from .base_agent import BaseAgent, AgentEvaluation
from ..config import AIConfig

logger = logging.getLogger("aviator_bot.ai.agents.strategy_optimizer")


class StrategyOptimizerAgent(BaseAgent):
    """EV & Cashout Tactician: Calculates mathematical expected value & optimizes staking progression."""

    @property
    def agent_id(self) -> str:
        return "strategy_optimizer"

    @property
    def name(self) -> str:
        return "Strategy & EV Tactician"

    @property
    def role(self) -> str:
        return "Mathematical EV & Cashout Tactician"

    def evaluate(
        self,
        telemetry: dict[str, Any],
        config: AIConfig | None = None,
    ) -> AgentEvaluation:
        odds_records = telemetry.get("odds_records", [])
        current_strategy = str(telemetry.get("strategy") or "martingale").lower()
        current_cashout = float(telemetry.get("auto_cashout") or 1.50)
        base_stake = float(telemetry.get("base_stake") or 50.0)

        multipliers = [float(r.get("multiplier", 1.0)) for r in odds_records if "multiplier" in r]
        total_sample = len(multipliers)

        # Empirical win probability for current cashout
        if total_sample >= 10:
            hits = sum(1 for m in multipliers if m >= current_cashout)
            p_win = hits / total_sample
        else:
            p_win = 0.65  # baseline expectation for 1.50x in crash games

        # Expected Value (EV) per unit wagered: EV = (p_win * (cashout - 1)) - ((1 - p_win) * 1.0)
        ev_per_unit = (p_win * (current_cashout - 1.0)) - ((1.0 - p_win) * 1.0)

        # Simulation of alternative cashout target: 1.35x
        if total_sample >= 10:
            hits_135 = sum(1 for m in multipliers if m >= 1.35)
            p_win_135 = hits_135 / total_sample
        else:
            p_win_135 = 0.72
        ev_135 = (p_win_135 * (1.35 - 1.0)) - ((1.0 - p_win_135) * 1.0)

        metrics = {
            "strategy": current_strategy,
            "target_cashout": current_cashout,
            "empirical_win_prob": round(p_win * 100, 1),
            "ev_per_unit": round(ev_per_unit, 4),
            "alt_135_win_prob": round(p_win_135 * 100, 1),
            "alt_135_ev": round(ev_135, 4),
        }

        recommendations = []
        if ev_per_unit > 0.02:
            directive = "BET"
            sentiment = "BULLISH"
            confidence = 85.0
            reasoning = (
                f"Positive mathematical edge detected! Empirical win rate is {p_win * 100:.1f}% at {current_cashout:.2f}x "
                f"yielding an EV of +{ev_per_unit:.3f} units per round."
            )
            recommendations.append(f"Maintain active {current_strategy.upper()} strategy at {current_cashout:.2f}x")
        elif ev_per_unit < -0.15:
            directive = "CAUTION"
            sentiment = "BEARISH"
            confidence = 78.0
            reasoning = (
                f"Negative expectancy phase: Win probability {p_win * 100:.1f}% at {current_cashout:.2f}x produces severe EV drag ({ev_per_unit:.3f}). "
                f"However, 1.35x target shows {p_win_135 * 100:.1f}% hit frequency."
            )
            recommendations.append("Consider lowering target cashout from 1.50x to 1.35x")
            recommendations.append("Switch from Martingale to D'Alembert to moderate streak variance")
        else:
            directive = "BET"
            sentiment = "NEUTRAL"
            confidence = 70.0
            reasoning = (
                f"Expected value is neutral ({ev_per_unit:+.3f}). Standard variance observed for {current_strategy.upper()} "
                f"at {current_cashout:.2f}x target."
            )
            recommendations.append("Continue current staking plan with standard escalation")

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
