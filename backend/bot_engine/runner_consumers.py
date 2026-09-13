from __future__ import annotations

import json
import logging
import time
from typing import Any
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .security import authenticate_websocket_scope

logger = logging.getLogger("bot_engine.runner_consumers")


class RunnerConsumer(AsyncWebsocketConsumer):
    """Secure WebSocket endpoint for the Local Residential Desktop Runner Agent.
    
    Acts as the bidirectional command and telemetry relay between the Cloud Web Platform
    and the user's home/office personal PC.
    """

    room_group_name = "runner_agents"

    async def connect(self):
        # 1. Grade-A Authentication
        if not authenticate_websocket_scope(self.scope):
            logger.warning("[Runner Relay] Unauthorized connection attempt rejected.")
            await self.close(code=4003)
            return

        # 2. Join the runner channel group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        client_ip = self.scope.get("client", ["unknown"])[0]
        logger.info("[Runner Relay] Local Desktop Runner connected from %s", client_ip)

        # 3. Update Service State & Notify Web UI
        from .service import bot_service
        await database_sync_to_async(bot_service.set_runner_connected)(True, client_ip)

        # Broadcast runner online event to web dashboard
        await self.channel_layer.group_send(
            "bot_updates",
            {
                "type": "bot_event",
                "event_type": "runner_status",
                "data": {
                    "connected": True,
                    "client_ip": client_ip,
                    "timestamp": time.time(),
                }
            }
        )

        await self.send(text_data=json.dumps({
            "type": "runner_connected",
            "message": "Desktop Runner Authenticated & Connected to Cloud Relay",
            "status": "ready"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        logger.info("[Runner Relay] Local Desktop Runner disconnected (code: %s)", close_code)

        from .service import bot_service
        await database_sync_to_async(bot_service.set_runner_connected)(False)

        # Broadcast runner offline event to web dashboard
        await self.channel_layer.group_send(
            "bot_updates",
            {
                "type": "bot_event",
                "event_type": "runner_status",
                "data": {
                    "connected": False,
                    "timestamp": time.time(),
                }
            }
        )

    async def receive(self, text_data: str):
        """Process incoming telemetry, odds, and status from the local Desktop Runner."""
        try:
            payload = json.loads(text_data)
        except Exception:
            return

        msg_type = payload.get("type")
        from .service import bot_service

        if msg_type == "ping":
            await database_sync_to_async(bot_service.touch_runner_heartbeat)()
            await self.send(text_data=json.dumps({"type": "pong", "time": time.time()}))
            return

        if msg_type == "odds_extracted":
            multiplier = float(payload.get("multiplier", 1.0))
            await database_sync_to_async(bot_service.handle_remote_odds)(multiplier)
            return

        if msg_type == "round_result":
            msg = str(payload.get("message", ""))
            balance = payload.get("balance")
            stake = float(payload.get("current_stake", 50.0))
            loss_streak = int(payload.get("loss_streak", 0))
            await database_sync_to_async(bot_service.handle_remote_round_result)(
                msg, balance, stake, loss_streak
            )
            return

        if msg_type == "balance_updated":
            balance = float(payload.get("balance", 0.0))
            await database_sync_to_async(bot_service.handle_remote_balance)(balance)
            return

        if msg_type == "status_changed":
            status_text = str(payload.get("status", "IDLE"))
            is_running = bool(payload.get("is_running", False))
            is_staking = bool(payload.get("is_staking", False))
            await database_sync_to_async(bot_service.handle_remote_status)(
                status_text, is_running, is_staking
            )
            return

        if msg_type == "log":
            level = str(payload.get("level", "INFO"))
            message = str(payload.get("message", ""))
            await database_sync_to_async(bot_service.handle_remote_log)(level, message)
            return

    async def runner_command(self, event: dict[str, Any]):
        """Handler for commands sent to the 'runner_agents' group from the Web Dashboard."""
        command = event.get("command")
        params = event.get("params", {})
        await self.send(text_data=json.dumps({
            "type": "command",
            "action": command,
            "params": params,
            "timestamp": time.time(),
        }))
