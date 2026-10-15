from __future__ import annotations

from app.agents.base import Agent, AgentContext


class ExplainabilityAgent(Agent):
    name = "explainability"

    def run(self, context: AgentContext) -> dict:
        prediction = context.state["prediction"]
        explanation = prediction.explanation or {"base_value": 0.0, "contributions": {}}
        context.state["explanation"] = explanation

        contributions = explanation.get("contributions", {})
        top_feature = max(contributions, key=lambda k: abs(contributions[k])) if contributions else None

        return {
            "base_value": explanation.get("base_value", 0.0),
            "top_feature": top_feature,
            "contributions": contributions,
        }
