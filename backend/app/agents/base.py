from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session


@dataclass
class AgentContext:
    db: Session
    module: str
    region: str | None
    features: dict[str, float]
    model_run_id: int | None
    interventions: list[dict]
    state: dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    name: str

    @abstractmethod
    def run(self, context: AgentContext) -> dict[str, Any]:
        """Execute this agent's step, mutate context.state as needed, and return a
        JSON-serializable summary of what it did (persisted into the execution trace)."""
