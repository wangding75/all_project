# Desktop Client HTTP Call Sites

The page does not implement cryptography. All Device Proof generation and
protected HTTP transport are centralized in the native desktop bridge.

| Call site | Responsibility | Transport |
|---|---|---|
| `client/ui/app.js:apiFetch` | Public/legacy auth calls and protected resource calls | Uses browser `fetch` for public calls; delegates protected paths to `pywebview.api.api_request` |
| `client/ui/app.js:clientMethod` | Local queue, history, file and timer operations | Native bridge only; no Server Job/File API |
| `client/desktop/main.py:WindowApi.api_request` | Unified Desktop JSON boundary | Serializes the exact body once per attempt and delegates to `DesktopHttpClient` |
| `client/desktop/main.py:WindowApi.redeem_license` | License activation | Native activation proof; calls RD `/v1/license/activate` |
| `client/desktop/main.py:WindowApi.resolve_and_download` | Resolve then create local tasks | Calls RD `/v1/resolve`, then `DownloadManager.add_descriptor` |
| `client/desktop/download_manager.py` | Queue, concurrency, progress, retry, pause/resume | Downloads direct/proxy descriptors to client `.part` files |
| `client/desktop/download_repository.py` | Local task/history/file index | SQLite under the current Windows user's LocalAppData |
| `client/desktop/discovery_timer.py` | Hot/new polling and optional local auto-enqueue | Calls protected RD `/v1/discover`; persists state locally |

## Protected scope

The current protected scope is defined in both
`server/app/license_guard.py` and `client/desktop/http_client.py`:

- `GET /v1/search`
- `GET /v1/detail`
- `GET /v1/discover`
- `POST /v1/batch/resolve`
- `POST /v1/image/recognize`
- `GET /v1/hongguo/people`
- `GET /v1/license/status`
- `POST /v1/resolve`
- `GET /v1/downloads/proxy/{ticket}`

The final method, path plus query and raw body hash are signed. HTTP retries
regenerate the proof, so a timestamp/nonce/signature is never replayed.

## Removed server responsibilities

The Desktop main chain must not call or depend on:

- `/v1/jobs`
- `/v1/files`
- `/v1/automation/*`
- a server output directory or server download history

Local files are never uploaded back to RD Server. A browser without the native
bridge fails closed for protected calls with
`DESKTOP_DEVICE_IDENTITY_REQUIRED`.
