"""RD authentication and License Service activation/guard contract tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db
from app.config import get_settings
from app.models_orm import CardKey, User

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def reset_settings():
    settings = get_settings()
    original_auth_mode = settings.auth_mode
    original_api_key = settings.api_key
    yield
    settings.auth_mode = original_auth_mode
    settings.api_key = original_api_key


def _login(client: TestClient) -> str:
    client.post("/v1/auth/register", json={"username": "user123", "password": "password123"})
    return client.post(
        "/v1/auth/login",
        json={"username": "user123", "password": "password123"},
    ).json()["access_token"]


def _activation_body(card_code: str = "LIC-TEST") -> dict:
    return {
        "card_code": card_code,
        "device_id": "dev_" + "1" * 64,
        "device_key_algorithm": "ED25519",
        "device_public_key": "dGVzdC1wdWJsaWMta2V5",
        "proof": {
            "timestamp": 1760000000,
            "nonce": "activation-proof-nonce-1234",
            "signature": "activation-proof-signature",
        },
    }


def test_redeem_no_auth(client):
    response = client.post("/v1/auth/redeem", json={"card_code": "LIC-TEST"})
    assert response.status_code == 401


def test_redeem_api_key_is_not_a_user(client):
    settings = get_settings()
    settings.auth_mode = "dual"
    settings.api_key = "test-api-key"
    response = client.post(
        "/v1/auth/redeem",
        headers={"X-API-Key": "test-api-key"},
        json=_activation_body(),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "请使用用户登录后兑换"


def test_redeem_missing_device_proof_is_stable(client):
    settings = get_settings()
    settings.auth_mode = "dual"
    token = _login(client)
    response = client.post(
        "/v1/auth/redeem",
        headers={"Authorization": f"Bearer {token}"},
        json={"card_code": "LIC-TEST"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "DEVICE_PROOF_REQUIRED"


def test_redeem_uses_license_result_without_touching_legacy_tables(
    client,
    db_session,
    license_gateway_for_tests,
):
    settings = get_settings()
    settings.auth_mode = "dual"
    card = CardKey(code="LIC-LEGACY-01", duration_days=30, is_used=False)
    db_session.add(card)
    db_session.commit()
    token = _login(client)

    response = client.post(
        "/v1/auth/redeem",
        headers={"Authorization": f"Bearer {token}"},
        json=_activation_body("LIC-LEGACY-01"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["reason"] == "ACTIVATED"
    assert payload["license_expires_at"] == "2099-01-01T00:00:00+00:00"
    assert payload["vip_expires_at"] == payload["license_expires_at"]

    db_session.expire_all()
    persisted_card = db_session.query(CardKey).filter(CardKey.code == "LIC-LEGACY-01").one()
    user = db_session.query(User).filter(User.username == "user123").one()
    assert persisted_card.is_used is False
    assert user.vip_expires_at is None
    assert len(license_gateway_for_tests.activations) == 1


def test_resolve_requires_active_device_license_even_with_legacy_vip_or_card(
    client,
    db_session,
    device_headers,
    license_gateway_for_tests,
):
    settings = get_settings()
    settings.auth_mode = "dual"
    settings.api_key = "test-api-key"
    token = _login(client)
    user = db_session.query(User).filter(User.username == "user123").one()
    from datetime import datetime, timedelta, timezone

    user.vip_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
    db_session.add(CardKey(code="LEGACY-CARD", duration_days=30, is_used=False))
    db_session.commit()
    body = {"platform": "fanqie", "resource_id": "12345", "range": "1-1"}

    no_proof = client.post(
        "/v1/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    assert no_proof.status_code == 403
    assert no_proof.json()["detail"] == "DEVICE_PROOF_REQUIRED"

    license_gateway_for_tests.check_result = {
        "activated": False,
        "reason": "LICENSE_EXPIRED",
        "decision": "INACTIVE",
        "source": "remote",
    }
    expired = client.post(
        "/v1/resolve",
        headers={"Authorization": f"Bearer {token}", **device_headers},
        json=body,
    )
    assert expired.status_code == 403
    assert expired.json()["detail"] == "LICENSE_EXPIRED"

    license_gateway_for_tests.check_result = {
        "activated": True,
        "reason": "ACTIVE",
        "decision": "ACTIVE",
        "source": "remote",
    }
    allowed = client.post(
        "/v1/resolve",
        headers={"Authorization": f"Bearer {token}", **device_headers},
        json=body,
    )
    assert allowed.status_code != 403

    api_key_allowed = client.post(
        "/v1/resolve",
        headers={"X-API-Key": "test-api-key", **device_headers},
        json=body,
    )
    assert api_key_allowed.status_code != 403

    api_key_without_proof = client.post(
        "/v1/resolve",
        headers={"X-API-Key": "test-api-key"},
        json=body,
    )
    assert api_key_without_proof.status_code == 403
    assert api_key_without_proof.json()["detail"] == "DEVICE_PROOF_REQUIRED"


def test_guard_binds_raw_body_and_query_to_license_check(
    client,
    device_headers,
    license_gateway_for_tests,
):
    settings = get_settings()
    settings.auth_mode = "dev"
    settings.api_key = "test-api-key"
    raw_body = b'{"platform":"fanqie","resource_id":"raw-1","range":"1-1"}'
    response = client.post(
        "/v1/resolve?mode=full",
        content=raw_body,
        headers={
            "X-API-Key": "test-api-key",
            "Content-Type": "application/json",
            **device_headers,
        },
    )
    assert response.status_code != 403
    check = license_gateway_for_tests.requests[-1]
    assert check["raw_body"] == raw_body
    assert check["request_target"] == "/v1/resolve?mode=full"


def test_guard_maps_invalid_replay_audience_and_unknown_stably(
    client,
    device_headers,
    license_gateway_for_tests,
):
    settings = get_settings()
    settings.auth_mode = "dev"
    settings.api_key = "test-api-key"
    body = {"platform": "fanqie", "resource_id": "stable-1", "range": "1-1"}
    headers = {"X-API-Key": "test-api-key", **device_headers}

    for reason in ("INVALID_DEVICE_PROOF", "DEVICE_PROOF_REPLAYED", "WRONG_AUDIENCE"):
        license_gateway_for_tests.check_result = {
            "activated": False,
            "reason": reason,
            "decision": "INACTIVE",
            "source": "remote",
        }
        response = client.post("/v1/resolve", headers=headers, json=body)
        assert response.status_code == 403
        assert response.json()["detail"] in {
            "DEVICE_PROOF_INVALID",
            "DEVICE_PROOF_REPLAYED",
            "LICENSE_REQUIRED",
        }

    license_gateway_for_tests.check_result = {
        "activated": False,
        "reason": "LICENSE_SERVICE_TIMEOUT",
        "decision": "UNKNOWN",
        "source": "fail_closed",
    }
    unavailable = client.post("/v1/resolve", headers=headers, json=body)
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"] == "LICENSE_SERVICE_TIMEOUT"
