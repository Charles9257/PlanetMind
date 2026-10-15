from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db_models import RiskModelRun, RiskPrediction
from app.services.explainability import explain_prediction


ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"


@dataclass
class TrainingResult:
    model_run: RiskModelRun
    feature_columns: list[str]
    metrics: dict


def _parse_csv_bytes(content: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(content))


def _ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    converted = df.copy()
    for col in columns:
        converted[col] = pd.to_numeric(converted[col], errors="coerce")
    return converted


def _build_pipeline(feature_columns: list[str]) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                feature_columns,
            )
        ],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=250,
                    max_depth=10,
                    min_samples_leaf=2,
                    random_state=42,
                ),
            ),
        ]
    )


def train_from_dataset(
    db: Session,
    module: str,
    dataset_bytes: bytes,
    target_column: str = "risk_score",
) -> TrainingResult:
    raw_df = _parse_csv_bytes(dataset_bytes)
    if target_column not in raw_df.columns:
        raise ValueError(f"Target column '{target_column}' is missing from dataset")

    numeric_columns = [col for col in raw_df.columns if col != target_column]
    if not numeric_columns:
        raise ValueError("Dataset must include numeric feature columns besides the target")

    df = _ensure_numeric(raw_df, numeric_columns + [target_column])
    df = df.dropna(subset=[target_column])
    if len(df) < 20:
        raise ValueError("Dataset needs at least 20 rows after cleaning for reliable training")

    feature_columns = [col for col in numeric_columns if df[col].notna().any()]
    if not feature_columns:
        raise ValueError("No usable numeric features found after dataset cleaning")

    x = df[feature_columns]
    y = df[target_column].clip(lower=0.0, upper=1.0)

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    pipeline = _build_pipeline(feature_columns)
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    metrics = {
        "r2": round(float(r2_score(y_test, predictions)), 5),
        "rmse": round(float(root_mean_squared_error(y_test, predictions)), 5),
        "mae": round(float(mean_absolute_error(y_test, predictions)), 5),
    }

    next_version = int(
        (
            db.query(func.max(RiskModelRun.model_version))
            .filter(RiskModelRun.module == module)
            .scalar()
            or 0
        )
        + 1
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model_file = (
        ARTIFACT_DIR
        / f"{module}_model_v{next_version}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.joblib"
    )
    joblib.dump(
        {
            "pipeline": pipeline,
            "feature_columns": feature_columns,
            "target_column": target_column,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "model_version": next_version,
        },
        model_file,
    )

    has_active = (
        db.query(RiskModelRun)
        .filter(RiskModelRun.module == module, RiskModelRun.is_active.is_(True))
        .first()
        is not None
    )
    default_active = not has_active

    run = RiskModelRun(
        module=module,
        model_version=next_version,
        is_active=default_active,
        promoted_at=datetime.now(timezone.utc) if default_active else None,
        target_column=target_column,
        feature_columns=feature_columns,
        rows_trained=int(len(df)),
        model_path=str(model_file),
        metrics=metrics,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return TrainingResult(model_run=run, feature_columns=feature_columns, metrics=metrics)


def _resolve_model_run(db: Session, module: str, model_run_id: int | None) -> RiskModelRun:
    if model_run_id is not None:
        run = db.get(RiskModelRun, model_run_id)
        if run is None or run.module != module:
            raise ValueError(f"Model run with id={model_run_id} not found for module '{module}'")
        return run

    active = (
        db.query(RiskModelRun)
        .filter(RiskModelRun.module == module, RiskModelRun.is_active.is_(True))
        .order_by(desc(RiskModelRun.promoted_at))
        .first()
    )
    if active is None:
        active = (
            db.query(RiskModelRun)
            .filter(RiskModelRun.module == module)
            .order_by(desc(RiskModelRun.model_version))
            .first()
        )

    if active is None:
        raise ValueError(f"No trained {module} model found. Train a model first.")
    return active


def predict_and_store(
    db: Session,
    module: str,
    features: dict[str, float],
    region: str | None = None,
    model_run_id: int | None = None,
) -> RiskPrediction:
    run = _resolve_model_run(db, module, model_run_id)

    artifact = joblib.load(run.model_path)
    pipeline: Pipeline = artifact["pipeline"]
    expected_features: list[str] = artifact["feature_columns"]

    clean_features: dict[str, float] = {}
    for name in expected_features:
        value = features.get(name, 0.0)
        try:
            clean_features[name] = float(value)
        except (TypeError, ValueError):
            clean_features[name] = 0.0

    input_df = pd.DataFrame([clean_features])
    predicted = float(pipeline.predict(input_df)[0])
    predicted = max(0.0, min(1.0, predicted))

    explanation = explain_prediction(pipeline, expected_features, input_df)

    record = RiskPrediction(
        module=module,
        region=region,
        model_run_id=run.id,
        feature_payload=clean_features,
        predicted_risk=round(predicted, 5),
        explanation=explanation,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_recent_predictions(db: Session, module: str, limit: int = 50) -> list[RiskPrediction]:
    return (
        db.query(RiskPrediction)
        .filter(RiskPrediction.module == module)
        .order_by(desc(RiskPrediction.created_at))
        .limit(max(1, min(limit, 200)))
        .all()
    )


def list_model_runs(db: Session, module: str, limit: int = 100) -> list[RiskModelRun]:
    return (
        db.query(RiskModelRun)
        .filter(RiskModelRun.module == module)
        .order_by(desc(RiskModelRun.model_version))
        .limit(max(1, min(limit, 300)))
        .all()
    )


def promote_model_run(db: Session, module: str, model_run_id: int) -> RiskModelRun:
    run = db.get(RiskModelRun, model_run_id)
    if run is None or run.module != module:
        raise ValueError(f"Model run with id={model_run_id} not found for module '{module}'")

    db.query(RiskModelRun).filter(RiskModelRun.module == module).update({RiskModelRun.is_active: False})
    run.is_active = True
    run.promoted_at = datetime.now(timezone.utc)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
