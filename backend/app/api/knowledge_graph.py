from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import KnowledgeGraphResponse
from app.services.knowledge_graph import build_knowledge_graph, serialize_graph

router = APIRouter(prefix="/api/v1/knowledge-graph", tags=["knowledge-graph"])


@router.get("", response_model=KnowledgeGraphResponse)
def get_knowledge_graph(
    limit_predictions: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> KnowledgeGraphResponse:
    graph = build_knowledge_graph(db, limit_predictions=limit_predictions)
    return KnowledgeGraphResponse(**serialize_graph(graph))
