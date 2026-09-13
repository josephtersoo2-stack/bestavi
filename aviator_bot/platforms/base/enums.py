from __future__ import annotations

from enum import Enum


class GameCategory(str, Enum):
    CRASH = "CRASH"
    LIMBO = "LIMBO"
    DICE = "DICE"
    MINES = "MINES"
    ROULETTE = "ROULETTE"
    WHEEL = "WHEEL"


class RoundPhase(str, Enum):
    IDLE = "IDLE"
    BETTING = "BETTING"
    RUNNING = "RUNNING"
    CRASHED = "CRASHED"
    SETTLED = "SETTLED"


class PlatformStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DEPRECATED = "DEPRECATED"
