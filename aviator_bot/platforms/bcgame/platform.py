from __future__ import annotations

from aviator_bot.platforms.base.platform_base import BasePlatform
from .games.crash import BCGameCrashGame
from .games.limbo import BCGameLimboGame


class BCGamePlatform(BasePlatform):
    """BC.Game crypto casino platform addon."""

    @property
    def platform_id(self) -> str:
        return "bcgame"

    @property
    def display_name(self) -> str:
        return "BC.Game"

    @property
    def default_url(self) -> str:
        return "https://bc.game/game/crash"

    @property
    def default_game_id(self) -> str:
        return "crash"

    def _register_supported_games(self) -> None:
        self.add_game(BCGameCrashGame())
        self.add_game(BCGameLimboGame())
