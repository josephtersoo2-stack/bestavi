from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any, Callable
from urllib.parse import urlparse

import websockets

logger = logging.getLogger("desktop_agent.runner")


class DesktopRunnerClient:
    """Persistent WebSocket client running on the user's local PC.
    
    Connects to the Cloud Web Platform and relays commands to the local Playwright browser
    while streaming live table telemetry back to the cloud.
    """

    def __init__(
        self,
        server_url: str,
        api_key: str,
        on_log: Callable[[str], None] | None = None,
        on_status_change: Callable[[str, bool], None] | None = None,
    ) -> None:
        self.server_url = server_url.strip().rstrip("/")
        self.api_key = api_key.strip()
        self.on_log = on_log or (lambda msg: None)
        self.on_status_change = on_status_change or (lambda status, connected: None)

        self._running = False
        self._connected = False
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

        # Local Browser Controller instance
        self.controller: Any = None
        self.last_status: str = "IDLE"

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        """Start runner in a dedicated background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="DesktopRunnerThread")
        self._thread.start()

    def stop(self) -> None:
        """Gracefully stop runner and close browser."""
        self._running = False
        self._connected = False
        if self._loop and self._ws:
            asyncio.run_coroutine_threadsafe(self._close_ws(), self._loop)
        if self.controller:
            try:
                self.controller.stop()
            except Exception:
                pass
            self.controller = None
        self.on_status_change("DISCONNECTED", False)
        self.on_log("[Agent] Desktop Runner stopped.")

    async def _close_ws(self) -> None:
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass

    def _get_ws_url(self) -> str:
        parsed = urlparse(self.server_url)
        scheme = "wss" if parsed.scheme in ("https", "wss") else "ws"
        netloc = parsed.netloc or parsed.path
        return f"{scheme}://{netloc}/ws/runner/?api_key={self.api_key}"

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connection_supervisor())

    async def _connection_supervisor(self) -> None:
        backoff = 2
        while self._running:
            ws_url = self._get_ws_url()
            self.on_log(f"[Network] Connecting to Cloud Relay: {self.server_url}...")
            self.on_status_change("CONNECTING", False)

            try:
                # Add headers and timeout for reliable connection
                headers = {"X-API-Key": self.api_key}
                async with websockets.connect(
                    ws_url,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=15,
                    close_timeout=5,
                ) as ws:
                    self._ws = ws
                    self._connected = True
                    backoff = 2
                    self.on_log("[Network] Successfully connected to Cloud Web Platform! (Residential IP Active)")
                    self.on_status_change("CONNECTED", True)

                    # Spawn heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_worker(ws))

                    # Process incoming commands from Cloud
                    try:
                        async for raw_message in ws:
                            await self._handle_cloud_message(raw_message)
                    except websockets.ConnectionClosed as cc:
                        self.on_log(f"[Network] Connection closed by server (code: {cc.code}).")
                    finally:
                        heartbeat_task.cancel()
                        self._connected = False
                        self._ws = None

            except Exception as exc:
                self._connected = False
                self._ws = None
                self.on_status_change("OFFLINE", False)
                self.on_log(f"[Network] Connection error: {exc}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 20)

    async def _heartbeat_worker(self, ws: websockets.WebSocketClientProtocol) -> None:
        while self._running and self._connected:
            try:
                await asyncio.sleep(15)
                await ws.send(json.dumps({"type": "ping", "time": time.time()}))
            except Exception:
                break

    async def send_telemetry(self, payload: dict[str, Any]) -> None:
        if self._ws and self._connected:
            try:
                await self._ws.send(json.dumps(payload))
            except Exception as exc:
                logger.debug("Failed to send telemetry: %s", exc)

    def send_telemetry_sync(self, payload: dict[str, Any]) -> None:
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.send_telemetry(payload), self._loop)

    async def _handle_cloud_message(self, raw_message: str) -> None:
        try:
            data = json.loads(raw_message)
        except Exception:
            return

        msg_type = data.get("type")
        if msg_type == "runner_connected":
            self.on_log(f"[Cloud Handshake] {data.get('message', 'Ready')}")
            return

        if msg_type == "pong":
            return

        if msg_type == "command":
            action = data.get("action")
            params = data.get("params", {})
            self.on_log(f"[Remote Command Received] Action: {action.upper()}")
            await self._execute_remote_command(action, params)

    async def _execute_remote_command(self, action: str, params: dict[str, Any]) -> None:
        if action == "prepare":
            self._execute_prepare(params)
        elif action == "start":
            self._execute_start()
        elif action == "pause":
            self._execute_pause()
        elif action == "stop":
            self._execute_stop()

    def _execute_prepare(self, params: dict[str, Any]) -> None:
        self.on_log("[Browser] Launching Visible Google Chrome / Chromium on your desktop...")
        try:
            from dataclasses import replace
            from pathlib import Path
            from aviator_bot.config.site_profiles import profile
            from aviator_bot.config.settings import BotSettings, BrowserSelectors, load_settings
            from aviator_bot.browser.controller import PlaywrightAdapter, DryRunAdapter
            from aviator_bot.bot.controller import BotController

            platform_key = (params.get("platform") or "ilotbet").lower().strip()
            game_key = (params.get("game") or "best_aviator").lower().strip()
            game_url = params.get("game_url") or "https://www.ilotbet.com"
            dry_run = bool(params.get("dry_run", False))

            data_dir = Path("data").resolve()
            user_data_path = str(data_dir / f"browser_profile_{platform_key}")

            base_browser = BrowserSelectors(
                url=game_url,
                headless=False,
                user_data_dir=user_data_path,
            )
            browser_selectors = replace(profile(platform_key, base=base_browser), user_data_dir=user_data_path, headless=False)

            settings = BotSettings(
                base_stake=float(params.get("base_stake", 50.0)),
                auto_cashout=float(params.get("auto_cashout", 1.50)),
                multiplier=float(params.get("auto_cashout", 1.50)),
                strategy=params.get("strategy", "martingale"),
                site=platform_key,
                dry_run=dry_run,
                browser=browser_selectors,
            )

            if self.controller and self.controller.running:
                self.controller.update_settings(settings)
                self.last_status = "Prepared (Running)"
                self.send_telemetry_sync({"type": "status_changed", "status": self.last_status, "is_running": True, "is_staking": False})
                self.on_log("[Browser] Updated settings on existing browser session.")
                return

            if self.controller:
                try:
                    self.controller.stop()
                except Exception:
                    pass
                self.controller = None

            adapter = DryRunAdapter() if dry_run else PlaywrightAdapter(
                settings.browser,
                platform_id=platform_key,
                game_id=game_key,
            )

            self.controller = BotController(
                settings=settings,
                adapter=adapter,
                on_event=self._on_local_browser_event,
            )
            self.controller.start(authorized=False)
            self.last_status = "Preparing Game Controls..."
            self.send_telemetry_sync({"type": "status_changed", "status": self.last_status, "is_running": True, "is_staking": False})
            self.on_log("[Browser] Visible Chrome opened. Live Odds Extractor started.")

        except Exception as exc:
            self.on_log(f"[Browser Error] Failed to launch browser: {exc}")
            self.send_telemetry_sync({"type": "log", "level": "ERROR", "message": f"Browser launch failed: {exc}"})

    def _execute_start(self) -> None:
        if not self.controller or not self.controller.running:
            self.on_log("[Browser] Controller not prepared. Preparing first...")
            self._execute_prepare({})
        if self.controller:
            self.controller.authorize()
            self.last_status = "Live Auto-Staking Active"
            self.send_telemetry_sync({"type": "status_changed", "status": self.last_status, "is_running": True, "is_staking": True})
            self.on_log("[Staking] Live Staking Authorized & Active!")

    def _execute_pause(self) -> None:
        if self.controller and self.controller.running:
            self.controller.pause_staking()
            self.last_status = "Staking Paused (Observation Active)"
            self.send_telemetry_sync({"type": "status_changed", "status": self.last_status, "is_running": True, "is_staking": False})
            self.on_log("[Staking] Live Staking Paused (Result observation continues).")

    def _execute_stop(self) -> None:
        if self.controller:
            self.controller.stop()
            self.controller = None
        self.last_status = "STOPPED"
        self.send_telemetry_sync({"type": "status_changed", "status": self.last_status, "is_running": False, "is_staking": False})
        self.on_log("[Browser] Emergency Stop executed. Browser closed.")

    def _on_local_browser_event(self, event: str | tuple) -> None:
        """Callback from BrowserBotController when odds, balance, or rounds change."""
        msg = str(event[1]) if isinstance(event, tuple) else str(event)
        self.on_log(f"[Game Event] {msg}")

        # 1. Extracted multiplier
        if msg.startswith("extracted_result: "):
            try:
                val = float(msg.replace("extracted_result: ", ""))
                self.send_telemetry_sync({
                    "type": "odds_extracted",
                    "multiplier": val,
                })
            except Exception:
                pass
            return

        # 2. Result of bet round
        if msg.startswith("Result "):
            bal = self.controller.risk.balance if (self.controller and getattr(self.controller, "risk", None)) else None
            stake = getattr(self.controller, "current_stake", 50.0) if self.controller else 50.0
            loss_streak = getattr(self.controller.risk, "loss_streak", 0) if (self.controller and getattr(self.controller, "risk", None)) else 0
            self.send_telemetry_sync({
                "type": "round_result",
                "message": msg,
                "balance": bal,
                "current_stake": stake,
                "loss_streak": loss_streak,
            })
            return

        # 3. Balance updated
        if msg.startswith("balance_updated: "):
            try:
                bal = float(msg.replace("balance_updated: ", ""))
                self.send_telemetry_sync({
                    "type": "balance_updated",
                    "balance": bal,
                })
            except Exception:
                pass
            return

        # 4. Status change
        if msg.startswith("Status: "):
            st = msg.replace("Status: ", "")
            self.last_status = st
            is_run = bool(self.controller and self.controller.running)
            is_stake = bool(self.controller and self.controller.is_authorized)
            self.send_telemetry_sync({
                "type": "status_changed",
                "status": st,
                "is_running": is_run,
                "is_staking": is_stake,
            })
            return

        # Forward generic logs
        self.send_telemetry_sync({
            "type": "log",
            "level": "INFO",
            "message": msg,
        })
