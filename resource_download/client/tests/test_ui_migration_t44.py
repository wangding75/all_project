from pathlib import Path


def test_desktop_ui_download_data_source_is_client_owned():
    app_js = Path(__file__).parents[1] / "ui" / "app.js"
    source = app_js.read_text(encoding="utf-8")
    assert "resolve_and_download" in source
    assert "get_download_state" in source
    assert "list_local_files" in source
    assert "/v1/jobs" not in source
    assert "/v1/files" not in source
    assert "download_file" in source  # legacy bridge remains a compatibility fallback
