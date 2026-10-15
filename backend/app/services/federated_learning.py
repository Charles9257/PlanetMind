from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, SGDRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db_models import FederatedTrainingRun


@dataclass
class FederatedTrainingResult:
    run: FederatedTrainingRun


def _parse_csv_bytes(content: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(content))


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "r2": round(float(r2_score(y_true, y_pred)), 5),
        "rmse": round(float(root_mean_squared_error(y_true, y_pred)), 5),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 5),
    }


def train_federated(
    db: Session,
    module: str,
    dataset_bytes: bytes,
    target_column: str = "risk_score",
    num_clients: int = 3,
    rounds: int = 10,
) -> FederatedTrainingResult:
    """Simulate `num_clients` organizations each training a local linear model on their
    own private data shard, aggregated via federated averaging (FedAvg) of coefficients.
    Also trains a centralized Ridge baseline on the pooled training data for comparison,
    evaluated on the same held-out test split -- this directly tests whether federated
    training can match centralized accuracy (H2) without any organization exposing raw data.
    """
    raw_df = _parse_csv_bytes(dataset_bytes)
    if target_column not in raw_df.columns:
        raise ValueError(f"Target column '{target_column}' is missing from dataset")

    feature_columns = [col for col in raw_df.columns if col != target_column]
    if not feature_columns:
        raise ValueError("Dataset must include numeric feature columns besides the target")

    df = raw_df.copy()
    for col in feature_columns + [target_column]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=feature_columns + [target_column])

    min_rows = num_clients * 5 + 5
    if len(df) < min_rows:
        raise ValueError(
            f"Dataset needs at least {min_rows} rows to simulate {num_clients} clients "
            "with a reliable held-out test split"
        )

    x = df[feature_columns].to_numpy(dtype=float)
    y = df[target_column].clip(lower=0.0, upper=1.0).to_numpy(dtype=float)

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    # Partition training rows into client shards, simulating separate organizations that
    # never share raw data -- only their locally fit coefficients cross the "federation".
    rng = np.random.RandomState(42)
    shard_indices = np.array_split(rng.permutation(len(x_train_scaled)), num_clients)
    client_sample_counts = [int(len(idx)) for idx in shard_indices]

    n_features = x_train_scaled.shape[1]
    global_coef = np.zeros(n_features)
    global_intercept = 0.0

    for _ in range(rounds):
        round_coefs = []
        round_intercepts = []
        for idx in shard_indices:
            client_model = SGDRegressor(
                loss="squared_error",
                penalty="l2",
                alpha=0.0001,
                max_iter=5,
                learning_rate="constant",
                eta0=0.01,
                random_state=42,
            )
            client_model.fit(
                x_train_scaled[idx],
                y_train[idx],
                coef_init=global_coef.copy(),
                intercept_init=np.array([global_intercept]),
            )
            round_coefs.append(client_model.coef_)
            round_intercepts.append(client_model.intercept_[0])

        weights = np.array(client_sample_counts, dtype=float)
        weights /= weights.sum()
        global_coef = np.average(round_coefs, axis=0, weights=weights)
        global_intercept = float(np.average(round_intercepts, weights=weights))

    federated_predictions = np.clip(x_test_scaled @ global_coef + global_intercept, 0.0, 1.0)
    federated_metrics = _metrics(y_test, federated_predictions)

    centralized_model = Ridge(alpha=1.0, random_state=42)
    centralized_model.fit(x_train_scaled, y_train)
    centralized_predictions = np.clip(centralized_model.predict(x_test_scaled), 0.0, 1.0)
    centralized_metrics = _metrics(y_test, centralized_predictions)

    run = FederatedTrainingRun(
        module=module,
        num_clients=num_clients,
        rounds=rounds,
        target_column=target_column,
        feature_columns=feature_columns,
        client_sample_counts=client_sample_counts,
        federated_metrics=federated_metrics,
        centralized_metrics=centralized_metrics,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return FederatedTrainingResult(run=run)


def list_federated_runs(db: Session, module: str, limit: int = 50) -> list[FederatedTrainingRun]:
    return (
        db.query(FederatedTrainingRun)
        .filter(FederatedTrainingRun.module == module)
        .order_by(desc(FederatedTrainingRun.created_at))
        .limit(max(1, min(limit, 200)))
        .all()
    )
