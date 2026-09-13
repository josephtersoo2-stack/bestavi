from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type
from .game_base import BaseGameAddon


class BasePlatform(ABC):
    """Abstract interface representing a betting / casino platform addon."""

    def __init__(self) -> None:
        self._games: dict[str, BaseGameAddon] = {}
        self._register_supported_games()

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Unique key for this platform, e.g. 'ilotbet', 'bcgame', 'sportybet'."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human readable title, e.g. 'iLOTBET', 'BC.Game', 'SportyBet'."""
        pass

    @property
    @abstractmethod
    def default_url(self) -> str:
        """Base website or default game entry URL."""
        pass

    @property
    @abstractmethod
    def default_game_id(self) -> str:
        """Default active game for this platform, e.g. 'aviator' or 'crash'."""
        pass

    @abstractmethod
    def _register_supported_games(self) -> None:
        """Populate self._games with supported game addon instances."""
        pass

    def add_game(self, game: BaseGameAddon) -> None:
        """Register a game under this platform, including aliases."""
        self._games[game.game_id.lower()] = game
        for alias in getattr(game, "aliases", ()):
            self._games[alias.lower()] = game

    def get_game(self, game_id: str | None = None) -> BaseGameAddon:
        """Retrieve game addon by id, falling back to default game if None or missing."""
        key = (game_id or self.default_game_id).lower()
        if key not in self._games:
            # Fallback to first registered game or default
            if self.default_game_id.lower() in self._games:
                return self._games[self.default_game_id.lower()]
            if self._games:
                return next(iter(self._games.values()))
            raise KeyError(f"No games registered for platform '{self.platform_id}'")
        return self._games[key]

    def list_games(self) -> list[dict[str, Any]]:
        """Return list of supported unique games for UI and API selection."""
        seen = set()
        unique_games = []
        for g in self._games.values():
            if g.game_id not in seen:
                seen.add(g.game_id)
                unique_games.append(g)

        return [
            {
                "id": g.game_id,
                "name": g.display_name,
                "category": g.category.value,
                "aliases": list(getattr(g, "aliases", ())),
            }
            for g in unique_games
        ]
