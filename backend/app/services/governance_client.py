import os
import time

import httpx


class GovernanceApprovalError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


_TOKEN_CACHE: dict[str, str | float] = {"access": "", "expires_at": 0.0}


def _is_enforced() -> bool:
    return os.getenv("CONTROL_PLANE_ENFORCE_GOVERNANCE", "false").lower() in {"1", "true", "yes", "on"}


def _is_sync_enabled() -> bool:
    return os.getenv("CONTROL_PLANE_SYNC_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def _get_base_url() -> str:
    return os.getenv("CONTROL_PLANE_BASE_URL", "http://control-plane:8100").rstrip("/")


def _get_timeout_seconds() -> float:
    return float(os.getenv("CONTROL_PLANE_TIMEOUT_SECONDS", "5"))


def _get_service_access_token() -> str:
    now = time.time()
    cached = str(_TOKEN_CACHE.get("access", ""))
    expires_at = float(_TOKEN_CACHE.get("expires_at", 0.0))
    if cached and expires_at - now > 30:
        return cached

    base_url = _get_base_url()
    response = httpx.post(
        f"{base_url}/control/auth/service-token",
        json={
            "client_id": os.getenv("CONTROL_PLANE_SERVICE_CLIENT_ID", "planetmind-backend"),
            "client_secret": os.getenv("CONTROL_PLANE_SERVICE_CLIENT_SECRET", "change-me-service-secret"),
        },
        timeout=_get_timeout_seconds(),
    )
    if response.status_code >= 400:
        raise GovernanceApprovalError(503, "Failed to obtain governance service token")

    payload = response.json()
    access = str(payload.get("access", ""))
    if not access:
        raise GovernanceApprovalError(503, "Governance service token response invalid")

    _TOKEN_CACHE["access"] = access
    _TOKEN_CACHE["expires_at"] = now + 14 * 60
    return access


def _build_auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_get_service_access_token()}"}


def sync_model_run_registration(
    *,
    model_run_id: int,
    model_version: int,
    is_active: bool,
    module: str = "climate",
    model_name: str = "climate-risk-regressor",
) -> dict[str, object]:
    if not _is_sync_enabled():
        return {"governance_synced": False, "governance_status": "disabled"}

    base_url = _get_base_url()
    try:
        response = httpx.post(
            f"{base_url}/control/governance/registry/sync/",
            json={
                "organization": int(os.getenv("CONTROL_PLANE_DEFAULT_ORG_ID", "1")),
                "source_system": "fastapi",
                "external_model_run_id": model_run_id,
                "module": module,
                "model_name": model_name,
                "model_version": str(model_version),
                "is_active": is_active,
            },
            headers=_build_auth_headers(),
            timeout=_get_timeout_seconds(),
        )
    except httpx.RequestError as exc:
        return {
            "governance_synced": False,
            "governance_status": "error",
            "governance_error": f"Governance registry sync unreachable: {exc}",
        }
    except GovernanceApprovalError as exc:
        # Token request was rejected (e.g. mismatched client secret); don't fail model training over it.
        return {
            "governance_synced": False,
            "governance_status": "error",
            "governance_error": f"Governance registry sync failed: {exc.detail}",
        }

    if response.status_code >= 400:
        return {
            "governance_synced": False,
            "governance_status": "error",
            "governance_error": f"Governance registry sync failed: HTTP {response.status_code}",
        }

    payload = response.json()
    approval = payload.get("approval", {}) if isinstance(payload, dict) else {}
    return {
        "governance_synced": True,
        "governance_status": approval.get("status", "pending"),
        "governance_error": None,
    }


def ensure_model_promotion_is_approved(model_run_id: int) -> None:
    if not _is_enforced():
        return

    base_url = _get_base_url()
    timeout_seconds = _get_timeout_seconds()

    url = f"{base_url}/control/governance/approvals/status/"

    try:
        response = httpx.get(
            url,
            params={"external_model_run_id": model_run_id, "source_system": "fastapi"},
            headers=_build_auth_headers(),
            timeout=timeout_seconds,
        )
    except httpx.RequestError as exc:
        raise GovernanceApprovalError(503, f"Governance service unreachable: {exc}") from exc

    if response.status_code >= 500:
        raise GovernanceApprovalError(503, "Governance service unavailable")
    if response.status_code in {401, 403}:
        raise GovernanceApprovalError(503, "Governance service authorization failed")
    if response.status_code >= 400:
        raise GovernanceApprovalError(503, f"Governance query failed: HTTP {response.status_code}")

    payload = response.json()
    if isinstance(payload, dict) and payload.get("approved") is True:
        return

    raise GovernanceApprovalError(403, "Model promotion blocked by governance policy: approval required")
