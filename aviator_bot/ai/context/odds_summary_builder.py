from __future__ import annotations

from typing import Any


def build_odds_summary(odds_records: list[dict[str, Any]], target_odds: float = 1.50) -> dict[str, Any]:
    """Aggregate raw multiplier records into structured analytical metrics for LLM reasoning."""
    if not odds_records:
        return {
            "total_rounds": 0,
            "target_odds": target_odds,
            "safezone_win_rate": 0.0,
            "loss_rate": 0.0,
            "max_loss_streak": 0,
            "current_loss_streak": 0,
            "loss_cluster_distribution": {},
            "recent_multipliers": [],
            "cold_pattern_detected": False,
        }

    total = len(odds_records)
    wins = 0
    cur_loss = 0
    cur_win = 0
    max_loss = 0
    loss_streaks = []
    sub_1_30_count = 0

    for item in odds_records:
        m = float(item["multiplier"])
        if m < 1.30:
            sub_1_30_count += 1

        if m >= target_odds:
            wins += 1
            if cur_loss > 0:
                loss_streaks.append(cur_loss)
                cur_loss = 0
            cur_win += 1
        else:
            if cur_win > 0:
                cur_win = 0
            cur_loss += 1
            if cur_loss > max_loss:
                max_loss = cur_loss

    if cur_loss > 0:
        loss_streaks.append(cur_loss)

    # Cluster frequency
    streak_freq = {str(i): 0 for i in range(1, 11)}
    streak_freq["11+"] = 0
    for s in loss_streaks:
        if 1 <= s <= 10:
            streak_freq[str(s)] += 1
        else:
            streak_freq["11+"] += 1

    win_rate = round((wins / total * 100), 1) if total > 0 else 0.0
    recent_pills = [round(float(item["multiplier"]), 2) for item in odds_records[-15:]]
    recent_sub_1_50 = sum(1 for m in recent_pills[-10:] if m < target_odds)

    # A "cold" cluster pattern is when 5+ of the last 10 rounds crashed below target odds
    cold_pattern = recent_sub_1_50 >= 5

    return {
        "total_rounds": total,
        "target_odds": target_odds,
        "safezone_win_rate": win_rate,
        "loss_rate": round(100.0 - win_rate, 1),
        "max_loss_streak": max_loss,
        "current_loss_streak": cur_loss,
        "current_win_streak": cur_win,
        "total_loss_clusters": len(loss_streaks),
        "loss_cluster_distribution": streak_freq,
        "sub_1_30_ratio": round((sub_1_30_count / total * 100), 1) if total > 0 else 0.0,
        "recent_multipliers": recent_pills,
        "cold_pattern_detected": cold_pattern,
    }
