from conftest import build_training_csv


def test_federated_train_matches_shape_of_centralized_baseline(client) -> None:
    csv_payload = build_training_csv(rows=60)

    response = client.post(
        "/api/v1/climate/federated/train",
        files={"dataset": ("federated_climate.csv", csv_payload, "text/csv")},
        data={"target_column": "risk_score", "num_clients": "3", "rounds": "8"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["module"] == "climate"
    assert data["num_clients"] == 3
    assert data["rounds"] == 8
    assert len(data["client_sample_counts"]) == 3
    assert sum(data["client_sample_counts"]) > 0

    for metrics in (data["federated_metrics"], data["centralized_metrics"]):
        assert set(metrics.keys()) == {"r2", "rmse", "mae"}
        assert metrics["rmse"] >= 0
        assert metrics["mae"] >= 0

    # Federated averaging over a simple linearly-generated dataset should stay in the
    # same ballpark as the centralized baseline, not degrade wildly.
    assert data["federated_metrics"]["mae"] < data["centralized_metrics"]["mae"] + 0.25


def test_federated_train_rejects_dataset_too_small_for_client_count(client) -> None:
    csv_payload = build_training_csv(rows=10)

    response = client.post(
        "/api/v1/climate/federated/train",
        files={"dataset": ("tiny.csv", csv_payload, "text/csv")},
        data={"target_column": "risk_score", "num_clients": "5", "rounds": "3"},
    )
    assert response.status_code == 400
    assert "at least" in response.json()["detail"].lower()


def test_federated_runs_history_is_listed(client) -> None:
    csv_payload = build_training_csv(rows=60)
    client.post(
        "/api/v1/pandemic/federated/train",
        files={"dataset": ("federated_pandemic.csv", csv_payload, "text/csv")},
        data={"target_column": "risk_score", "num_clients": "2", "rounds": "5"},
    )

    response = client.get("/api/v1/pandemic/federated/runs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(row["module"] == "pandemic" for row in data)
