from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RiskModelRun(Base):
    __tablename__ = "risk_model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_column: Mapped[str] = mapped_column(String(128), nullable=False)
    feature_columns: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    rows_trained: Mapped[int] = mapped_column(Integer, nullable=False)
    model_path: Mapped[str] = mapped_column(String(512), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)

    predictions: Mapped[list["RiskPrediction"]] = relationship(back_populates="model_run")


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("risk_model_runs.id"), nullable=False, index=True)
    feature_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    predicted_risk: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    model_run: Mapped[RiskModelRun] = relationship(back_populates="predictions")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    steps: Mapped[list] = mapped_column(JSON, nullable=False)
    final_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class FederatedTrainingRun(Base):
    __tablename__ = "federated_training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    num_clients: Mapped[int] = mapped_column(Integer, nullable=False)
    rounds: Mapped[int] = mapped_column(Integer, nullable=False)
    target_column: Mapped[str] = mapped_column(String(128), nullable=False)
    feature_columns: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    client_sample_counts: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    federated_metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    centralized_metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
