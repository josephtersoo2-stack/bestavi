import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .security import authenticate_websocket_scope


class BotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Grade-A WebSocket Security: Authenticate incoming connection
        if not authenticate_websocket_scope(self.scope):
            # Unauthorized handshake: reject immediately with code 4003 (Forbidden)
            await self.close(code=4003)
            return

        self.room_group_name = "bot_updates"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connected",
            "message": "Connected to Aviator Bot WebSocket Stream"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")
            # Handle any incoming client ping or action if needed
            if action == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except Exception:
            pass

    async def bot_event(self, event):
        await self.send(text_data=json.dumps({
            "type": event.get("event_type", "event"),
            "data": event.get("data", {})
        }))
