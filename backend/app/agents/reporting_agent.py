from __future__ import annotations

from app.agents.base import Agent, AgentContext


class ReportingAgent(Agent):
    name = "reporting"

    def run(self, context: AgentContext) -> dict:
        prediction = context.state["prediction"]
        explanation = context.state.get("explanation", {})
        simulation = context.state.get("simulation")
        contributions = explanation.get("contributions", {})
        top_feature = max(contributions, key=lambda k: abs(contributions[k])) if contributions else None

        summary_parts = [
            f"{context.module.capitalize()} risk for {context.region or 'the selected area'} "
            f"is {prediction.predicted_risk:.2f}."
        ]
        if top_feature:
            summary_parts.append(f"Strongest contributing factor: '{top_feature}'.")
        if simulation:
            summary_parts.append(
                f"Simulated interventions would reduce risk to {simulation['projected_score']:.2f} "
                f"(delta={simulation['net_reduction']:.2f})."
            )

        report = {
            "prediction_id": prediction.id,
            "predicted_risk": prediction.predicted_risk,
            "top_feature": top_feature,
            "simulation": simulation,
            "summary": " ".join(summary_parts),
        }
        context.state["report"] = report
        return report
