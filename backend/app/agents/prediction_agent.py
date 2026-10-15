from __future__ import annotations

from app.agents.base import Agent, AgentContext
from app.services.ml_module_service import predict_and_store


class PredictionAgent(Agent):
    name = "prediction"

    def run(self, context: AgentContext) -> dict:
        prediction = predict_and_store(
            db=context.db,
            module=context.module,
            features=context.state["features"],
            region=context.region,
            model_run_id=context.model_run_id,
        )
        context.state["prediction"] = prediction
        return {
            "prediction_id": prediction.id,
            "model_run_id": prediction.model_run_id,
            "predicted_risk": prediction.predicted_risk,
        }
