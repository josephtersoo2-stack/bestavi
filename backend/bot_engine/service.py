from __future__ import annotations

import logging
import threading
import time
from typing import Any
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from aviator_bot.config.settings import BotSettings, BrowserSelectors
from aviator_bot.browser.controller import PlaywrightAdapter, DryRunAdapter
from aviator_bot.bot.controller import BotController
from .security import sanitize_log

logger = logging.getLogger("bot_engine.service")


class DjangoBotService:
    _instance: DjangoBotService | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.controller: BotController | None = None
        self.last_balance: float | None = None
        self.last_status: str = "IDLE"
        self.last_event_msg: str = "Ready"
        self.schedule_timer: threading.Timer | None = None
        self.schedule_stop_timer: threading.Timer | None = None
        self.scheduled_start_time: str | None = None
        self.scheduled_duration_minutes: int | None = None
        self.scheduled_auto_stake: bool = True
        self.schedule_active: bool = False
        self._ai_auto_paused: bool = False

        # Hybrid Architecture: Local Residential Desktop Runner State
        self.runner_connected: bool = False
        self.runner_ip: str | None = None
        self.runner_last_seen: float | None = None
        self.is_remote_running: bool = False
        self.is_remote_staking: bool = False

    @property
    def is_running(self) -> bool:
        if self.runner_connected:
            return bool(getattr(self, "is_remote_running", False))
        return bool(self.controller and self.controller.running)

    @property
    def is_staking(self) -> bool:
        if self.runner_connected:
            return bool(getattr(self, "is_remote_staking", False))
        return bool(self.controller and self.controller.is_authorized)

    @property
    def is_paused(self) -> bool:
        return bool(self.is_running and not self.is_staking)

    @property
    def balance(self) -> float | None:
        if self.controller and getattr(self.controller, "risk", None) and self.controller.risk.balance is not None:
            return self.controller.risk.balance
        return self.last_balance

    @property
    def current_stake(self) -> float:
        if self.controller:
            return getattr(self.controller, "current_stake", 50.0)
        return 50.0

    @property
    def loss_streak(self) -> int:
        if self.controller and getattr(self.controller, "risk", None):
            return getattr(self.controller.risk, "loss_streak", 0)
        return 0

    @property
    def session_profit(self) -> float:
        if self.controller and getattr(self.controller, "risk", None):
            return getattr(self.controller.risk, "session_profit", 0.0)
        return 0.0

    @classmethod
    def get_instance(cls) -> DjangoBotService:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "bot_updates",
                    {
                        "type": "bot_event",
                        "event_type": event_type,
                        "data": data,
                    }
                )
        except Exception as exc:
            logger.debug("Failed to broadcast WebSocket event: %s", exc)

    def _on_bot_event(self, event: str | tuple) -> None:
        import os
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

        from .models import ExtractedOdds, BetRecord, BotLog

        if isinstance(event, tuple):
            if event[0] == "log":
                msg = sanitize_log(str(event[1]))
                try:
                    BotLog.objects.create(level="INFO", message=msg)
                except Exception as exc:
                    logger.debug("Could not record BotLog: %s", exc)
                self._broadcast("log", {"message": msg})
                return
            event = str(event)

        msg = sanitize_log(str(event))
        self.last_event_msg = msg

        # Save log entry
        try:
            BotLog.objects.create(level="INFO", message=msg)
        except Exception as exc:
            logger.debug("Could not record BotLog: %s", exc)

        # 1. Extracted live multiplier
        if msg.startswith("extracted_result: "):
            try:
                val = float(msg.replace("extracted_result: ", ""))
                from .models import BotConfig
                cfg = BotConfig.get_active()
                site = cfg.platform or cfg.site or "ilotbet"
                game = cfg.game or "best_aviator"
                ExtractedOdds.objects.create(multiplier=val, site=site, game=game)
                recent = self.get_recent_multipliers(10)
                self._broadcast("odds_extracted", {
                    "multiplier": val,
                    "recent_ribbon": recent,
                })

                # Autonomous Multi-Agent Swarm Staking Hook
                if cfg.ai_enabled and cfg.ai_autonomous_mode and self.is_running:
                    self._check_autonomous_swarm_directive(cfg)
            except Exception as exc:
                logger.error("Error saving extracted odds: %s", exc)
            return

        # 2. Result of a bet round
        if msg.startswith("Result "):
            bal = self.controller.risk.balance if (self.controller and self.controller.risk.balance is not None) else None
            if bal is not None:
                self.last_balance = bal
            self._broadcast("round_result", {
                "message": msg,
                "balance": bal,
                "current_stake": self.controller.current_stake if self.controller else 0.0,
                "loss_streak": self.controller.risk.loss_streak if self.controller else 0,
            })
            return

        # 3. Balance updated
        if msg.startswith("balance_updated: "):
            try:
                bal = float(msg.replace("balance_updated: ", ""))
                self.last_balance = bal
                self._broadcast("balance_updated", {"balance": bal})
            except Exception:
                pass
            return

        # 4. Status change
        if msg.startswith("Status: "):
            self.last_status = msg.replace("Status: ", "")
            self._broadcast("status_changed", {"status": self.last_status})
            return

        self._broadcast("bot_message", {"message": msg})

    # =========================================================================
    # Hybrid Architecture: Remote Desktop Runner Relay Methods
    # =========================================================================
    def _send_runner_command(self, action: str, params: dict[str, Any] | None = None) -> bool:
        """Send command to connected desktop runner agent via channel layer."""
        if not self.runner_connected:
            return False
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "runner_agents",
                    {
                        "type": "runner_command",
                        "command": action,
                        "params": params or {},
                    }
                )
                return True
        except Exception as exc:
            logger.error("Failed to forward command to desktop runner: %s", exc)
        return False

    def set_runner_connected(self, connected: bool, client_ip: str = "") -> None:
        self.runner_connected = connected
        if connected:
            self.runner_ip = client_ip
            self.runner_last_seen = time.time()
            self._on_bot_event(f"Desktop Runner Connected ({client_ip} - Residential IP Active)")
        else:
            self.is_remote_running = False
            self.is_remote_staking = False
            self._on_bot_event("Desktop Runner Disconnected")

    def touch_runner_heartbeat(self) -> None:
        self.runner_last_seen = time.time()

    def handle_remote_odds(self, multiplier: float) -> None:
        self.touch_runner_heartbeat()
        self.is_remote_running = True
        try:
            from .models import ExtractedOdds, BotConfig
            ExtractedOdds.objects.create(multiplier=multiplier)
            recent = self.get_recent_multipliers(10)
            self._broadcast("odds_extracted", {
                "multiplier": multiplier,
                "recent_ribbon": recent,
            })
            cfg = BotConfig.get_active()
            if cfg.ai_enabled and cfg.ai_autonomous_mode and self.is_running:
                self._check_autonomous_swarm_directive(cfg)
        except Exception as exc:
            logger.error("Error saving remote odds: %s", exc)

    def handle_remote_round_result(self, message: str, balance: float | None, current_stake: float, loss_streak: int) -> None:
        self.touch_runner_heartbeat()
        if balance is not None:
            self.last_balance = balance
        self._broadcast("round_result", {
            "message": message,
            "balance": balance,
            "current_stake": current_stake,
            "loss_streak": loss_streak,
        })

    def handle_remote_balance(self, balance: float) -> None:
        self.touch_runner_heartbeat()
        self.last_balance = balance
        self._broadcast("balance_updated", {"balance": balance})

    def handle_remote_status(self, status: str, is_running: bool, is_staking: bool) -> None:
        self.touch_runner_heartbeat()
        self.last_status = status
        self.is_remote_running = is_running
        self.is_remote_staking = is_staking
        self._broadcast("status_changed", {"status": status})

    def handle_remote_log(self, level: str, message: str) -> None:
        self.touch_runner_heartbeat()
        from .models import BotLog
        try:
            BotLog.objects.create(level=level.upper(), message=message)
        except Exception:
            pass
        self._broadcast("log", {"message": message})

    # =========================================================================
    # Control Actions (Hybrid Remote + Local Fallback)
    # =========================================================================
    def prepare(self) -> dict[str, Any]:
        from dataclasses import replace
        from pathlib import Path
        from django.conf import settings as django_settings
        from aviator_bot.config.site_profiles import profile
        from aviator_bot.config.settings import load_settings
        from .models import BotConfig

        config = BotConfig.get_active()
        game_url = config.get_decrypted_game_url()
        platform_key = (config.platform or config.site or "ilotbet").lower().strip()
        game_key = (config.game or "best_aviator").lower().strip()

        # Hybrid Mode: If Desktop Runner is connected, forward command to runner
        if self.runner_connected:
            self._send_runner_command("prepare", {
                "platform": platform_key,
                "game": game_key,
                "game_url": game_url,
                "base_stake": float(config.base_stake),
                "auto_cashout": float(config.auto_cashout),
                "strategy": config.strategy,
                "dry_run": config.dry_run,
            })
            self.last_status = "Remote Desktop: Preparing Browser..."
            self.is_remote_running = True
            self.is_remote_staking = False
            self._broadcast("status_changed", {"status": self.last_status})
            return {"status": "ok", "message": "Command sent to Desktop Runner (Launching local Chrome)"}

        if not game_url:
            return {"status": "error", "message": "Game URL is not configured. Please set the game URL in the Bot Configuration."}

        project_root = Path(django_settings.BASE_DIR).parent.resolve()
        settings_file = project_root / "config" / "settings.json"
        data_dir = project_root / "data"
        user_data_path = str(data_dir / f"browser_profile_{platform_key}")

        try:
            file_settings = load_settings(str(settings_file))
            base_browser = replace(
                file_settings.browser,
                url=game_url,
                headless=False,
                user_data_dir=user_data_path
            )
        except Exception:
            base_browser = BrowserSelectors(
                url=game_url,
                headless=False,
                user_data_dir=user_data_path
            )

        browser_selectors = replace(profile(platform_key, base=base_browser), user_data_dir=user_data_path, headless=False)

        settings = BotSettings(
            base_stake=config.base_stake,
            strategy=config.strategy,
            multiplier=config.multiplier,
            auto_cashout=config.auto_cashout,
            max_stake=config.max_stake,
            max_loss_steps=config.max_loss_steps,
            stop_loss=config.stop_loss,
            profit_target=config.profit_target,
            dry_run=config.dry_run,
            network_auto_retry=config.network_auto_retry,
            network_retry_delay=config.network_retry_delay,
            network_max_retries=config.network_max_retries,
            site=platform_key,
            browser=browser_selectors
        )

        if self.controller and self.controller.running:
            self.controller.update_settings(settings)
            self.last_status = "Prepared (Running)"
            return {"status": "ok", "message": "Bot settings updated on live session"}

        if self.controller:
            try:
                self.controller.close()
            except Exception:
                pass
            self.controller = None

        adapter = DryRunAdapter() if config.dry_run else PlaywrightAdapter(
            settings.browser,
            platform_id=platform_key,
            game_id=game_key
        )
        self.controller = BotController(settings=settings, adapter=adapter, on_event=self._on_bot_event)
        self.controller.start(authorized=False)
        self.last_status = "Preparing Game Controls..."
        return {"status": "ok", "message": "Game preparation started (Visible browser opened)"}

    def start_staking(self) -> dict[str, Any]:
        if self.runner_connected:
            self._send_runner_command("start")
            self.is_remote_running = True
            self.is_remote_staking = True
            self.last_status = "Remote Desktop: Live Staking Active"
            self._broadcast("status_changed", {"status": self.last_status})
            return {"status": "ok", "message": "Live staking started on Desktop Runner"}

        if not self.controller or not self.controller.running:
            self.prepare()
        if self.controller:
            self.controller.authorize()
            self.last_status = "Live Auto-Staking Active"
            return {"status": "ok", "message": "Live staking started"}
        return {"status": "error", "message": "Could not initialize bot controller"}

    def pause_staking(self) -> dict[str, Any]:
        if self.runner_connected:
            self._send_runner_command("pause")
            self.is_remote_staking = False
            self.last_status = "Remote Desktop: Staking Paused"
            self._broadcast("status_changed", {"status": self.last_status})
            return {"status": "ok", "message": "Staking paused on Desktop Runner"}

        if self.controller and self.controller.running:
            self.controller.pause_staking()
            self.last_status = "Staking Paused (Extracting Results)"
            return {"status": "ok", "message": "Live staking paused. Result observation active."}
        return {"status": "error", "message": "Bot is not running"}

    def emergency_stop(self) -> dict[str, Any]:
        if self.schedule_stop_timer:
            self.schedule_stop_timer.cancel()
            self.schedule_stop_timer = None

        if self.runner_connected:
            self._send_runner_command("stop")
            self.is_remote_running = False
            self.is_remote_staking = False
            self.last_status = "Remote Desktop: STOPPED"
            self._broadcast("status_changed", {"status": self.last_status})
            return {"status": "ok", "message": "Emergency stop executed on Desktop Runner"}

        if self.controller:
            self.controller.stop()
            self.controller = None
            self.last_status = "STOPPED"
            return {"status": "ok", "message": "Emergency stop executed"}
        return {"status": "ok", "message": "Bot was not active"}

    def schedule_auto_start(self, start_in_seconds: float, duration_minutes: int | None = None, target_iso_time: str | None = None, auto_stake: bool = True) -> dict[str, Any]:
        self.cancel_schedule()
        self.schedule_active = True
        self.scheduled_start_time = target_iso_time
        self.scheduled_duration_minutes = duration_minutes
        self.scheduled_auto_stake = auto_stake

        self.schedule_timer = threading.Timer(start_in_seconds, self._execute_scheduled_start, args=[duration_minutes, auto_stake])
        self.schedule_timer.daemon = True
        self.schedule_timer.start()

        mode_desc = "Live Auto-Staking" if auto_stake else "Odds Data Collection (Observation)"
        self._broadcast("schedule_updated", {
            "active": True,
            "start_time": target_iso_time,
            "duration_minutes": duration_minutes,
            "auto_stake": auto_stake,
        })
        self._on_bot_event(f"Schedule armed [{mode_desc}]: Auto-prepare visible browser in {int(start_in_seconds)}s" + (f", auto-stop in {duration_minutes}m" if duration_minutes else ""))
        return {"status": "ok", "message": f"Bot scheduled to launch ({mode_desc}) in {int(start_in_seconds)} seconds"}

    def cancel_schedule(self) -> dict[str, Any]:
        if self.schedule_timer:
            self.schedule_timer.cancel()
            self.schedule_timer = None
        if self.schedule_stop_timer:
            self.schedule_stop_timer.cancel()
            self.schedule_stop_timer = None
        was_active = self.schedule_active
        self.schedule_active = False
        self.scheduled_start_time = None
        self.scheduled_duration_minutes = None
        self.scheduled_auto_stake = True

        self._broadcast("schedule_updated", {
            "active": False,
            "start_time": None,
            "duration_minutes": None,
            "auto_stake": True,
        })
        if was_active:
            self._on_bot_event("Active schedule cancelled by user.")
        return {"status": "ok", "message": "Schedule cancelled"}

    def _execute_scheduled_start(self, duration_minutes: int | None = None, auto_stake: bool = True) -> None:
        self.schedule_active = False
        self.scheduled_start_time = None
        action_desc = "and starting live auto-staking" if auto_stake else "(Observation Mode: collecting odds data without staking)"
        self._on_bot_event(f"Scheduled start triggered: Opening visible browser, preparing game interface, {action_desc}...")
        self._broadcast("schedule_updated", {
            "active": False,
            "start_time": None,
            "duration_minutes": self.scheduled_duration_minutes,
            "auto_stake": auto_stake,
        })

        prep_res = self.prepare()
        if prep_res.get("status") == "error":
            self._on_bot_event(f"Scheduled start error during prepare: {prep_res.get('message')}")
            return

        if auto_stake:
            import time
            time.sleep(2.5)
            start_res = self.start_staking()
            self._on_bot_event(f"Scheduled live staking started: {start_res.get('message')}")
        else:
            self._on_bot_event("Scheduled launch complete: Visible browser opened and game controls prepared. Live Odds Extractor is actively collecting round data.")

        if duration_minutes and duration_minutes > 0:
            self._on_bot_event(f"Auto-stop timer armed for {duration_minutes} minutes.")
            self.schedule_stop_timer = threading.Timer(duration_minutes * 60, self._execute_scheduled_stop)
            self.schedule_stop_timer.daemon = True
            self.schedule_stop_timer.start()

    def _execute_scheduled_stop(self) -> None:
        self._on_bot_event("Scheduled duration elapsed: executing safe automatic stop.")
        self.emergency_stop()

    def _check_autonomous_swarm_directive(self, cfg: Any) -> None:
        """Autonomously pause or resume staking based on multi-agent swarm consensus."""
        try:
            from aviator_bot.ai.ai_engine import AIEngine
            from .chat_views import _get_active_telemetry
            engine = AIEngine()
            telemetry = _get_active_telemetry(cfg)
            swarm = engine.evaluate_swarm(telemetry)
            directive = swarm.get("consensus_directive")
            score = swarm.get("consensus_score", 0)
            reason = swarm.get("consensus_summary", "")

            # If directive is PAUSE_STAKING and bot is currently staking
            if directive == "PAUSE_STAKING" and self.is_staking:
                self.pause_staking()
                self._ai_auto_paused = True
                log_msg = f"[AI Swarm Alert ({score}%)] Staking autonomously paused: {reason}"
                logger.warning(log_msg)
                from .models import BotLog
                BotLog.objects.create(level="WARNING", message=log_msg)
                self._broadcast("log", {"message": log_msg})
                self._broadcast("swarm_directive_triggered", {"directive": directive, "score": score, "reason": reason})

            # If directive is BET or RESUME_STAKING and bot was paused by AI
            elif directive in ("BET", "RESUME_STAKING") and getattr(self, "_ai_auto_paused", False) and not self.is_staking:
                self.start_staking()
                self._ai_auto_paused = False
                log_msg = f"[AI Swarm Alert ({score}%)] Staking autonomously resumed: Favorable regime detected."
                logger.info(log_msg)
                from .models import BotLog
                BotLog.objects.create(level="INFO", message=log_msg)
                self._broadcast("log", {"message": log_msg})
                self._broadcast("swarm_directive_triggered", {"directive": directive, "score": score, "reason": reason})
        except Exception as exc:
            logger.debug("Autonomous swarm evaluation error: %s", exc)


    def get_recent_multipliers(self, count: int = 10) -> list[float]:
        if self.controller and self.controller.recent_live_multipliers:
            return self.controller.recent_live_multipliers[:count]
        from .models import ExtractedOdds
        odds = list(ExtractedOdds.objects.values_list('multiplier', flat=True)[:count])
        return odds

    def get_status(self) -> dict[str, Any]:
        bal = self.controller.risk.balance if (self.controller and self.controller.risk.balance is not None) else self.last_balance
        state = self.controller.state.value if self.controller else ("RUNNING" if self.is_running else "STOPPED")
        is_running = self.is_running
        is_staking = self.is_staking
        current_stake = self.controller.current_stake if self.controller else 50.0
        loss_streak = self.controller.risk.loss_streak if self.controller else 0

        return {
            "is_running": is_running,
            "is_staking": is_staking,
            "state": state,
            "status_text": self.last_status,
            "balance": bal,
            "current_stake": current_stake,
            "loss_streak": loss_streak,
            "recent_multipliers": self.get_recent_multipliers(8),
            "last_message": self.last_event_msg,
            "runner_connected": self.runner_connected,
            "runner_ip": getattr(self, "runner_ip", None),
            "runner_last_seen": getattr(self, "runner_last_seen", None),
            "schedule": {
                "active": self.schedule_active,
                "start_time": self.scheduled_start_time,
                "duration_minutes": self.scheduled_duration_minutes,
                "auto_stake": self.scheduled_auto_stake,
            }
        }


# Global singleton instance for clean imports
bot_service = DjangoBotService.get_instance()
