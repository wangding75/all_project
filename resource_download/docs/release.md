# RD Release Manual

This document describes the frozen T47 release topology. The authoritative
responsibility boundary is `docs/ARCHITECTURE_BOUNDARY.md`.

## Release topology

Build a standalone server and a thin desktop client:

```text
RDServer.exe  <---- HTTP / Device Proof ----  ResourceDownloader.exe
  platform adapters,                         queue, downloads,
  resolve, License/Quota,                    files, SQLite/history,
  short-lived streaming proxy                timers and UI state
```

`ResourceDownloader.exe` must run with `CLIENT_MODE=thin`. Embedded server
mode is for development only and is not a production release topology.

## Build

Use the complete package builder from the repository root:

```powershell
python scripts/build_release_package.py
python scripts/package_smoke.py .\RD-1.0.0-T47.zip
```

The package builder is the supported assembly path. It builds both
executables, copies the curated server/platform runtime and safe templates,
and writes a fresh release ZIP. The smoke test extracts into a temporary
directory and verifies the package without using the source checkout as a
runtime dependency.

## Runtime state

The server may persist only control-plane state and bounded presentation data:

- `data/app.db` for server-side identity/license/quota/idempotency state;
- `data/cache/covers/` for short-lived, bounded cover presentation files;
- platform session/configuration state managed by the deployment.

The server does not create or own `data/jobs/`, `data/outputs/`, download
history, or a permanent media library. Download files, task state and history
are owned by the Desktop Client and its local SQLite/download directory.

Secrets, cookies, activation codes, private keys and service credentials must
be injected by the deployment secret mechanism. They must not be included in
the ZIP, Git, logs or release reports.

## Verification

Run the deterministic local gate with an isolated test data directory:

```powershell
python scripts/quality_gate.py
```

Run the health smoke against an already started RD Server:

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY = "<operator key>"
python scripts/smoke_health.py
```

Platform/device E2E is an environment gate and must exercise the current
`POST /v1/resolve` plus client-owned download flow. The historical scripts
that call `/v1/jobs`, `/v1/files` or `/v1/automation/*` are not release gates.
