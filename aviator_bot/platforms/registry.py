from __future__ import annotations

import logging
from typing import Any
from .base.platform_base import BasePlatform
from .base.game_base import BaseGameAddon

logger = logging.getLogger("aviator_bot.platforms.registry")


class PlatformRegistry:
    """Central singleton registry for platform addons and their game types."""
    _instance: PlatformRegistry | None = None

    def __init__(self) -> None:
        self._platforms: dict[str, BasePlatform] = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> PlatformRegistry:
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.auto_discover()
        return cls._instance

    def register_platform(self, platform: BasePlatform) -> None:
        """Register a platform addon into the registry."""
        key = platform.platform_id.lower().strip()
        self._platforms[key] = platform
        logger.info("Registered platform addon: %s (%s)", platform.display_name, key)

    def get_platform(self, platform_id: str | None = None) -> BasePlatform:
        """Retrieve a registered platform by id, falling back to 'ilotbet' if not found."""
        if not self._initialized:
            self.auto_discover()
        key = (platform_id or "ilotbet").lower().strip()
        if key in self._platforms:
            return self._platforms[key]
        # Fallback to ilotbet or first available
        if "ilotbet" in self._platforms:
            return self._platforms["ilotbet"]
        if self._platforms:
            return next(iter(self._platforms.values()))
        raise RuntimeError("No platform addons registered in PlatformRegistry")

    def get_game(self, platform_id: str | None = None, game_id: str | None = None) -> BaseGameAddon:
        """Convenience method to retrieve a game addon directly."""
        platform = self.get_platform(platform_id)
        return platform.get_game(game_id)

    def list_platforms(self) -> list[dict[str, Any]]:
        """Return platform metadata and supported games for API / UI consumption."""
        if not self._initialized:
            self.auto_discover()
        result = []
        for p in self._platforms.values():
            result.append({
                "id": p.platform_id,
                "name": p.display_name,
                "default_url": p.default_url,
                "default_game": p.default_game_id,
                "games": p.list_games(),
            })
        return result

    def auto_discover(self) -> None:
        """Discover and load built-in platforms."""
        if self._initialized:
            return
        self._initialized = True

        # 1. iLotBet Addon
        try:
            from .ilotbet.platform import ILotBetPlatform
            self.register_platform(ILotBetPlatform())
        except Exception as exc:
            logger.warning("Failed to load iLotBet platform addon: %s", exc)

        # 2. BC.Game Addon
        try:
            from .bcgame.platform import BCGamePlatform
            self.register_platform(BCGamePlatform())
        except Exception as exc:
            logger.warning("Failed to load BC.Game platform addon: %s", exc)

        # 3. SportyBet Addon
        try:
            from .sportybet.platform import SportyBetPlatform
            self.register_platform(SportyBetPlatform())
        except Exception as exc:
            logger.warning("Failed to load SportyBet platform addon: %s", exc)
