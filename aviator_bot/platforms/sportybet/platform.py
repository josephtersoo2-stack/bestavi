from __future__ import annotations

from aviator_bot.platforms.base.platform_base import BasePlatform
from .games.aviator import SportyBetAviatorGame


class SportyBetPlatform(BasePlatform):
    """SportyBet Nigeria platform addon."""

    @property
    def platform_id(self) -> str:
        return "sportybet"

    @property
    def display_name(self) -> str:
        return "SportyBet"

    @property
    def default_url(self) -> str:
        return "https://www.sportybet.com/ng/games/aviator"

    @property
    def default_game_id(self) -> str:
        return "aviator"

    def _register_supported_games(self) -> None:
        self.add_game(SportyBetAviatorGame())
