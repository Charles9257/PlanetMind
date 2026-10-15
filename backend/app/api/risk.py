from fastapi import APIRouter

from app.models import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.services.risk_engine import build_explanation, score_risk, simulate_interventions

router = APIRouter(prefix="/api/v1/risk", tags=["risk-sandbox"])


@router.post("/predict", response_model=RiskPredictionResponse)
def predict_risk(payload: RiskPredictionRequest) -> RiskPredictionResponse:
    score, contributors = score_risk(payload.domain, payload.signals)
    severity = (
        "critical" if score >= 0.8 else "high" if score >= 0.6 else "medium" if score >= 0.4 else "low"
    )

    return RiskPredictionResponse(
        domain=payload.domain,
        region=payload.region,
        score=score,
        severity=severity,
        explanation=build_explanation(payload.domain, score, contributors),
        top_contributors=contributors,
    )


@router.post("/simulate", response_model=SimulationResponse)
def simulate(payload: SimulationRequest) -> SimulationResponse:
    projected_score, net_reduction = simulate_interventions(payload.baseline_score, payload.interventions)
    return SimulationResponse(
        baseline_score=payload.baseline_score,
        projected_score=projected_score,
        net_reduction=net_reduction,
        summary=(
            f"Interventions reduce risk from {payload.baseline_score:.2f} "
            f"to {projected_score:.2f} (delta={net_reduction:.2f})."
        ),
    )
