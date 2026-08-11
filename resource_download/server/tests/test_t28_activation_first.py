"""T28 activation-first server/client boundary checks."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _activation_body() -> dict:
    return {
        "card_code": "RD-T28-TEST",
        "device_id": "dev_" + "a" * 64,
        "device_key_algorithm": "ED25519",
        "device_public_key": "public-key",
        "proof": {
            "timestamp": 1760000000,
            "nonce": "activation-nonce-123456",
            "signature": "activation-signature",
        },
    }


def test_activation_first_endpoint_does_not_require_user_or_jwt():
    with TestClient(app) as client:
        response = client.post("/v1/license/activate", json=_activation_body())
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_activation_endpoint_requires_device_activation_proof():
    body = _activation_body()
    body.pop("proof")
    with TestClient(app) as client:
        response = client.post("/v1/license/activate", json=body)
    assert response.status_code == 403
    assert response.json()["detail"] == "DEVICE_PROOF_REQUIRED"


def test_license_status_is_business_guarded():
    from app.main import app as fastapi_app

    guarded = {
        route.path
        for route in fastapi_app.routes
        if route.path == "/v1/license/status"
        and any(
            getattr(dependency.call, "__name__", "") == "require_active_device_license"
            for dependency in getattr(getattr(route, "dependant", None), "dependencies", [])
        )
    }
    assert guarded == {"/v1/license/status"}
