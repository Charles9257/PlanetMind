from __future__ import annotations

import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_planetmind.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app

init_db()

_client = TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    return _client


def build_training_csv(rows: int = 20) -> bytes:
    """Deterministic synthetic dataset shared by climate/pandemic module tests:
    4 numeric feature columns linearly combined into a bounded risk_score target."""
    lines = ["feature_a,feature_b,feature_c,feature_d,risk_score"]
    for i in range(rows):
        a = round(0.02 * i + 0.05, 3)
        b = round(0.025 * i + 0.03, 3)
        c = round(0.018 * i + 0.04, 3)
        d = round(0.012 * i + 0.02, 3)
        target = round(min(0.98, max(0.02, 0.28 * a + 0.28 * b + 0.24 * c + 0.20 * d)), 3)
        lines.append(f"{a},{b},{c},{d},{target}")
    return "\n".join(lines).encode("utf-8")
