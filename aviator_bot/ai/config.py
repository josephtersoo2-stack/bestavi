from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AIConfig:
    """Runtime configuration for the AI Copilot and Advisor."""
    enabled: bool = True
    provider: str = "gemini"  # "gemini" or "openrouter"
    model_name: str = "gemini-2.0-flash"
    api_key: str = ""
    temperature: float = 0.2
    max_tokens: int = 1500
    risk_tolerance: str = "conservative"  # "conservative", "balanced", "aggressive"
    autonomous_mode: bool = False
