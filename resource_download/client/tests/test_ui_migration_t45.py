from pathlib import Path


def test_ui_uses_client_discovery_timer_instead_of_server_scheduler():
    source = (Path(__file__).parents[1] / "ui" / "app.js").read_text(encoding="utf-8")
    assert "configure_discovery_timer" in source
    assert "trigger_discovery_timer" in source
    assert "get_discovery_timer" in source
    assert 'apiFetch("/v1/automation' not in source
    assert "resolve_and_download" in source
