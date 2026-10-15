"""create climate analytics tables with model versioning

Revision ID: 20260710_0001
Revises:
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260710_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "climate_model_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_column", sa.String(length=128), nullable=False),
        sa.Column("feature_columns", sa.JSON(), nullable=False),
        sa.Column("rows_trained", sa.Integer(), nullable=False),
        sa.Column("model_path", sa.String(length=512), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_climate_model_runs_id"), "climate_model_runs", ["id"], unique=False)
    op.create_index(op.f("ix_climate_model_runs_model_version"), "climate_model_runs", ["model_version"], unique=False)

    op.create_table(
        "climate_predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("model_run_id", sa.Integer(), nullable=False),
        sa.Column("feature_payload", sa.JSON(), nullable=False),
        sa.Column("predicted_risk", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["model_run_id"], ["climate_model_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_climate_predictions_id"), "climate_predictions", ["id"], unique=False)
    op.create_index(op.f("ix_climate_predictions_model_run_id"), "climate_predictions", ["model_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_climate_predictions_model_run_id"), table_name="climate_predictions")
    op.drop_index(op.f("ix_climate_predictions_id"), table_name="climate_predictions")
    op.drop_table("climate_predictions")

    op.drop_index(op.f("ix_climate_model_runs_model_version"), table_name="climate_model_runs")
    op.drop_index(op.f("ix_climate_model_runs_id"), table_name="climate_model_runs")
    op.drop_table("climate_model_runs")
