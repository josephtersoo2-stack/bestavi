from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any
from ..config import AIConfig


@dataclass
class AgentEvaluation:
    agent_id: str
    name: str
    role: str
    directive: str  # "BET", "CAUTION", "PAUSE_STAKING", "RESUME_STAKING"
    confidence: float  # 0.0 to 100.0
    sentiment: str  # "BULLISH", "NEUTRAL", "BEARISH", "CRITICAL"
    reasoning: str
    metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseAgent(ABC):
    """Abstract base class for all specialized swarm agents."""

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique key for this agent, e.g. 'analyst', 'risk_guardian'."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name, e.g. 'Market Pattern Analyst'."""
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        """Role description, e.g. 'Pattern & Streak Detective'."""
        pass

    @abstractmethod
    def evaluate(
        self,
        telemetry: dict[str, Any],
        config: AIConfig | None = None,
    ) -> AgentEvaluation:
        """Perform autonomous evaluation using live game telemetry and bankroll stats."""
        pass
