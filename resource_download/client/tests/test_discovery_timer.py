from __future__ import annotations

from client.desktop.discovery_timer import ClientDiscoveryTimer


def test_discovery_timer_builds_local_baseline_and_auto_enqueues_only_new_items(tmp_path):
    responses = [
        {
            "sections": [
                {
                    "kind": "new",
                    "items": [
                        {"id": "a", "platform": "hongguo", "title": "A", "author": "author"},
                    ],
                }
            ]
        },
        {
            "sections": [
                {
                    "kind": "new",
                    "items": [
                        {"id": "a", "platform": "hongguo", "title": "A", "author": "author"},
                        {"id": "b", "platform": "fanqie", "title": "B", "author": "writer"},
                    ],
                }
            ]
        },
    ]
    requested = []
    resolved = []

    def request(target, access_token, api_key):
        requested.append((target, access_token, api_key))
        return responses.pop(0)

    def resolve(item, access_token, api_key):
        resolved.append((item["id"], access_token, api_key))
        return {"ok": True}

    timer = ClientDiscoveryTimer(request, resolve, tmp_path)
    timer.configure(
        {
            "enabled": False,
            "auto_enqueue": True,
            "interval_seconds": 30,
            "include_keywords": ["B"],
            "max_auto_enqueue_per_scan": 5,
        },
        "token",
        "api-key",
    )
    assert timer.trigger_now()["baseline_initialized"] is True
    status = timer.trigger_now()

    assert len(requested) == 2
    assert resolved == [("b", "token", "api-key")]
    assert status["last_detected_count"] == 1
    assert status["total_enqueued_count"] == 1
    assert "platform=all" in requested[0][0]
    timer.shutdown()


def test_discovery_timer_rejects_missing_credentials_and_persists_status(tmp_path):
    timer = ClientDiscoveryTimer(lambda *_args: {}, lambda *_args: {"ok": True}, tmp_path)
    timer.configure({"enabled": False}, "", "")
    assert timer.trigger_now()["last_error"] == "RuntimeError"
    assert (tmp_path / "discovery_timer.json").is_file()
    timer.shutdown()
