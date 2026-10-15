from __future__ import annotations

import networkx as nx
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db_models import RiskModelRun, RiskPrediction


def build_knowledge_graph(db: Session, limit_predictions: int = 100) -> nx.DiGraph:
    graph = nx.DiGraph()

    model_runs = db.query(RiskModelRun).order_by(desc(RiskModelRun.created_at)).limit(200).all()
    for run in model_runs:
        module_node = f"module:{run.module}"
        run_node = f"model_run:{run.id}"
        graph.add_node(module_node, label=run.module.capitalize(), type="Module")
        graph.add_node(run_node, label=f"{run.module} v{run.model_version}", type="ModelRun")
        graph.add_edge(run_node, module_node, relation="TRAINED_FOR")

    predictions = (
        db.query(RiskPrediction)
        .order_by(desc(RiskPrediction.created_at))
        .limit(limit_predictions)
        .all()
    )
    for prediction in predictions:
        pred_node = f"prediction:{prediction.id}"
        run_node = f"model_run:{prediction.model_run_id}"
        graph.add_node(
            pred_node,
            label=f"Prediction #{prediction.id} ({prediction.predicted_risk:.2f})",
            type="Prediction",
        )
        if run_node not in graph:
            graph.add_node(run_node, label=f"Model run #{prediction.model_run_id}", type="ModelRun")
        graph.add_edge(pred_node, run_node, relation="USES_MODEL")

        if prediction.region:
            region_node = f"region:{prediction.region}"
            graph.add_node(region_node, label=prediction.region, type="Region")
            graph.add_edge(pred_node, region_node, relation="PREDICTED_FOR_REGION")

    return graph


def serialize_graph(graph: nx.DiGraph) -> dict:
    nodes = [
        {"id": node_id, "label": data.get("label", node_id), "type": data.get("type", "Unknown")}
        for node_id, data in graph.nodes(data=True)
    ]
    edges = [
        {"source": source, "target": target, "relation": data.get("relation", "RELATED_TO")}
        for source, target, data in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}
