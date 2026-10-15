from __future__ import annotations

from app.agents.base import Agent, AgentContext
from app.models import Intervention
from app.services.risk_engine import simulate_interventions


class SimulationAgent(Agent):
    name = "simulation"

    def run(self, context: AgentContext) -> dict:
        if not context.interventions:
            context.state["simulation"] = None
            return {"skipped": True, "reason": "no interventions provided"}

        prediction = context.state["prediction"]
        interventions = [Intervention(**item) for item in context.interventions]
        projected_score, net_reduction = simulate_interventions(prediction.predicted_risk, interventions)
        simulation = {
            "baseline_score": prediction.predicted_risk,
            "projected_score": projected_score,
            "net_reduction": net_reduction,
        }
        context.state["simulation"] = simulation
        return simulation
