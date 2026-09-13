from __future__ import annotations

import unittest
from aviator_bot.platforms.registry import PlatformRegistry
from aviator_bot.platforms.base.enums import GameCategory
from aviator_bot.ai.context.odds_summary_builder import build_odds_summary
from aviator_bot.ai.context.bankroll_context_builder import build_bankroll_summary
from aviator_bot.ai.parsers.json_extractor import extract_json, clean_json_text


class PlatformAddonTests(unittest.TestCase):
    def setUp(self):
        self.registry = PlatformRegistry.get_instance()

    def test_registered_platforms(self):
        platforms = self.registry.list_platforms()
        ids = [p["id"] for p in platforms]
        self.assertIn("ilotbet", ids)
        self.assertIn("bcgame", ids)
        self.assertIn("sportybet", ids)

    def test_ilotbet_aviator_game(self):
        game = self.registry.get_game("ilotbet", "best_aviator")
        self.assertEqual(game.game_id, "best_aviator")
        self.assertIn("Best Aviator", game.display_name)
        # Verify backward-compatibility alias
        game_alias = self.registry.get_game("ilotbet", "aviator")
        self.assertEqual(game_alias, game)
        self.assertEqual(game.category, GameCategory.CRASH)
        self.assertTrue(bool(game.selectors.stake_input_selector))
        self.assertTrue(bool(game.selectors.bet_button_selector))

    def test_bcgame_games(self):
        crash = self.registry.get_game("bcgame", "crash")
        self.assertEqual(crash.game_id, "crash")
        self.assertEqual(crash.category, GameCategory.CRASH)

        limbo = self.registry.get_game("bcgame", "limbo")
        self.assertEqual(limbo.game_id, "limbo")
        self.assertEqual(limbo.category, GameCategory.LIMBO)

    def test_sportybet_aviator_game(self):
        game = self.registry.get_game("sportybet", "aviator")
        self.assertEqual(game.game_id, "aviator")
        self.assertEqual(game.category, GameCategory.CRASH)


class AIContextAndParserTests(unittest.TestCase):
    def test_odds_summary_builder(self):
        # Sample odds: 3 wins (>=1.50) and 2 losses (<1.50)
        odds = [
            {"multiplier": 1.20},
            {"multiplier": 1.15},
            {"multiplier": 1.65},
            {"multiplier": 2.10},
            {"multiplier": 1.50},
        ]
        summary = build_odds_summary(odds, target_odds=1.50)
        self.assertEqual(summary["total_rounds"], 5)
        self.assertEqual(summary["safezone_win_rate"], 60.0)
        self.assertEqual(summary["max_loss_streak"], 2)
        self.assertEqual(summary["current_loss_streak"], 0)
        self.assertEqual(summary["current_win_streak"], 3)

    def test_bankroll_context_builder(self):
        bets = [
            {"stake": 50.0, "crash_multiplier": 1.20, "won": False, "profit_loss": -50.0},
            {"stake": 150.0, "crash_multiplier": 1.60, "won": True, "profit_loss": 25.0},
        ]
        summary = build_bankroll_summary(
            balance=5000.0,
            base_stake=50.0,
            current_stake=50.0,
            loss_streak=0,
            recent_bets=bets,
        )
        self.assertEqual(summary["balance"], 5000.0)
        self.assertEqual(summary["session_net_pnl"], -25.0)
        self.assertEqual(summary["total_bets_in_session"], 2)

    def test_json_extractor_clean(self):
        raw = '{"risk_score": 75, "risk_level": "HIGH"}'
        parsed = extract_json(raw)
        self.assertEqual(parsed["risk_score"], 75)
        self.assertEqual(parsed["risk_level"], "HIGH")

    def test_json_extractor_markdown_fenced(self):
        raw = """```json
{
  "risk_score": 85,
  "risk_level": "CRITICAL"
}
```"""
        parsed = extract_json(raw)
        self.assertEqual(parsed["risk_score"], 85)
        self.assertEqual(parsed["risk_level"], "CRITICAL")


class MultiAgentSwarmTests(unittest.TestCase):
    def test_swarm_execution_and_consensus(self):
        from aviator_bot.ai.agents.swarm_coordinator import SwarmCoordinator
        coordinator = SwarmCoordinator()
        telemetry = {
            "odds_records": [{"multiplier": 1.10}, {"multiplier": 1.25}, {"multiplier": 1.15}],
            "auto_cashout": 1.50,
            "base_stake": 50,
            "bankroll_data": {"loss_streak": 3, "current_stake": 450, "balance": 25000},
            "max_loss_steps": 5,
            "max_stake": 5000,
            "stop_loss": 10000,
            "profit_target": 5000,
            "session_profit": -150,
        }
        res = coordinator.run_swarm(telemetry)
        self.assertEqual(res["consensus_directive"], "PAUSE_STAKING")
        self.assertIn("analyst", res["agents"])
        self.assertIn("risk_guardian", res["agents"])
        self.assertIn("strategy_optimizer", res["agents"])
        self.assertIn("supervisor", res["agents"])
        self.assertGreater(len(res["recommendations"]), 0)

    def test_chat_memory_builder(self):
        from aviator_bot.ai.context.chat_memory_builder import build_chat_memory_context
        past_sessions = [
            {
                "title": "Previous Strategy Session",
                "msg_count": 4,
                "sample_exchanges": [{"role": "user", "content": "How does 1.35x cashout perform?"}],
                "updated_at": "2026-09-12T10:00:00Z"
            }
        ]
        curr_msgs = [{"sender_name": "User", "content": "Let's review that strategy again"}]
        context = build_chat_memory_context(curr_msgs, past_sessions)
        self.assertIn("CROSS-SESSION HISTORICAL MEMORY", context)
        self.assertIn("Previous Strategy Session", context)
        self.assertIn("Let's review that strategy again", context)


if __name__ == "__main__":
    unittest.main()

