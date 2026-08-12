# T47 RD Release Package Deployment

This package is a standalone deployment artifact.  The supported production
topology is:

`RDServer.exe` (standalone server) <- `ResourceDownloader.exe` (thin desktop client)

The desktop executable is not the server and must not be used in embedded
mode for a production deployment.  Both executables are started from the
package root.  No source checkout, source virtual environment, `PYTHONPATH`,
or adjacent development directory is required.

## Deployment

1. Extract `RD-1.0.0-T47.zip` into a new deployment directory.
2. Copy `config/production.env.example` to a protected operator-managed
   secret location and provide the License Service endpoint, service
   credential, API key, JWT secret, and other deployment values through the
   process environment or the approved secret manager.  Do not commit or
   copy the resulting secret file into the release package.
3. Leave `ADB_DEVICE` empty unless it is an explicit assertion of the endpoint
   discovered for `MUMU_INSTANCE_NAME=RD测试`. The server queries MuMuManager
   at startup and fails closed if the assertion does not match; no port is an
   RD/SX identity.
4. Install the package's pinned SDK/runtime prerequisites if the deployment
   profile uses the raw `server/` runtime.  The normal production path uses
   the included `RDServer.exe`, which contains the Python server runtime.
5. Start `scripts/start_rd_server.ps1`, or start `RDServer.exe` with the
   package root as its working directory.
6. Verify `GET /health` returns HTTP 200 and the response is consistent with
   the configured platform readiness policy.
7. Start `ResourceDownloader.exe` with `CLIENT_MODE=thin` and
   `API_BASE=http://127.0.0.1:8000` (or the configured RD URL).

The package includes `server/app`, `server/platforms`, curated Hongguo
runtime modules, UI assets, configuration templates, and version metadata.
The raw files are present for transparent audit and controlled fallback; the
release gate starts the packaged server executable.

## Runtime data and secrets

`data/app.db`, `data/jobs/`, `data/outputs/`, and platform session files are
deployment state, not release inputs.  Create them at runtime and protect
them with the deployment account.  Real cookies, session tokens, activation
codes, private keys, service credentials, and master keys must be injected by
the secret manager and must never be placed in this ZIP, Git, logs, or a
release report.

## Release gate smoke

Run the package smoke before any business test:

```powershell
python scripts/package_smoke.py .\RD-1.0.0-T47.zip
```

The smoke extracts to a fresh temporary directory, verifies required files,
imports `app` from that extracted package, starts `RDServer.exe`, checks
`/health`, and starts the thin client.  It removes `PYTHONPATH` and never
uses the source checkout as a runtime dependency.
