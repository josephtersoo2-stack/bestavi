from __future__ import annotations

import logging
from typing import Any
from .base_agent import BaseAgent, AgentEvaluation
from ..config import AIConfig
from ..context.odds_summary_builder import build_odds_summary

logger = logging.getLogger("aviator_bot.ai.agents.analyst")


class AnalystAgent(BaseAgent):
    """Pattern Detective: Analyzes multiplier distribution, crash streaks, and cluster density."""

    @property
    def agent_id(self) -> str:
        return "analyst"

    @property
    def name(self) -> str:
        return "Market Pattern Analyst"

    @property
    def role(self) -> str:
        return "Pattern & Streak Detective"

    def evaluate(
        self,
        telemetry: dict[str, Any],
        config: AIConfig | None = None,
    ) -> AgentEvaluation:
        odds_records = telemetry.get("odds_records", [])
        target_odds = float(telemetry.get("auto_cashout") or 1.50)
        summary = build_odds_summary(odds_records, target_odds=target_odds)

        total_rounds = summary.get("total_rounds", 0)
        current_loss_streak = summary.get("current_loss_streak", 0)
        safezone_win_rate = summary.get("safezone_win_rate", 50.0)
        recent_10 = summary.get("recent_multipliers", [])[:10]
        recent_sub_target = sum(1 for m in recent_10 if m < target_odds)

        metrics = {
            "sample_rounds": total_rounds,
            "target_odds": target_odds,
            "safezone_win_rate": safezone_win_rate,
            "current_loss_streak": current_loss_streak,
            "recent_sub_target_count": recent_sub_target,
            "recent_sample_len": len(recent_10),
        }

        recommendations = []
        if current_loss_streak >= 3:
            directive = "PAUSE_STAKING"
            sentiment = "CRITICAL"
            confidence = 88.0
            reasoning = (
                f"Severe cold cluster in progress: {current_loss_streak} consecutive rounds below target {target_odds:.2f}x. "
                f"High probability of extended cluster drawdown. Recommend waiting for a recovery stabilizer."
            )
            recommendations.append("Halt new wagers until a multiplier >= 2.00x resets streak")
            recommendations.append("Observe round outcomes without staking")
        elif recent_sub_target >= 6:
            directive = "CAUTION"
            sentiment = "BEARISH"
            confidence = 74.0
            reasoning = (
                f"Elevated crash frequency: {recent_sub_target} of the last {len(recent_10)} rounds crashed below target {target_odds:.2f}x. "
                f"Current SafeZone rate has compressed to {safezone_win_rate:.1f}%."
            )
            recommendations.append("Lower base stake by 50% or tighten cashout target to 1.35x")
        elif safezone_win_rate >= 68.0 and current_loss_streak == 0:
            directive = "BET"
            sentiment = "BULLISH"
            confidence = 82.0
            reasoning = (
                f"Favorable odds regime: SafeZone win rate is healthy at {safezone_win_rate:.1f}% with 0 active loss streak. "
                f"Multiplier dispersion indicates standard distribution."
            )
            recommendations.append(f"Standard betting cycle active at {target_odds:.2f}x target")
        else:
            directive = "BET" if current_loss_streak == 0 else "CAUTION"
            sentiment = "NEUTRAL"
            confidence = 65.0
            reasoning = (
                f"Market in balanced state. SafeZone win rate is {safezone_win_rate:.1f}% with current streak of {current_loss_streak}. "
                f"No abnormal clustering detected."
            )
            recommendations.append("Maintain baseline parameters")

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
