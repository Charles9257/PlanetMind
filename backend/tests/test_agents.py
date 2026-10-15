from unittest.mock import patch

from conftest import build_training_csv


def _train_module(client, module: str) -> None:
    with patch(
        f"app.api.ml_modules.sync_model_run_registration",
        return_value={"governance_synced": True, "governance_status": "pending", "governance_error": None},
    ):
        response = client.post(
            f"/api/v1/{module}/train",
            files={"dataset": (f"{module}.csv", build_training_csv(), "text/csv")},
            data={"target_column": "risk_score"},
        )
    assert response.status_code == 200


def test_agent_pipeline_runs_full_trace_without_interventions(client) -> None:
    _train_module(client, "climate")

    payload = {
        "module": "climate",
        "region": "Sahel Belt",
        "features": {"feature_a": 0.4, "feature_b": 0.35, "feature_c": 0.3, "feature_d": 0.25},
    }
    response = client.post("/api/v1/agents/pipeline/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["module"] == "climate"
    assert data["status"] == "ok"
    step_names = [step["name"] for step in data["steps"]]
    assert step_names == ["ingestion", "prediction", "explainability", "simulation", "reporting"]
    assert all(step["status"] == "ok" for step in data["steps"])

    simulation_step = data["steps"][3]
    assert simulation_step["output"]["skipped"] is True

    assert "summary" in data["final_output"]
    assert 0 <= data["final_output"]["predicted_risk"] <= 1


def test_agent_pipeline_runs_simulation_when_interventions_given(client) -> None:
    _train_module(client, "climate")

    payload = {
        "module": "climate",
        "region": "Sahel Belt",
        "features": {"feature_a": 0.6, "feature_b": 0.55, "feature_c": 0.5, "feature_d": 0.45},
        "interventions": [{"name": "early_warning_system", "expected_reduction": 0.2}],
    }
    response = client.post("/api/v1/agents/pipeline/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    simulation_step = next(step for step in data["steps"] if step["name"] == "simulation")
    assert simulation_step["output"]["projected_score"] < simulation_step["output"]["baseline_score"]
    assert data["final_output"]["simulation"] is not None


def test_agent_pipeline_fails_cleanly_when_module_has_no_model(client) -> None:
    payload = {
        "module": "cyber-unseeded",
        "region": "Test Region",
        "features": {"feature_a": 0.1},
    }
    response = client.post("/api/v1/agents/pipeline/run", json=payload)
    assert response.status_code == 400
    assert "no trained" in response.json()["detail"].lower()


def test_agent_pipeline_history_lists_runs(client) -> None:
    _train_module(client, "climate")
    client.post(
        "/api/v1/agents/pipeline/run",
        json={
            "module": "climate",
            "region": "History Test",
            "features": {"feature_a": 0.2, "feature_b": 0.2, "feature_c": 0.2, "feature_d": 0.2},
        },
    )

    response = client.get("/api/v1/agents/pipeline/runs?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(row["region"] == "History Test" for row in data)
