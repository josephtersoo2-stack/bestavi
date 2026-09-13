from __future__ import annotations

from typing import Any


def build_bankroll_summary(
    balance: float | None,
    base_stake: float,
    current_stake: float,
    loss_streak: int,
    recent_bets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate financial state and recent ledger records for risk evaluation."""
    bets = recent_bets or []
    total_profit = sum(b.get("profit_loss", 0.0) for b in bets)
    total_bets = len(bets)
    wins = sum(1 for b in bets if b.get("won", False))
    win_rate = round((wins / total_bets * 100), 1) if total_bets > 0 else 0.0

    return {
        "balance": balance,
        "base_stake": base_stake,
        "current_stake": current_stake,
        "current_loss_streak": loss_streak,
        "total_bets_in_session": total_bets,
        "session_win_rate": win_rate,
        "session_net_pnl": round(total_profit, 2),
        "recent_bet_history": [
            {
                "stake": b.get("stake"),
                "crash": b.get("crash_multiplier"),
                "won": b.get("won"),
                "pnl": b.get("profit_loss"),
            }
            for b in bets[-5:]
        ],
    }
