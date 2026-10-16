import importlib
import os

import pytest


@pytest.fixture()
def governance_client(monkeypatch):
    monkeypatch.setenv("CONTROL_PLANE_BASE_URL", "http://control-plane.invalid:8100")
    monkeypatch.setenv("CONTROL_PLANE_SYNC_ENABLED", "true")
    monkeypatch.setenv("CONTROL_PLANE_ENFORCE_GOVERNANCE", "true")
    monkeypatch.setenv("CONTROL_PLANE_TIMEOUT_SECONDS", "1")

    from app.services import governance_client

    importlib.reload(governance_client)
    governance_client._TOKEN_CACHE["access"] = ""
    governance_client._TOKEN_CACHE["expires_at"] = 0.0
    return governance_client


def test_sync_model_run_registration_degrades_gracefully_when_control_plane_unreachable(governance_client) -> None:
    # Exercises the real (unmocked) code path -- this is what would have caught the
    # previous NameError from a misplaced module-level cache declaration.
    result = governance_client.sync_model_run_registration(
        model_run_id=1,
        model_version=1,
        is_active=True,
        module="climate",
        model_name="climate-risk-regressor",
    )
    assert result["governance_synced"] is False
    assert result["governance_status"] == "error"
    assert "unreachable" in (result["governance_error"] or "").lower()


def test_sync_model_run_registration_degrades_gracefully_when_token_is_rejected(governance_client, monkeypatch) -> None:
    # A reachable control plane that rejects the service credentials (e.g. mismatched secret)
    # must not turn model training into a 500.
    def reject_token(*args, **kwargs):
        raise governance_client.GovernanceApprovalError(503, "Failed to obtain governance service token")

    monkeypatch.setattr(governance_client, "_get_service_access_token", reject_token)
    result = governance_client.sync_model_run_registration(model_run_id=1, model_version=1, is_active=True)
    assert result["governance_synced"] is False
    assert result["governance_status"] == "error"
    assert "service token" in (result["governance_error"] or "").lower()


def test_ensure_model_promotion_is_approved_raises_when_control_plane_unreachable(governance_client) -> None:
    with pytest.raises(governance_client.GovernanceApprovalError) as exc_info:
        governance_client.ensure_model_promotion_is_approved(model_run_id=1)
    assert exc_info.value.status_code == 503
