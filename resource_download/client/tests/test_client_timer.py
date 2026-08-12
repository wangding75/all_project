from __future__ import annotations

import json

from client.desktop.client_timer import ClientTimer


def test_timer_persists_success_and_skips_reentrant_poll(tmp_path):
    calls = []

    timer = ClientTimer(lambda: calls.append("poll"), tmp_path / "timer.json", interval_seconds=10)
    assert timer.poll_once() is True
    assert calls == ["poll"]
    payload = json.loads((tmp_path / "timer.json").read_text(encoding="utf-8"))
    assert payload["error_count"] == 0
    assert payload["last_success_at"]


def test_timer_backoff_is_fail_closed_and_stops(tmp_path):
    def fail():
        raise RuntimeError("fixture")

    timer = ClientTimer(fail, tmp_path / "timer.json", interval_seconds=2, max_backoff_seconds=10)
    assert timer.poll_once() is False
    assert timer.state.error_count == 1
    assert timer.state.last_error == "RuntimeError"
    assert timer.state.next_poll_at
    timer.start()
    timer.stop()
    assert timer.state.enabled is False
