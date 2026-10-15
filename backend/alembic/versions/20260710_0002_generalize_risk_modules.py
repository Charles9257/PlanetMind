"""generalize climate tables into module-parameterized risk tables; add agent runs and federated training runs

Revision ID: 20260710_0002
Revises: 20260710_0001
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260710_0002"
down_revision = "20260710_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("climate_model_runs", "risk_model_runs")
    op.drop_index(op.f("ix_climate_model_runs_id"), table_name="risk_model_runs")
    op.drop_index(op.f("ix_climate_model_runs_model_version"), table_name="risk_model_runs")
    op.add_column(
        "risk_model_runs",
        sa.Column("module", sa.String(length=64), nullable=False, server_default="climate"),
    )
    op.create_index(op.f("ix_risk_model_runs_id"), "risk_model_runs", ["id"], unique=False)
    op.create_index(op.f("ix_risk_model_runs_model_version"), "risk_model_runs", ["model_version"], unique=False)
    op.create_index(op.f("ix_risk_model_runs_module"), "risk_model_runs", ["module"], unique=False)

    op.rename_table("climate_predictions", "risk_predictions")
    op.drop_index(op.f("ix_climate_predictions_id"), table_name="risk_predictions")
    op.drop_index(op.f("ix_climate_predictions_model_run_id"), table_name="risk_predictions")
    op.add_column(
        "risk_predictions",
        sa.Column("module", sa.String(length=64), nullable=False, server_default="climate"),
    )
    op.add_column("risk_predictions", sa.Column("explanation", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_risk_predictions_id"), "risk_predictions", ["id"], unique=False)
    op.create_index(op.f("ix_risk_predictions_model_run_id"), "risk_predictions", ["model_run_id"], unique=False)
    op.create_index(op.f("ix_risk_predictions_module"), "risk_predictions", ["module"], unique=False)

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("final_output", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_runs_id"), "agent_runs", ["id"], unique=False)
    op.create_index(op.f("ix_agent_runs_module"), "agent_runs", ["module"], unique=False)

    op.create_table(
        "federated_training_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("num_clients", sa.Integer(), nullable=False),
        sa.Column("rounds", sa.Integer(), nullable=False),
        sa.Column("target_column", sa.String(length=128), nullable=False),
        sa.Column("feature_columns", sa.JSON(), nullable=False),
        sa.Column("client_sample_counts", sa.JSON(), nullable=False),
        sa.Column("federated_metrics", sa.JSON(), nullable=False),
        sa.Column("centralized_metrics", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_federated_training_runs_id"), "federated_training_runs", ["id"], unique=False)
    op.create_index(op.f("ix_federated_training_runs_module"), "federated_training_runs", ["module"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_federated_training_runs_module"), table_name="federated_training_runs")
    op.drop_index(op.f("ix_federated_training_runs_id"), table_name="federated_training_runs")
    op.drop_table("federated_training_runs")

    op.drop_index(op.f("ix_agent_runs_module"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_id"), table_name="agent_runs")
    op.drop_table("agent_runs")

    op.drop_index(op.f("ix_risk_predictions_module"), table_name="risk_predictions")
    op.drop_index(op.f("ix_risk_predictions_model_run_id"), table_name="risk_predictions")
    op.drop_index(op.f("ix_risk_predictions_id"), table_name="risk_predictions")
    with op.batch_alter_table("risk_predictions") as batch_op:
        batch_op.drop_column("explanation")
        batch_op.drop_column("module")
    op.create_index(op.f("ix_climate_predictions_model_run_id"), "risk_predictions", ["model_run_id"], unique=False)
    op.create_index(op.f("ix_climate_predictions_id"), "risk_predictions", ["id"], unique=False)
    op.rename_table("risk_predictions", "climate_predictions")

    op.drop_index(op.f("ix_risk_model_runs_module"), table_name="risk_model_runs")
    op.drop_index(op.f("ix_risk_model_runs_model_version"), table_name="risk_model_runs")
    op.drop_index(op.f("ix_risk_model_runs_id"), table_name="risk_model_runs")
    with op.batch_alter_table("risk_model_runs") as batch_op:
        batch_op.drop_column("module")
    op.create_index(op.f("ix_climate_model_runs_model_version"), "risk_model_runs", ["model_version"], unique=False)
    op.create_index(op.f("ix_climate_model_runs_id"), "risk_model_runs", ["id"], unique=False)
    op.rename_table("risk_model_runs", "climate_model_runs")
