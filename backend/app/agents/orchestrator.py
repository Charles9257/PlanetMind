from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.agents.base import AgentContext
from app.agents.explainability_agent import ExplainabilityAgent
from app.agents.ingestion_agent import IngestionAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.reporting_agent import ReportingAgent
from app.agents.simulation_agent import SimulationAgent
from app.db_models import AgentRun
from app.models import Intervention

PIPELINE = [IngestionAgent(), PredictionAgent(), ExplainabilityAgent(), SimulationAgent(), ReportingAgent()]


def run_risk_pipeline(
    db: Session,
    module: str,
    region: str | None,
    features: dict[str, float],
    model_run_id: int | None = None,
    interventions: list[Intervention] | None = None,
) -> AgentRun:
    context = AgentContext(
        db=db,
        module=module,
        region=region,
        features=features,
        model_run_id=model_run_id,
        interventions=[item.model_dump() for item in (interventions or [])],
    )

    steps: list[dict] = []
    for agent in PIPELINE:
        started = time.perf_counter()
        try:
            output = agent.run(context)
        except ValueError as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            steps.append(
                {"name": agent.name, "status": "error", "duration_ms": duration_ms, "output": {"error": str(exc)}}
            )
            run = AgentRun(
                module=module,
                region=region,
                status="error",
                input_payload={"features": features, "model_run_id": model_run_id},
                steps=steps,
                final_output=None,
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            raise ValueError(f"Agent pipeline failed at step '{agent.name}': {exc}") from exc

        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        steps.append({"name": agent.name, "status": "ok", "duration_ms": duration_ms, "output": output})

    run = AgentRun(
        module=module,
        region=region,
        status="ok",
        input_payload={"features": features, "model_run_id": model_run_id},
        steps=steps,
        final_output=context.state.get("report"),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
