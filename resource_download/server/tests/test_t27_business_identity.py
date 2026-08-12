"""T27 business routes use Device Proof + License Context, not User/JWT."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.license_guard import _business_identity
from app.main import app


def _guarded_paths() -> set[str]:
    return {
        route.path
        for route in app.routes
        if any(
            getattr(dependency.call, "__name__", "") == "require_active_device_license"
            for dependency in getattr(getattr(route, "dependant", None), "dependencies", [])
        )
    }


def test_business_identity_has_license_subject_without_legacy_auth():
    identity = _business_identity(None, None)
    assert identity.kind == "license"
    assert identity.user_id is None
    assert identity.license_id is None


def test_all_ordinary_business_surfaces_are_license_guarded():
    guarded = _guarded_paths()
    expected = {
        "/v1/search",
        "/v1/detail",
        "/v1/discover",
        "/v1/batch/resolve",
        "/v1/image/recognize",
        "/v1/hongguo/people",
        "/v1/resolve",
        "/v1/downloads/proxy/{token}",
    }
    assert expected <= guarded


def test_api_key_without_device_proof_cannot_enter_business_route():
    with TestClient(app) as client:
        response = client.get(
            "/v1/search?q=demo",
            headers={"X-API-Key": "dev-key-change-me"},
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "DEVICE_PROOF_REQUIRED"
