from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FederatedTrainResponse
from app.services.federated_learning import list_federated_runs, train_federated


def _to_response(run) -> FederatedTrainResponse:
    return FederatedTrainResponse(
        federated_run_id=run.id,
        module=run.module,
        num_clients=run.num_clients,
        rounds=run.rounds,
        target_column=run.target_column,
        feature_columns=run.feature_columns,
        client_sample_counts=run.client_sample_counts,
        federated_metrics=run.federated_metrics,
        centralized_metrics=run.centralized_metrics,
        created_at=run.created_at,
    )


def build_federated_router(module: str) -> APIRouter:
    router = APIRouter(prefix=f"/api/v1/{module}/federated", tags=[f"{module}-federated"])

    @router.post("/train", response_model=FederatedTrainResponse)
    async def train_federated_model(
        dataset: UploadFile = File(...),
        target_column: str = Form(default="risk_score"),
        num_clients: int = Form(default=3),
        rounds: int = Form(default=10),
        db: Session = Depends(get_db),
    ) -> FederatedTrainResponse:
        if not dataset.filename or not dataset.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Dataset must be a CSV file")

        file_bytes = await dataset.read()
        try:
            result = train_federated(
                db=db,
                module=module,
                dataset_bytes=file_bytes,
                target_column=target_column,
                num_clients=num_clients,
                rounds=rounds,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return _to_response(result.run)

    @router.get("/runs", response_model=list[FederatedTrainResponse])
    def get_federated_runs(
        limit: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(get_db),
    ) -> list[FederatedTrainResponse]:
        rows = list_federated_runs(db, module=module, limit=limit)
        return [_to_response(row) for row in rows]

    return router


climate_federated_router = build_federated_router("climate")
pandemic_federated_router = build_federated_router("pandemic")
