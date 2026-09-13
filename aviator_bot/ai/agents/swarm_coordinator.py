from __future__ import annotations

import logging
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .base_agent import AgentEvaluation
from .analyst_agent import AnalystAgent
from .risk_guardian_agent import RiskGuardianAgent
from .strategy_optimizer_agent import StrategyOptimizerAgent
from .supervisor_agent import SupervisorAgent
from ..config import AIConfig

logger = logging.getLogger("aviator_bot.ai.agents.coordinator")


class SwarmCoordinator:
    """Orchestrates parallel execution of specialized agents and computes swarm consensus."""

    def __init__(self) -> None:
        self.analyst = AnalystAgent()
        self.risk_guardian = RiskGuardianAgent()
        self.strategy_optimizer = StrategyOptimizerAgent()
        self.supervisor = SupervisorAgent()

    def run_swarm(
        self,
        telemetry: dict[str, Any],
        config: AIConfig | None = None,
    ) -> dict[str, Any]:
        """Execute all specialized agents concurrently and synthesize executive consensus."""
        peer_agents = [self.analyst, self.risk_guardian, self.strategy_optimizer]
        peer_evaluations: dict[str, AgentEvaluation] = {}

        # 1. Execute peer agents in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_agent = {
                executor.submit(agent.evaluate, telemetry, config): agent
                for agent in peer_agents
            }
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    eval_result = future.result()
                    peer_evaluations[agent.agent_id] = eval_result
                except Exception as exc:
                    logger.exception("Agent %s failed evaluation: %s", agent.agent_id, exc)
                    # Safe fallback evaluation for failing agent
                    peer_evaluations[agent.agent_id] = AgentEvaluation(
                        agent_id=agent.agent_id,
                        name=agent.name,
                        role=agent.role,
                        directive="CAUTION",
                        confidence=50.0,
                        sentiment="NEUTRAL",
                        reasoning=f"Agent encountered temporary error during telemetry evaluation: {exc}",
                    )

        # 2. Executive Synthesis by Supervisor
        supervisor_eval = self.supervisor.synthesize(peer_evaluations, telemetry)
        all_agents = {**peer_evaluations, "supervisor": supervisor_eval}

        return {
            "consensus_directive": supervisor_eval.directive,
            "consensus_score": supervisor_eval.confidence,
            "consensus_sentiment": supervisor_eval.sentiment,
            "consensus_summary": supervisor_eval.reasoning,
            "recommendations": supervisor_eval.recommendations,
            "agents": {k: v.to_dict() for k, v in all_agents.items()},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
