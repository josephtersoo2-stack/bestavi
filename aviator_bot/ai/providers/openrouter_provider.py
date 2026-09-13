from __future__ import annotations

import logging
from typing import Any
import httpx

logger = logging.getLogger("aviator_bot.ai.openrouter")


class OpenRouterProvider:
    """OpenRouter.ai API provider (OpenAI-compatible)."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def fetch_models(self, api_key: str) -> list[dict[str, str]]:
        """Fetch all models dynamically from OpenRouter."""
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{self.BASE_URL}/models", headers=headers)
                if resp.status_code != 200:
                    logger.error("OpenRouter fetch_models failed (%d): %s", resp.status_code, resp.text)
                    return []
                data = resp.json()
                raw_models = data.get("data", [])
                models = []
                for m in raw_models:
                    model_id = m.get("id", "")
                    name = m.get("name") or model_id
                    desc = m.get("description", "")
                    models.append({
                        "id": model_id,
                        "name": name,
                        "description": desc[:150] if desc else "",
                    })
                # Sort popular models to top
                popular_keywords = ["deepseek", "gpt-4o", "claude-3", "llama-3", "gemini"]
                models.sort(
                    key=lambda x: any(k in x["id"].lower() for k in popular_keywords),
                    reverse=True
                )
                return models
        except Exception as exc:
            logger.error("Error fetching OpenRouter models: %s", exc)
            return []

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "deepseek/deepseek-chat",
        api_key: str = "",
        temperature: float = 0.2,
    ) -> str:
        """Call OpenRouter chat completions endpoint."""
        if not api_key:
            raise ValueError("OpenRouter API key is required")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://aviator-autostake.local",
            "X-Title": "Aviator Auto Stake Bot",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }

        with httpx.Client(timeout=45.0) as client:
            resp = client.post(f"{self.BASE_URL}/chat/completions", json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenRouter API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"OpenRouter returned no choices: {data}")
            return choices[0].get("message", {}).get("content", "")
