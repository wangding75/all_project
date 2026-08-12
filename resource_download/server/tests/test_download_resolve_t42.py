from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


class _ResolvePlatform:
    name = "hongguo"

    async def search(self, query: str, page: int = 1, **kwargs):
        return []

    async def get_detail(self, item_id: str, **kwargs):
        raise NotImplementedError

    async def resolve_download(self, resource_id: str, **kwargs):
        return [
            {
                "download_mode": "direct",
                "resource_id": resource_id,
                "title": "Fixture",
                "suggested_filename": "fixture.mp4",
                "url": "https://cdn.example.invalid/fixture.mp4",
                "range_supported": True,
            }
        ]


def test_resolve_authorizes_before_platform_and_does_not_create_file(device_headers, monkeypatch):
    from app.api import router as router_module

    monkeypatch.setattr(router_module, "get_platform", lambda _name: _ResolvePlatform())
    with TestClient(app) as client:
        response = client.post(
            "/v1/resolve",
            headers={**device_headers, "Idempotency-Key": f"t42-resolve-{uuid.uuid4().hex}"},
            json={"platform": "hongguo", "resource_id": "series-1", "title": "Fixture"},
        )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["descriptor"]["download_mode"] == "direct"
    assert payload["descriptors"][0]["url"].startswith("https://")


def test_resolve_idempotent_replay_does_not_call_platform_again(device_headers, monkeypatch):
    calls = []

    class _Platform(_ResolvePlatform):
        async def resolve_download(self, resource_id: str, **kwargs):
            calls.append(resource_id)
            return await super().resolve_download(resource_id, **kwargs)

    from app.api import router as router_module

    monkeypatch.setattr(router_module, "get_platform", lambda _name: _Platform())
    with TestClient(app) as client:
        headers = {**device_headers, "Idempotency-Key": f"t42-replay-{uuid.uuid4().hex}"}
        first = client.post("/v1/resolve", headers=headers, json={"platform": "hongguo", "resource_id": "series-2"})
        second = client.post("/v1/resolve", headers=headers, json={"platform": "hongguo", "resource_id": "series-2"})
    assert first.status_code == second.status_code == 200
    assert len(calls) == 1
    assert second.json()["idempotent_replay"] is True
