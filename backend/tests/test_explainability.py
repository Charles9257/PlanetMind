import pandas as pd

from app.services.explainability import explain_prediction
from app.services.ml_module_service import _build_pipeline


def test_explain_prediction_returns_contribution_per_feature() -> None:
    feature_columns = ["feature_a", "feature_b", "feature_c"]
    rows = [
        {"feature_a": 0.1, "feature_b": 0.2, "feature_c": 0.1, "target": 0.15},
        {"feature_a": 0.9, "feature_b": 0.8, "feature_c": 0.9, "target": 0.9},
        {"feature_a": 0.3, "feature_b": 0.4, "feature_c": 0.3, "target": 0.35},
        {"feature_a": 0.6, "feature_b": 0.7, "feature_c": 0.6, "target": 0.65},
        {"feature_a": 0.2, "feature_b": 0.1, "feature_c": 0.2, "target": 0.18},
        {"feature_a": 0.8, "feature_b": 0.9, "feature_c": 0.8, "target": 0.85},
    ]
    df = pd.DataFrame(rows)
    pipeline = _build_pipeline(feature_columns)
    pipeline.fit(df[feature_columns], df["target"])

    input_df = pd.DataFrame([{"feature_a": 0.7, "feature_b": 0.75, "feature_c": 0.7}])
    explanation = explain_prediction(pipeline, feature_columns, input_df)

    assert set(explanation["contributions"].keys()) == set(feature_columns)
    assert isinstance(explanation["base_value"], float)
    assert all(isinstance(value, float) for value in explanation["contributions"].values())

    predicted = pipeline.predict(input_df)[0]
    reconstructed = explanation["base_value"] + sum(explanation["contributions"].values())
    assert abs(predicted - reconstructed) < 1e-2
