from __future__ import annotations

import json
from typing import Any

RISK_SYSTEM_PROMPT = """You are an advanced quantitative risk analyst specializing in crash games (Aviator, Crash, Limbo).
Your objective is to protect player capital, identify dangerous loss clustering (consecutive sub-1.50x multipliers), and provide actionable risk ratings.

You MUST always return your final response as valid JSON matching this schema:
{
  "risk_score": <integer from 1 to 100, where 1 is minimal risk and 100 is extreme cluster danger>,
  "risk_level": "<LOW | MODERATE | HIGH | CRITICAL>",
  "market_regime": "<NORMAL | COLD_CLUSTER | VOLATILE | HOT_STREAK>",
  "cluster_threat_summary": "<One concise sentence describing current loss streak hazard>",
  "action_recommendation": "<CONTINUE | CAUTION | PAUSE_STAKING | LOWER_STAKE>",
  "autonomous_pause_advised": <boolean, true if severe clustering warrants immediately pausing live staking>,
  "key_findings": ["<bullet point 1>", "<bullet point 2>", "<bullet point 3>"]
}
Do NOT include any markdown code fences or explanatory text outside the JSON object.
"""


def format_risk_user_prompt(odds_summary: dict[str, Any], bankroll_summary: dict[str, Any]) -> str:
    """Format prompt payload for the LLM."""
    return f"""Analyze current live crash round patterns and financial exposure:

--- RECENT CRASH ODDS METRICS ---
- Total Sample Rounds: {odds_summary.get('total_rounds')}
- Target Cashout: {odds_summary.get('target_odds')}x
- SafeZone Win Rate (>= {odds_summary.get('target_odds')}x): {odds_summary.get('safezone_win_rate')}%
- Loss Rate (< {odds_summary.get('target_odds')}x): {odds_summary.get('loss_rate')}%
- Maximum Observed Loss Streak: {odds_summary.get('max_loss_streak')}
- Current Active Loss Streak: {odds_summary.get('current_loss_streak')}
- Sub-1.30x Crash Density: {odds_summary.get('sub_1_30_ratio')}%
- Cold Cluster Pattern Flag: {odds_summary.get('cold_pattern_detected')}
- Recent Multiplier Ribbon (latest 15): {odds_summary.get('recent_multipliers')}
- Loss Streak Distribution (consecutive loss cluster counts): {json.dumps(odds_summary.get('loss_cluster_distribution', {}))}

--- BANKROLL & STAKE STATUS ---
- Current Balance: {bankroll_summary.get('balance')}
- Base Stake: {bankroll_summary.get('base_stake')}
- Current Escalation Stake: {bankroll_summary.get('current_stake')}
- Session Net P/L: {bankroll_summary.get('session_net_pnl')}
- Recent Bet History: {json.dumps(bankroll_summary.get('recent_bet_history', []))}

Evaluate the current pattern risk. Calculate the probability of hitting a 5+ loss streak in the immediate future and return the structured JSON evaluation.
"""
