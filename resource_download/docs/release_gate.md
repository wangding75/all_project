# T47 Release Gate

Release version: `v1.0.0`

This checklist is the release gate for the frozen Server -> Desktop Client
boundary. It is a checklist, not a pre-recorded sign-off; mark each item for
the exact build being released.

Only a build with every applicable item checked may be labeled **Release Gate Passed**.

## Architecture gate

- [ ] `docs/ARCHITECTURE_BOUNDARY.md` is still the only normative boundary.
- [ ] The live server route set contains resolve and the short-lived streaming
      proxy, but no `/v1/jobs`, `/v1/files` or `/v1/automation/*` route.
- [ ] The server has no `JobFile`, server download queue, output directory or
      download-history API.
- [ ] The server owns platform compatibility, Device Proof, License, Quota,
      idempotency and resolve; it does not write downloaded media.
- [ ] Cover presentation cache limits (TTL, file count and bytes) are enabled.
- [ ] The client owns DownloadManager, queue/progress/retry/resume, local
      files, SQLite/history and polling timers.

The structural checks above are covered by:

```powershell
python -m pytest server/tests/test_t46_architecture_boundary.py `
  server/tests/test_t47_architecture_release_gate.py `
  server/tests/test_media_cache.py -q
```

## Functional and security gate

- [ ] `python scripts/quality_gate.py` passes with an isolated `DATA_DIR`.
- [ ] `GET /health` is healthy in the target deployment.
- [ ] Protected resource calls require the current Device Proof and active
      license context; API key is not a download-license bypass.
- [ ] `/v1/resolve` returns client-consumable descriptors and charges quota
      only for a successful new resolve; idempotent replay is not double
      charged.
- [ ] The proxy streams the resolved resource and never creates a server
      download file.
- [ ] Fanqie and Hongguo device E2E passes in the target environment using
      the current resolve-to-client-download path.

## Package gate

- [ ] `python scripts/build_release_package.py` creates the package from a
      clean staging directory.
- [ ] `python scripts/package_smoke.py .\RD-1.0.0-T47.zip` passes.
- [ ] The package runs `RDServer.exe` independently and the desktop binary in
      `CLIENT_MODE=thin`; it does not depend on source checkout paths.
- [ ] No secret, cookie, private key, session token or generated download file
      is included in the package.

## Legacy evidence

The old server-job scripts and documents are historical migration evidence.
They may be used to understand the migration, but they must not be invoked by
CI or used as evidence that the current release contract works.
