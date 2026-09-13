from __future__ import annotations

from typing import Protocol, Any


class LLMProviderProtocol(Protocol):
    """Protocol for AI LLM providers."""

    def fetch_models(self, api_key: str) -> list[dict[str, str]]:
        """Fetch available models dynamically from the provider."""
        ...

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "",
        api_key: str = "",
        temperature: float = 0.2,
    ) -> str:
        """Generate text completion from the provider."""
        ...
