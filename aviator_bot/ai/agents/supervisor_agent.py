from __future__ import annotations

import logging
from typing import Any
from .base_agent import BaseAgent, AgentEvaluation
from ..config import AIConfig

logger = logging.getLogger("aviator_bot.ai.agents.supervisor")


class SupervisorAgent(BaseAgent):
    """Swarm Executive Synthesizer: Aggregates agent votes, weighs risk, and issues consensus directive."""

    @property
    def agent_id(self) -> str:
        return "supervisor"

    @property
    def name(self) -> str:
        return "Swarm Executive Supervisor"

    @property
    def role(self) -> str:
        return "Executive Synthesizer & Directive Issuer"

    def evaluate(
        self,
        telemetry: dict[str, Any],
        config: AIConfig | None = None,
    ) -> AgentEvaluation:
        # If peer evaluations provided in telemetry, synthesize directly
        peer_evals: dict[str, AgentEvaluation] = telemetry.get("peer_evaluations", {})
        return self.synthesize(peer_evals, telemetry)

    def synthesize(
        self,
        peer_evaluations: dict[str, AgentEvaluation],
        telemetry: dict[str, Any],
    ) -> AgentEvaluation:
        """Synthesize multiple agent evaluations into a binding swarm consensus."""
        analyst = peer_evaluations.get("analyst")
        risk_guardian = peer_evaluations.get("risk_guardian")
        strategy_optimizer = peer_evaluations.get("strategy_optimizer")

        # 1. Safety Veto Check: Risk Guardian or Analyst demanding immediate pause
        if risk_guardian and risk_guardian.directive == "PAUSE_STAKING":
            return AgentEvaluation(
                agent_id=self.agent_id,
                name=self.name,
                role=self.role,
                directive="PAUSE_STAKING",
                confidence=risk_guardian.confidence,
                sentiment="CRITICAL",
                reasoning=f"Executive Safety Veto enacted by Risk Guardian: {risk_guardian.reasoning}",
                metrics={"consensus_score": 15.0, "veto_agent": "risk_guardian"},
                recommendations=risk_guardian.recommendations + ["Bot staking autonomously suspended"],
            )

        if analyst and analyst.directive == "PAUSE_STAKING" and analyst.confidence >= 80.0:
            return AgentEvaluation(
                agent_id=self.agent_id,
                name=self.name,
                role=self.role,
                directive="PAUSE_STAKING",
                confidence=analyst.confidence,
                sentiment="CRITICAL",
                reasoning=f"Executive Hazard Intercept enacted by Analyst: {analyst.reasoning}",
                metrics={"consensus_score": 25.0, "veto_agent": "analyst"},
                recommendations=analyst.recommendations + ["Observing telemetry until safezone stabilizes"],
            )

        # 2. Weighted Score Calculation
        # Base weights: Risk Guardian (40%), Analyst (35%), Strategy (25%)
        weights = {"risk_guardian": 0.40, "analyst": 0.35, "strategy_optimizer": 0.25}
        total_score = 0.0
        active_weight = 0.0

        for agent_key, weight in weights.items():
            ev = peer_evaluations.get(agent_key)
            if not ev:
                continue
            active_weight += weight
            # Directional multiplier based on directive
            dir_val = 1.0 if ev.directive == "BET" else (0.5 if ev.directive == "CAUTION" else 0.0)
            agent_score = (ev.confidence * 0.5) + (dir_val * 50.0)
            total_score += agent_score * weight

        consensus_score = round(total_score / max(active_weight, 0.01), 1)

        # 3. Consensus Directive Decision
        all_recs: list[str] = []
        for ev in peer_evaluations.values():
            all_recs.extend(ev.recommendations)

        if consensus_score >= 70.0:
            directive = "BET"
            sentiment = "BULLISH"
            reasoning = (
                f"Swarm Consensus: Favorable alignment across all agents with {consensus_score}% agreement. "
                f"Risk exposure is controlled, expected value is positive, and streak variance is within tolerances."
            )
        elif consensus_score >= 50.0:
            directive = "CAUTION"
            sentiment = "NEUTRAL"
            reasoning = (
                f"Swarm Consensus: Moderate confidence ({consensus_score}%). Market exhibits mixed signals. "
                f"Proceed with measured stakes or tighter auto-cashout targets."
            )
        else:
            directive = "PAUSE_STAKING"
            sentiment = "BEARISH"
            reasoning = (
                f"Swarm Consensus: Sub-threshold agreement ({consensus_score}%). Combined risk signals advise "
                f"pausing automated betting until conditions improve."
            )

        return AgentEvaluation(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            directive=directive,
            confidence=consensus_score,
            sentiment=sentiment,
            reasoning=reasoning,
            metrics={"consensus_score": consensus_score},
            recommendations=list(dict.fromkeys(all_recs))[:4],
        )
