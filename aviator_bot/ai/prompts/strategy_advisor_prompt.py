from __future__ import annotations

import json
from typing import Any

STRATEGY_SYSTEM_PROMPT = """You are a professional mathematical betting strategist specializing in Crash game bankroll management and Martingale/D'Alembert progression optimization.

Your goal is to optimize staking parameters based on the observed crash multiplier distribution to maximize capital preservation while generating consistent positive edge.

Mathematical rules to consider:
1. For an auto-cashout of C, Martingale recovery multiplier M should satisfy M >= 1 / (C - 1) so that a single win recoups all previous losses plus profit. (e.g. For C=1.50x, M=3.0x is ideal).
2. If the observed win rate at 1.50x is high (>= 60%), 1.50x with 3.0x multiplier and conservative base stake is high expected value.
3. If sub-1.30x clustering is elevated, advise lower base stake and fewer loss steps.

You MUST always return your response as valid JSON matching this schema:
{
  "recommended_base_stake": <float, e.g. 50.0>,
  "recommended_auto_cashout": <float, e.g. 1.50>,
  "recommended_multiplier": <float, e.g. 3.0>,
  "recommended_max_loss_steps": <integer, e.g. 4 or 5>,
  "recommended_stop_loss": <float, e.g. 10000.0>,
  "recommended_profit_target": <float, e.g. 5000.0>,
  "strategy_model": "<martingale | dalembert | flat>",
  "confidence_score": <integer from 1 to 100>,
  "strategy_rationale": "<Concise 2-3 sentence explanation of why these parameters are optimal right now>"
}
Do NOT include any markdown code fences or explanatory text outside the JSON object.
"""


def format_strategy_user_prompt(odds_summary: dict[str, Any], current_config: dict[str, Any]) -> str:
    """Format prompt payload for strategy optimization."""
    return f"""Optimize the staking parameters based on the actual table performance:

--- OBSERVED DISTRIBUTION ---
- Total Rounds Analyzed: {odds_summary.get('total_rounds')}
- Current SafeZone Win Rate at {odds_summary.get('target_odds')}x: {odds_summary.get('safezone_win_rate')}%
- Maximum Loss Streak: {odds_summary.get('max_loss_streak')}
- Sub-1.30x Crash Density: {odds_summary.get('sub_1_30_ratio')}%
- Recent Multipliers: {odds_summary.get('recent_multipliers')}
- Loss Cluster Breakdown: {json.dumps(odds_summary.get('loss_cluster_distribution', {}))}

--- CURRENT USER SETTINGS ---
- Current Base Stake: {current_config.get('base_stake')} NGN
- Current Target Cashout: {current_config.get('auto_cashout')}x
- Current Loss Multiplier: {current_config.get('multiplier')}x
- Current Max Loss Steps: {current_config.get('max_loss_steps')}
- Current Stop Loss: {current_config.get('stop_loss')} NGN
- Current Profit Target: {current_config.get('profit_target')} NGN
- Risk Appetite: {current_config.get('ai_risk_tolerance', 'conservative')}

Recommend the optimal, mathematically sound staking configuration.
"""
