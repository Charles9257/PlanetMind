from __future__ import annotations

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline


def explain_prediction(
    pipeline: Pipeline,
    feature_columns: list[str],
    input_df: pd.DataFrame,
) -> dict:
    """Compute per-feature SHAP contributions for a single prediction row.

    Uses tree_path_dependent perturbation so no background dataset is required,
    and operates on the pipeline's post-preprocessing (imputed + scaled) input
    space, which preserves feature order/identity against feature_columns.
    """
    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]

    transformed = preprocessor.transform(input_df[feature_columns])
    explainer = shap.TreeExplainer(model, feature_perturbation="tree_path_dependent")
    shap_values = explainer.shap_values(transformed)

    values = np.asarray(shap_values)
    if values.ndim == 3:
        values = values[:, :, 0]
    row = values[0]

    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = base_value[0]

    contributions = {
        name: round(float(value), 5) for name, value in zip(feature_columns, row)
    }

    return {
        "base_value": round(float(base_value), 5),
        "contributions": contributions,
    }
