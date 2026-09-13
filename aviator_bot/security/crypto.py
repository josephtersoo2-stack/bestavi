from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

# Ensure root .env is loaded
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT_DIR / ".env")

_FERNET_CIPHER = None


def _get_cipher():
    global _FERNET_CIPHER
    if _FERNET_CIPHER is not None:
        return _FERNET_CIPHER

    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    raw_key = os.getenv("SECURITY_ENCRYPTION_KEY", "").strip()
    if raw_key:
        try:
            # Validate if it's already a valid Fernet 32-byte urlsafe key
            _FERNET_CIPHER = Fernet(raw_key.encode("utf-8"))
            return _FERNET_CIPHER
        except Exception:
            pass

    # Fallback to PBKDF2 derivation from DJANGO_SECRET_KEY
    secret_seed = os.getenv("DJANGO_SECRET_KEY", "aviator-bot-zero-leak-fallback-seed").encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"aviator_bot_deterministic_salt_v1",
        iterations=100_000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(secret_seed))
    _FERNET_CIPHER = Fernet(derived_key)
    return _FERNET_CIPHER


def encrypt_string(plaintext: str) -> str:
    """Encrypt a plaintext string using AES-128-CBC + HMAC-SHA256 (Fernet).
    Prepends 'enc::' to identify encrypted values.
    """
    if not plaintext:
        return ""
    if plaintext.startswith("enc::"):
        return plaintext  # Already encrypted
    cipher = _get_cipher()
    encrypted_bytes = cipher.encrypt(plaintext.encode("utf-8"))
    return f"enc::{encrypted_bytes.decode('utf-8')}"


def decrypt_string(ciphertext: str) -> str:
    """Decrypt a ciphertext string if prefixed by 'enc::'.
    Returns unchanged if not encrypted.
    """
    if not ciphertext or not ciphertext.startswith("enc::"):
        return ciphertext
    cipher = _get_cipher()
    raw = ciphertext[5:].encode("utf-8")
    try:
        decrypted_bytes = cipher.decrypt(raw)
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # If decryption fails (e.g. corrupted or key changed), return empty or sanitized notice
        return ""


def mask_sensitive_url(url: str) -> str:
    """Mask sensitive query parameters (e.g. content=, token=, session=) in a URL."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        params = parse_qs(parsed.query, keep_blank_values=True)
        sensitive_keywords = {"content", "token", "session", "auth", "password", "key", "secret", "sig"}
        masked_params = {}
        for k, vals in params.items():
            k_lower = k.lower()
            if any(kw in k_lower for kw in sensitive_keywords):
                masked_params[k] = ["REDACTED"]
            else:
                # Check if the parameter value is a nested URL that might have its own query
                new_vals = []
                for v in vals:
                    if "://" in v and ("content=" in v.lower() or "token=" in v.lower()):
                        new_vals.append(mask_sensitive_url(v))
                    else:
                        new_vals.append(v)
                masked_params[k] = new_vals

        new_query = urlencode(masked_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url


def mask_secret(secret: str, show_last: int = 4) -> str:
    """Mask secret token showing only trailing characters."""
    if not secret:
        return ""
    s = secret.strip()
    if len(s) <= show_last:
        return "***"
    return f"{'*' * (len(s) - show_last)}{s[-show_last:]}"


def sanitize_log_message(message: str) -> str:
    """Scrub sensitive credentials, tokens, session parameters, and API keys from log strings."""
    if not message:
        return ""
    msg = str(message)
    # 1. Mask Telegram Bot Tokens: bot123456:ABC-DEF...
    msg = re.sub(r"(bot\d+:)[A-Za-z0-9_-]+", r"\1[REDACTED]", msg)
    # 2. Mask OpenRouter API Keys: sk-or-v1-...
    msg = re.sub(r"sk-or-v1-[A-Za-z0-9_-]{16,}", r"sk-or-v1-[REDACTED]", msg)
    # 3. Mask Google Gemini AI Keys: AQ.... or AIzaSy...
    msg = re.sub(r"AQ\.[A-Za-z0-9_-]{25,}", r"AQ.[REDACTED]", msg)
    msg = re.sub(r"AIzaSy[A-Za-z0-9_-]{30,}", r"AIzaSy[REDACTED]", msg)
    # 4. Mask OpenAI / DeepSeek / generic Bearer API Keys: sk-...
    msg = re.sub(r"sk-[A-Za-z0-9_-]{24,}", r"sk-[REDACTED]", msg)
    # 5. Mask Fernet Ciphertext Tokens: enc::gAAAA... or gAAAA...
    msg = re.sub(r"enc::gAAAA[A-Za-z0-9_=-]{30,}", r"enc::[REDACTED]", msg)
    msg = re.sub(r"gAAAA[A-Za-z0-9_=-]{30,}", r"gAAAA[REDACTED]", msg)
    # 6. Mask sensitive query parameters: content=..., token=..., session=...
    msg = re.sub(
        r"(\b(?:content|token|session|auth|password|key|secret)=)[^&\s\"'>]+",
        r"\1[REDACTED]",
        msg,
        flags=re.IGNORECASE,
    )
    # 7. Mask Authorization headers in strings
    msg = re.sub(
        r"(Bearer\s+)[A-Za-z0-9_.-]{12,}",
        r"\1[REDACTED]",
        msg,
        flags=re.IGNORECASE,
    )
    # 8. Mask generic API key label assignments
    msg = re.sub(
        r"((?:x-goog-)?api[-_]?key[\s:=\"']+)[A-Za-z0-9_.-]{12,}",
        r"\1[REDACTED]",
        msg,
        flags=re.IGNORECASE,
    )
    # 9. Mask database passwords in connection strings
    msg = re.sub(
        r"(postgres(?:ql)?://[^:]+:)[^@]+(@)",
        r"\1[REDACTED]\2",
        msg,
        flags=re.IGNORECASE,
    )
    return msg

