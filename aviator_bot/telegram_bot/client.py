from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


import ssl


def _get_ssl_context(verify: bool = True) -> ssl.SSLContext:
    if verify:
        try:
            return ssl.create_default_context()
        except Exception:
            pass
    return ssl._create_unverified_context()


class TelegramClient:
    """Lightweight, zero-dependency Telegram Bot API client."""

    def __init__(self, token: str) -> None:
        self.token = token.strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def __repr__(self) -> str:
        from aviator_bot.security.crypto import mask_secret
        return f"<TelegramClient token={mask_secret(self.token)}>"

    def is_configured(self) -> bool:
        return bool(self.token)

    def get_me(self) -> dict[str, Any] | None:
        return self._request("getMe")

    def get_updates(self, offset: int = 0, timeout: int = 15) -> list[dict[str, Any]]:
        params = {"offset": offset, "timeout": timeout}
        res = self._request("getUpdates", data=params)
        if res and res.get("ok"):
            return res.get("result", [])
        return []

    def send_message(self, chat_id: str | int, text: str, reply_markup: dict[str, Any] | None = None,
                     parse_mode: str = "HTML") -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._request("sendMessage", data=payload)

    def send_document(self, chat_id: str | int, file_path: str | Path, caption: str = "") -> dict[str, Any] | None:
        path = Path(file_path)
        if not path.exists():
            return None

        boundary = "----WebKitFormBoundary" + os.urandom(16).hex()
        body = bytearray()

        # chat_id part
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode("utf-8"))

        # caption part
        if caption:
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode("utf-8"))

        # document file part
        filename = path.name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        file_bytes = path.read_bytes()

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_bytes)
        body.extend(b"\r\n")

        # closing boundary
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(
            f"{self.base_url}/sendDocument",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        for verify in (True, False):
            try:
                ctx = _get_ssl_context(verify=verify)
                with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                if not verify:
                    return None
        return None

    def _request(self, method: str, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if not self.token:
            return None
        url = f"{self.base_url}/{method}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers)
        for verify in (True, False):
            try:
                ctx = _get_ssl_context(verify=verify)
                with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                if not verify:
                    return None
        return None
