from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    ExplanationPayload,
    ModuleModelRunItem,
    ModulePredictRequest,
    ModulePredictResponse,
    ModulePredictionHistoryItem,
    ModuleTrainResponse,
)
from app.services.governance_client import (
    GovernanceApprovalError,
    ensure_model_promotion_is_approved,
    sync_model_run_registration,
)
from app.services.ml_module_service import (
    list_model_runs,
    list_recent_predictions,
    predict_and_store,
    promote_model_run,
    train_from_dataset,
)


def build_module_router(module: str, model_name: str) -> APIRouter:
    router = APIRouter(prefix=f"/api/v1/{module}", tags=[module])

    @router.post("/train", response_model=ModuleTrainResponse)
    async def train_module_model(
        dataset: UploadFile = File(...),
        target_column: str = Form(default="risk_score"),
        db: Session = Depends(get_db),
    ) -> ModuleTrainResponse:
        if not dataset.filename or not dataset.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Dataset must be a CSV file")

        file_bytes = await dataset.read()
        try:
            result = train_from_dataset(
                db=db, module=module, dataset_bytes=file_bytes, target_column=target_column
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        governance_result = sync_model_run_registration(
            model_run_id=result.model_run.id,
            model_version=result.model_run.model_version,
            is_active=result.model_run.is_active,
            module=module,
            model_name=model_name,
        )

        return ModuleTrainResponse(
            module=module,
            model_run_id=result.model_run.id,
            model_version=result.model_run.model_version,
            is_active=result.model_run.is_active,
            target_column=result.model_run.target_column,
            feature_columns=result.feature_columns,
            rows_trained=result.model_run.rows_trained,
            metrics=result.metrics,
            governance_synced=bool(governance_result.get("governance_synced", False)),
            governance_status=governance_result.get("governance_status"),
            governance_error=governance_result.get("governance_error"),
        )

    @router.post("/predict", response_model=ModulePredictResponse)
    def predict_module(payload: ModulePredictRequest, db: Session = Depends(get_db)) -> ModulePredictResponse:
        try:
            prediction = predict_and_store(
                db=db,
                module=module,
                features=payload.features,
                region=payload.region,
                model_run_id=payload.model_run_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return ModulePredictResponse(
            module=module,
            prediction_id=prediction.id,
            model_run_id=prediction.model_run_id,
            model_version=prediction.model_run.model_version,
            region=prediction.region,
            predicted_risk=prediction.predicted_risk,
            explanation=ExplanationPayload(**prediction.explanation),
            created_at=prediction.created_at,
        )

    @router.get("/models", response_model=list[ModuleModelRunItem])
    def get_module_models(
        limit: int = Query(default=50, ge=1, le=300),
        db: Session = Depends(get_db),
    ) -> list[ModuleModelRunItem]:
        rows = list_model_runs(db, module=module, limit=limit)
        return [
            ModuleModelRunItem(
                module=module,
                model_run_id=row.id,
                model_version=row.model_version,
                is_active=row.is_active,
                created_at=row.created_at,
                promoted_at=row.promoted_at,
                target_column=row.target_column,
                feature_columns=row.feature_columns,
                rows_trained=row.rows_trained,
                metrics=row.metrics,
            )
            for row in rows
        ]

    @router.post("/models/{model_run_id}/promote", response_model=ModuleModelRunItem)
    def promote_module_model(model_run_id: int, db: Session = Depends(get_db)) -> ModuleModelRunItem:
        try:
            ensure_model_promotion_is_approved(model_run_id=model_run_id)
        except GovernanceApprovalError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

        try:
            row = promote_model_run(db=db, module=module, model_run_id=model_run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        return ModuleModelRunItem(
            module=module,
            model_run_id=row.id,
            model_version=row.model_version,
            is_active=row.is_active,
            created_at=row.created_at,
            promoted_at=row.promoted_at,
            target_column=row.target_column,
            feature_columns=row.feature_columns,
            rows_trained=row.rows_trained,
            metrics=row.metrics,
        )

    @router.get("/predictions", response_model=list[ModulePredictionHistoryItem])
    def get_module_prediction_history(
        limit: int = Query(default=50, ge=1, le=200),
        db: Session = Depends(get_db),
    ) -> list[ModulePredictionHistoryItem]:
        rows = list_recent_predictions(db, module=module, limit=limit)
        return [
            ModulePredictionHistoryItem(
                module=module,
                prediction_id=row.id,
                model_run_id=row.model_run_id,
                region=row.region,
                predicted_risk=row.predicted_risk,
                created_at=row.created_at,
                feature_payload=row.feature_payload,
                explanation=ExplanationPayload(**row.explanation) if row.explanation else None,
            )
            for row in rows
        ]

    return router


climate_router = build_module_router("climate", "climate-risk-regressor")
pandemic_router = build_module_router("pandemic", "pandemic-risk-regressor")
