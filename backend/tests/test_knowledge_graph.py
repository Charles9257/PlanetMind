from unittest.mock import patch

from conftest import build_training_csv


def test_knowledge_graph_reflects_trained_models_and_predictions(client) -> None:
    with patch(
        "app.api.ml_modules.sync_model_run_registration",
        return_value={"governance_synced": True, "governance_status": "pending", "governance_error": None},
    ):
        train_response = client.post(
            "/api/v1/climate/train",
            files={"dataset": ("kg_climate.csv", build_training_csv(), "text/csv")},
            data={"target_column": "risk_score"},
        )
    model_run_id = train_response.json()["model_run_id"]

    client.post(
        "/api/v1/climate/predict",
        json={
            "region": "Knowledge Graph Region",
            "model_run_id": model_run_id,
            "features": {"feature_a": 0.3, "feature_b": 0.3, "feature_c": 0.3, "feature_d": 0.3},
        },
    )

    response = client.get("/api/v1/knowledge-graph")
    assert response.status_code == 200
    data = response.json()

    node_types = {node["type"] for node in data["nodes"]}
    assert {"Module", "ModelRun", "Prediction", "Region"}.issubset(node_types)

    module_node_ids = {node["id"] for node in data["nodes"] if node["type"] == "Module"}
    assert "module:climate" in module_node_ids

    region_node_ids = {node["id"] for node in data["nodes"] if node["type"] == "Region"}
    assert "region:Knowledge Graph Region" in region_node_ids

    relations = {edge["relation"] for edge in data["edges"]}
    assert {"TRAINED_FOR", "USES_MODEL", "PREDICTED_FOR_REGION"}.issubset(relations)
