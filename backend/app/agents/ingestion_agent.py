from __future__ import annotations

from app.agents.base import Agent, AgentContext


class IngestionAgent(Agent):
    name = "ingestion"

    def run(self, context: AgentContext) -> dict:
        cleaned: dict[str, float] = {}
        for key, value in context.features.items():
            try:
                cleaned[key] = float(value)
            except (TypeError, ValueError):
                cleaned[key] = 0.0
        context.state["features"] = cleaned
        return {"feature_count": len(cleaned), "features": cleaned}
