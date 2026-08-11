# T30 Real License Plan Cross-Service E2E Report

Date: 2026-08-11

## Scope

This report records the T30 real cross-service acceptance run for the RD
License Plan / Device Proof path. The run used the local License Service HTTP
container, its PostgreSQL tenant database, and a real RD HTTP process. No
mock License Gateway or fake License Service was used in the cross-service
run. Temporary test keys, device keys, and data were generated for the run
and removed afterward; no credential values are recorded here.

Endpoints used during the run were loopback-only: License Service on port
18081, PostgreSQL on port 55432, and RD on port 18082.

## Acceptance results

- BASIC `basic/v1`: 10 successful quota reservations, then the 11th request
  returned HTTP 429.
- PRO `pro/v1`: quota 100; PRO `pro/v2`: quota 200; snapshot v1 activation
  returned the expected immutable plan snapshot.
- One License activated on three Devices; the fourth Device was rejected with
  `DEVICE_LIMIT_REACHED`.
- Devices sharing one License shared quota while Job reads and listings
  remained Device-isolated.
- Repeated requests with one Idempotency-Key produced one Job and consumed one
  quota slot.
- Automation configured with an active License returned READY; after database
  revocation and cache expiry, scan authorization was rejected and created no
  new Job.
- With the License Service stopped beyond the configured cache TTL, a fresh
  proof request failed closed with HTTP 503; after service recovery the same
  Device returned ACTIVE again.

Result: **PASS** (`T30_REAL_CROSS_SERVICE_E2E_PASS`).

## Regression and release checks

- License Service tests: `78 passed`.
- RD server tests: `157 passed, 10 warnings`.
- RD client tests: `10 passed`.
- RD Quality Gate: **PASS**, all five phases passed. Its nested test run
  reported `156 passed, 1 skipped, 10 warnings` because the recursive Quality
  Gate test is intentionally skipped.
- EXE build: **PASS**, `ResourceDownloader.exe`, 29.35 MB.
- EXE startup smoke: **PASS**, process remained alive for 5 seconds and was
  then stopped by the smoke harness.

## Source note

The real tenant migration run exposed a pre-existing migration compatibility
defect: the tenant `alembic_version.version_num` column was limited to 32
characters while the new revision identifier is longer. The fix was isolated
in License Service commit `aa29617` (`T30 widen tenant migration version
storage`), then the License Service test suite and this T30 E2E run were
repeated successfully.

No temporary E2E harness, key material, database password, or runtime fixture
was committed.
