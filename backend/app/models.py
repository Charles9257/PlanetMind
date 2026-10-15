from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RiskDomain(str, Enum):
    climate = "climate"
    health = "health"
    cyber = "cyber"
    economic = "economic"


class RiskSignal(BaseModel):
    name: str
    value: float = Field(ge=0, le=1)


class RiskPredictionRequest(BaseModel):
    domain: RiskDomain
    region: str = Field(min_length=2, max_length=128)
    signals: List[RiskSignal] = Field(min_length=1)


class RiskPredictionResponse(BaseModel):
    domain: RiskDomain
    region: str
    score: float = Field(ge=0, le=1)
    severity: str
    explanation: str
    top_contributors: Dict[str, float]


class Intervention(BaseModel):
    name: str
    expected_reduction: float = Field(ge=0, le=1)


class SimulationRequest(BaseModel):
    baseline_score: float = Field(ge=0, le=1)
    interventions: List[Intervention] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    baseline_score: float
    projected_score: float
    net_reduction: float
    summary: str


class ExplanationPayload(BaseModel):
    base_value: float
    contributions: Dict[str, float]


class ModuleTrainResponse(BaseModel):
    module: str
    model_run_id: int
    model_version: int
    is_active: bool
    target_column: str
    feature_columns: List[str]
    rows_trained: int
    metrics: Dict[str, float]
    governance_synced: bool = False
    governance_status: Optional[str] = None
    governance_error: Optional[str] = None


class ModulePredictRequest(BaseModel):
    region: Optional[str] = Field(default=None, min_length=2, max_length=128)
    features: Dict[str, float] = Field(min_length=1)
    model_run_id: Optional[int] = None


class ModulePredictResponse(BaseModel):
    module: str
    prediction_id: int
    model_run_id: int
    model_version: int
    region: Optional[str] = None
    predicted_risk: float = Field(ge=0, le=1)
    explanation: ExplanationPayload
    created_at: datetime


class ModulePredictionHistoryItem(BaseModel):
    module: str
    prediction_id: int
    model_run_id: int
    region: Optional[str] = None
    predicted_risk: float = Field(ge=0, le=1)
    created_at: datetime
    feature_payload: Dict[str, float]
    explanation: Optional[ExplanationPayload] = None


class ModuleModelRunItem(BaseModel):
    module: str
    model_run_id: int
    model_version: int
    is_active: bool
    created_at: datetime
    promoted_at: Optional[datetime] = None
    target_column: str
    feature_columns: List[str]
    rows_trained: int
    metrics: Dict[str, float]


class AgentPipelineRunRequest(BaseModel):
    module: str = Field(min_length=2, max_length=64)
    region: Optional[str] = Field(default=None, min_length=2, max_length=128)
    features: Dict[str, float] = Field(min_length=1)
    model_run_id: Optional[int] = None
    interventions: List[Intervention] = Field(default_factory=list)


class AgentStepItem(BaseModel):
    name: str
    status: str
    duration_ms: float
    output: Dict[str, object]


class AgentPipelineRunResponse(BaseModel):
    agent_run_id: int
    module: str
    region: Optional[str] = None
    status: str
    steps: List[AgentStepItem]
    final_output: Dict[str, object]
    created_at: datetime


class FederatedTrainRequest(BaseModel):
    target_column: str = "risk_score"
    num_clients: int = Field(default=3, ge=2, le=10)
    rounds: int = Field(default=10, ge=1, le=100)


class FederatedTrainResponse(BaseModel):
    federated_run_id: int
    module: str
    num_clients: int
    rounds: int
    target_column: str
    feature_columns: List[str]
    client_sample_counts: List[int]
    federated_metrics: Dict[str, float]
    centralized_metrics: Dict[str, float]
    created_at: datetime


class KnowledgeGraphNode(BaseModel):
    id: str
    label: str
    type: str


class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]
