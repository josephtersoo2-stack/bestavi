from __future__ import annotations

from aviator_bot.platforms.base.platform_base import BasePlatform
from .games.aviator import ILotBetAviatorGame


class ILotBetPlatform(BasePlatform):
    """iLotBet Nigeria platform addon."""

    @property
    def platform_id(self) -> str:
        return "ilotbet"

    @property
    def display_name(self) -> str:
        return "iLOTBET"

    @property
    def default_url(self) -> str:
        return "https://www.ilotbet.com/pc/iframe"

    @property
    def default_game_id(self) -> str:
        return "best_aviator"

    def _register_supported_games(self) -> None:
        self.add_game(ILotBetAviatorGame())
