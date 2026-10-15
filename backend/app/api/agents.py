from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_risk_pipeline
from app.database import get_db
from app.db_models import AgentRun
from app.models import AgentPipelineRunRequest, AgentPipelineRunResponse, AgentStepItem

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def _to_response(row: AgentRun) -> AgentPipelineRunResponse:
    return AgentPipelineRunResponse(
        agent_run_id=row.id,
        module=row.module,
        region=row.region,
        status=row.status,
        steps=[AgentStepItem(**step) for step in row.steps],
        final_output=row.final_output or {},
        created_at=row.created_at,
    )


@router.post("/pipeline/run", response_model=AgentPipelineRunResponse)
def run_pipeline(payload: AgentPipelineRunRequest, db: Session = Depends(get_db)) -> AgentPipelineRunResponse:
    try:
        agent_run = run_risk_pipeline(
            db=db,
            module=payload.module,
            region=payload.region,
            features=payload.features,
            model_run_id=payload.model_run_id,
            interventions=payload.interventions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _to_response(agent_run)


@router.get("/pipeline/runs", response_model=list[AgentPipelineRunResponse])
def list_pipeline_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[AgentPipelineRunResponse]:
    rows = db.query(AgentRun).order_by(desc(AgentRun.created_at)).limit(limit).all()
    return [_to_response(row) for row in rows]
