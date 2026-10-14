# RD Deployment Guide

The normative boundary is `docs/ARCHITECTURE_BOUNDARY.md`. The supported
production topology is:

```text
RDServer.exe  <---- HTTP / Device Proof ----  ResourceDownloader.exe
```

The server is the platform-compatibility and control-plane component. The
desktop client is the download product. A source checkout, source virtual
environment and `PYTHONPATH` are not production dependencies.

## Prerequisites

The deployment environment must provide the platform runtime required by the
configured adapters: ADB, a usable Android device, completed Android boot,
the Fanqie/Hongguo applications where applicable, Frida/Java bridge support,
and access to the License Service. Device ports are discovered at runtime;
historical ADB ports are not device identities.

Production secrets and platform session material must be supplied through the
deployment secret mechanism. Do not commit them or include them in a release
ZIP.

## Build and install

From the project root:

```powershell
python scripts/build_release_package.py
python scripts/package_smoke.py .\RD-1.0.0-T47.zip
```

Extract the ZIP into a new deployment directory. Provide the required
environment/configuration values, then start `RDServer.exe` from the package
root. Verify:

```text
GET /health -> HTTP 200
```

Start `ResourceDownloader.exe` with `CLIENT_MODE=thin` and an `API_BASE` that
points at the server. The client must be able to reach the server and must
not need access to server source paths.

## Runtime state

Server-side runtime state is limited to:

- `data/app.db` for control-plane identity, license, quota and idempotency;
- `data/cache/covers/` for bounded, short-lived cover presentation cache;
- platform session/configuration state required by the adapters.

The server does not create or own `data/jobs/`, `data/outputs/`, download
history or a permanent media library. Download files, task state, local file
index and history belong to the Desktop Client.

## Operations

Use the operator API and scripts only for control-plane operations such as
health, metrics, sign-pool status, users and card-key administration. Regular
resource calls use Device Proof plus an active license context; an API key is
not a substitute for download authorization.

For deterministic local verification:

```powershell
python scripts/quality_gate.py
```

For a running deployment:

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY = "<operator key>"
python scripts/smoke_health.py
```

Platform/device E2E must validate the current `POST /v1/resolve` and
client-owned download flow. Historical scripts that call `/v1/jobs`,
`/v1/files` or `/v1/automation/*` are migration evidence only and are not
deployment checks.

For rollback, stop both executables, preserve the control-plane database and
platform session state as required by operations, and restore the previous
package. See `docs/release_package_rollback.md` for the package-specific
rollback sequence.
