from __future__ import annotations

import logging
from typing import Any
import httpx

from aviator_bot.security.crypto import sanitize_log_message

logger = logging.getLogger("aviator_bot.ai.gemini")


class GeminiProvider:
    """Google Gemini AI Studio API provider with Grade-A Header Authentication."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def fetch_models(self, api_key: str) -> list[dict[str, str]]:
        """Fetch all available models directly from Google Gemini API via secure headers."""
        if not api_key:
            return []
        url = f"{self.BASE_URL}/models"
        headers = {
            "x-goog-api-key": api_key,
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code != 200:
                    clean_err = sanitize_log_message(resp.text)
                    logger.error("Gemini fetch_models failed (%d): %s", resp.status_code, clean_err)
                    return []
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        raw_name = m.get("name", "").replace("models/", "")
                        display = m.get("displayName") or raw_name
                        models.append({
                            "id": raw_name,
                            "name": display,
                            "description": m.get("description", ""),
                        })
                # Sort models so flash-latest, 2.5, and 1.5 are near top
                models.sort(
                    key=lambda x: (
                        "flash-latest" in x["id"],
                        "2.5" in x["id"],
                        "flash" in x["id"],
                        "pro" in x["id"]
                    ),
                    reverse=True
                )
                return models
        except Exception as exc:
            logger.error("Error fetching Gemini models: %s", sanitize_log_message(str(exc)))
            return []

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "gemini-flash-latest",
        api_key: str = "",
        temperature: float = 0.2,
    ) -> str:
        """Call Gemini generateContent endpoint with zero secrets in URL."""
        if not api_key:
            raise ValueError("Gemini API key is required")
        model_name = model.replace("models/", "")
        # Fallback if old deprecated gemini-2.0-flash is passed
        if model_name in ("gemini-2.0-flash", "gemini-2.0-flash-exp"):
            model_name = "gemini-flash-latest"

        url = f"{self.BASE_URL}/models/{model_name}:generateContent"
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                clean_err = sanitize_log_message(resp.text)
                raise RuntimeError(f"Gemini API error ({resp.status_code}): {clean_err}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned no candidates")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise RuntimeError("Gemini candidate content empty")
            return parts[0].get("text", "")

