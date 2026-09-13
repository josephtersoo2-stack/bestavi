from __future__ import annotations

import json
import logging
from typing import Any

from .config import AIConfig
from .providers.gemini_provider import GeminiProvider
from .providers.openrouter_provider import OpenRouterProvider
from .context.odds_summary_builder import build_odds_summary
from .context.bankroll_context_builder import build_bankroll_summary
from .prompts.risk_assessment_prompt import RISK_SYSTEM_PROMPT, format_risk_user_prompt
from .prompts.strategy_advisor_prompt import STRATEGY_SYSTEM_PROMPT, format_strategy_user_prompt
from .prompts.market_chat_prompt import get_chat_system_prompt
from .parsers.json_extractor import extract_json
from .agents.swarm_coordinator import SwarmCoordinator
from .context.chat_memory_builder import build_chat_memory_context, build_discovery_memories_context

logger = logging.getLogger("aviator_bot.ai.engine")


class AIEngine:
    """Central AI engine coordinating provider selection, prompts, and analysis."""

    def __init__(self) -> None:
        self.gemini = GeminiProvider()
        self.openrouter = OpenRouterProvider()
        self.swarm = SwarmCoordinator()

    def get_provider_client(self, provider_name: str) -> GeminiProvider | OpenRouterProvider:
        name = (provider_name or "gemini").lower().strip()
        if "openrouter" in name:
            return self.openrouter
        return self.gemini

    def fetch_available_models(self, provider_name: str, api_key: str) -> list[dict[str, str]]:
        """Query the remote platform to dynamically fetch its active models."""
        client = self.get_provider_client(provider_name)
        return client.fetch_models(api_key)

    def assess_risk(
        self,
        odds_records: list[dict[str, Any]],
        bankroll_data: dict[str, Any],
        config: AIConfig,
    ) -> dict[str, Any]:
        """Perform quantitative loss-cluster risk analysis with the chosen LLM."""
        target_odds = float(bankroll_data.get("auto_cashout") or 1.50)
        odds_summary = build_odds_summary(odds_records, target_odds=target_odds)
        bankroll_summary = build_bankroll_summary(
            balance=bankroll_data.get("balance"),
            base_stake=float(bankroll_data.get("base_stake") or 50.0),
            current_stake=float(bankroll_data.get("current_stake") or 50.0),
            loss_streak=int(bankroll_data.get("loss_streak") or 0),
            recent_bets=bankroll_data.get("recent_bets"),
        )

        user_prompt = format_risk_user_prompt(odds_summary, bankroll_summary)
        client = self.get_provider_client(config.provider)

        raw_response = client.generate(
            prompt=user_prompt,
            system_prompt=RISK_SYSTEM_PROMPT,
            model=config.model_name,
            api_key=config.api_key,
            temperature=config.temperature,
        )

        parsed = extract_json(raw_response)
        parsed["odds_summary"] = odds_summary
        return parsed

    def recommend_strategy(
        self,
        odds_records: list[dict[str, Any]],
        current_settings: dict[str, Any],
        config: AIConfig,
    ) -> dict[str, Any]:
        """Generate optimal mathematical staking parameters tailored to the observed distribution."""
        target_odds = float(current_settings.get("auto_cashout") or 1.50)
        odds_summary = build_odds_summary(odds_records, target_odds=target_odds)
        user_prompt = format_strategy_user_prompt(odds_summary, current_settings)
        client = self.get_provider_client(config.provider)

        raw_response = client.generate(
            prompt=user_prompt,
            system_prompt=STRATEGY_SYSTEM_PROMPT,
            model=config.model_name,
            api_key=config.api_key,
            temperature=config.temperature,
        )

        parsed = extract_json(raw_response)
        parsed["odds_summary"] = odds_summary
        return parsed

    def evaluate_swarm(
        self,
        telemetry: dict[str, Any],
        config: AIConfig | None = None,
    ) -> dict[str, Any]:
        """Execute parallel multi-agent swarm evaluation and return synthesized consensus."""
        return self.swarm.run_swarm(telemetry, config)

    def chat_copilot(
        self,
        user_message: str,
        odds_records: list[dict[str, Any]],
        platform: str,
        game: str,
        config: AIConfig,
        current_messages: list[dict[str, Any]] | None = None,
        past_sessions_summary: list[dict[str, Any]] | None = None,
        swarm_consensus: dict[str, Any] | None = None,
        discovery_memories: list[dict[str, Any]] | None = None,
    ) -> str:
        """Interactive conversation with Multi-Agent Swarm grounded in live odds, streak hours, and discovery memory."""
        target_odds = 1.50
        summary = build_odds_summary(odds_records, target_odds=target_odds)
        context_str = f"""
- Sample Size: {summary['total_rounds']} rounds
- SafeZone Win Rate (>= 1.50x): {summary['safezone_win_rate']}%
- Loss Rate (< 1.50x): {summary['loss_rate']}%
- Max Loss Streak: {summary['max_loss_streak']}
- Current Loss Streak: {summary['current_loss_streak']}
- Recent 15 Multipliers: {summary['recent_multipliers']}
- Loss Streak Clusters: {json.dumps(summary['loss_cluster_distribution'])}
- Long Loss Streaks (>=4 in a row): {summary.get('streak_timing_summary')}
- Hourly Loss Streak (>=4) Occurrences: {json.dumps(summary.get('hourly_streak_distribution', {}))}
"""
        memory_str = build_chat_memory_context(
            current_session_messages=current_messages or [],
            past_sessions_summary=past_sessions_summary,
        )
        discovery_str = build_discovery_memories_context(discovery_memories)

        swarm_str = ""
        if swarm_consensus:
            directive = swarm_consensus.get("consensus_directive", "BET")
            score = swarm_consensus.get("consensus_score", 50.0)
            reason = swarm_consensus.get("consensus_summary", "")
            swarm_str = f"Directive: {directive} | Confidence: {score}%\nReasoning: {reason}"

        system_prompt = get_chat_system_prompt(
            platform=platform,
            game=game,
            odds_context=context_str,
            memory_context=memory_str,
            swarm_context=swarm_str,
            discovery_context=discovery_str,
        )
        client = self.get_provider_client(config.provider)

        return client.generate(
            prompt=user_message,
            system_prompt=system_prompt,
            model=config.model_name,
            api_key=config.api_key,
            temperature=0.4,
        )


