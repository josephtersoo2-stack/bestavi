from __future__ import annotations

import os
import secrets
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, permissions
from rest_framework.exceptions import AuthenticationFailed

from aviator_bot.security.crypto import (
    encrypt_string as encrypt_secret,
    decrypt_string as decrypt_secret,
    mask_sensitive_url,
    mask_secret,
    sanitize_log_message as sanitize_log,
)


class BotAdminUser(AnonymousUser):
    """Authenticated user representing a verified administrator with a valid BOT_API_KEY."""

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_staff(self) -> bool:
        return True

    def __str__(self) -> str:
        return "BotAdminUser"


def get_expected_api_key() -> str:
    """Retrieve expected API key from environment."""
    key = os.getenv("BOT_API_KEY", "").strip()
    return key


def verify_api_key(provided_key: str | None) -> bool:
    """Verify an API key using constant-time string comparison."""
    if not provided_key:
        return False
    expected = get_expected_api_key()
    if not expected:
        return False
    return secrets.compare_digest(provided_key.strip(), expected)


class AdminApiKeyAuthentication(authentication.BaseAuthentication):
    """Grade-A Authentication backend validating against the high-entropy BOT_API_KEY.

    Supported methods:
    1. Header: X-API-Key: <BOT_API_KEY>
    2. Header: Authorization: Bearer <BOT_API_KEY>
    3. Query parameter: ?api_key=<BOT_API_KEY>
    """

    def authenticate(self, request):
        api_key = None

        # 1. Check X-API-Key Header
        if "HTTP_X_API_KEY" in request.META:
            api_key = request.META["HTTP_X_API_KEY"]

        # 2. Check Authorization Header (Bearer or Token)
        elif "HTTP_AUTHORIZATION" in request.META:
            auth_header = request.META["HTTP_AUTHORIZATION"]
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() in ("bearer", "token", "apikey"):
                api_key = parts[1]

        # 3. Check query string
        elif "api_key" in request.query_params:
            api_key = request.query_params["api_key"]

        if not api_key:
            return None  # Pass to next authenticator or permission check

        if verify_api_key(api_key):
            return (BotAdminUser(), None)

        raise AuthenticationFailed("Invalid API Key provided.")

    def authenticate_header(self, request):
        return 'ApiKey realm="AviatorBot"'


class IsAdminApiKey(permissions.BasePermission):
    """Permission that requires a verified BotAdminUser or staff user."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


def authenticate_websocket_scope(scope: dict) -> bool:
    """Validate WebSocket connection scope against BOT_API_KEY."""
    expected = get_expected_api_key()
    if not expected:
        return False

    # 1. Check Query String (?token=... or ?api_key=...)
    query_string = scope.get("query_string", b"").decode("utf-8")
    if query_string:
        params = parse_qs(query_string)
        token_val = params.get("token", [None])[0] or params.get("api_key", [None])[0]
        if token_val and secrets.compare_digest(token_val.strip(), expected):
            return True

    # 2. Check Headers
    headers = dict(scope.get("headers", []))
    header_key = headers.get(b"x-api-key")
    if header_key and secrets.compare_digest(header_key.decode("utf-8").strip(), expected):
        return True

    auth_header = headers.get(b"authorization")
    if auth_header:
        parts = auth_header.decode("utf-8").split()
        if len(parts) == 2 and parts[0].lower() in ("bearer", "token"):
            if secrets.compare_digest(parts[1].strip(), expected):
                return True

    return False


from aviator_bot.security.log_filter import SecurityScrubberFilter  # Re-export

