from unittest.mock import patch

from app.services.governance_client import GovernanceApprovalError
from conftest import build_training_csv


def test_healthcheck(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_risk_prediction(client) -> None:
    payload = {
        "domain": "climate",
        "region": "East Africa",
        "signals": [
            {"name": "temperature_anomaly", "value": 0.7},
            {"name": "rainfall_deficit", "value": 0.8},
            {"name": "soil_moisture_drop", "value": 0.6},
            {"name": "wildfire_index", "value": 0.2},
        ],
    }
    response = client.post("/api/v1/risk/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "climate"
    assert 0 <= data["score"] <= 1
    assert "explanation" in data


def test_risk_simulation(client) -> None:
    payload = {
        "baseline_score": 0.75,
        "interventions": [
            {"name": "water_reserve_release", "expected_reduction": 0.1},
            {"name": "crop_subsidy", "expected_reduction": 0.15},
        ],
    }
    response = client.post("/api/v1/risk/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["projected_score"] < payload["baseline_score"]


def test_climate_train_predict_and_history(client) -> None:
    csv_payload = build_training_csv()

    with patch(
        "app.api.ml_modules.sync_model_run_registration",
        return_value={"governance_synced": True, "governance_status": "pending", "governance_error": None},
    ):
        train_response = client.post(
            "/api/v1/climate/train",
            files={"dataset": ("climate.csv", csv_payload, "text/csv")},
            data={"target_column": "risk_score"},
        )
    assert train_response.status_code == 200
    train_data = train_response.json()
    assert train_data["module"] == "climate"
    assert train_data["rows_trained"] >= 20
    assert train_data["model_run_id"] > 0
    assert train_data["model_version"] >= 1
    assert train_data["governance_synced"] is True
    assert train_data["governance_status"] == "pending"

    models_response = client.get("/api/v1/climate/models?limit=10")
    assert models_response.status_code == 200
    models_data = models_response.json()
    assert len(models_data) >= 1
    assert any(model["is_active"] for model in models_data)

    promote_response = client.post(f"/api/v1/climate/models/{train_data['model_run_id']}/promote")
    assert promote_response.status_code == 200
    promoted = promote_response.json()
    assert promoted["is_active"] is True

    predict_payload = {
        "region": "East Africa",
        "model_run_id": train_data["model_run_id"],
        "features": {"feature_a": 0.3, "feature_b": 0.28, "feature_c": 0.22, "feature_d": 0.18},
    }
    predict_response = client.post("/api/v1/climate/predict", json=predict_payload)
    assert predict_response.status_code == 200
    pred_data = predict_response.json()
    assert pred_data["module"] == "climate"
    assert 0 <= pred_data["predicted_risk"] <= 1
    assert pred_data["model_version"] == train_data["model_version"]
    assert "contributions" in pred_data["explanation"]
    assert set(pred_data["explanation"]["contributions"].keys()) == {
        "feature_a",
        "feature_b",
        "feature_c",
        "feature_d",
    }

    history_response = client.get("/api/v1/climate/predictions?limit=5")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert len(history_data) >= 1
    assert any(row["prediction_id"] == pred_data["prediction_id"] for row in history_data)
    assert history_data[0]["explanation"] is not None


def test_pandemic_module_is_independent_of_climate(client) -> None:
    csv_payload = build_training_csv()

    with patch(
        "app.api.ml_modules.sync_model_run_registration",
        return_value={"governance_synced": True, "governance_status": "pending", "governance_error": None},
    ):
        train_response = client.post(
            "/api/v1/pandemic/train",
            files={"dataset": ("pandemic.csv", csv_payload, "text/csv")},
            data={"target_column": "risk_score"},
        )
    assert train_response.status_code == 200
    assert train_response.json()["module"] == "pandemic"
    # A fresh module's own versioning starts at 1, independent from climate's counter.
    assert train_response.json()["model_version"] == 1

    pandemic_models = client.get("/api/v1/pandemic/models").json()
    climate_models = client.get("/api/v1/climate/models").json()
    assert all(m["module"] == "pandemic" for m in pandemic_models)
    assert all(m["module"] == "climate" for m in climate_models)


def test_promote_model_blocked_when_governance_denies(client) -> None:
    with patch(
        "app.api.ml_modules.ensure_model_promotion_is_approved",
        side_effect=GovernanceApprovalError(403, "Model promotion blocked by governance policy: approval required"),
    ):
        response = client.post("/api/v1/climate/models/999/promote")

    assert response.status_code == 403
    data = response.json()
    assert "approval required" in data["detail"].lower()


def test_train_climate_returns_governance_sync_error_state(client) -> None:
    csv_payload = build_training_csv()

    with patch(
        "app.api.ml_modules.sync_model_run_registration",
        return_value={"governance_synced": False, "governance_status": "error", "governance_error": "sync failed"},
    ):
        response = client.post(
            "/api/v1/climate/train",
            files={"dataset": ("climate.csv", csv_payload, "text/csv")},
            data={"target_column": "risk_score"},
        )

    assert response.status_code == 200
    assert response.json()["governance_synced"] is False
    assert response.json()["governance_status"] == "error"
