# RD License Service Integration Report

## T13 status

**PASS**

T13 closes the RD-side background authorization path with the rc3 Server SDK.
The ordinary client path remains Device Proof V3 plus `/v1/check`; scheduled
jobs use only the saved, previously verified `device_id` and the service-auth
`/v1/entitlements/check` path.

## Baseline and boundaries

- License Service Contract Commit: `046dc8e2f621bfa434e8cc4ba88920b431207487`
- License Service HTTP: `http://127.0.0.1:18081` (environment supplied)
- SDK: `license_service_client-1.0.0rc3`
- SDK SHA-256: `30EC6E2FFA86627A7F1E6DD2E9AE7F2A07FE44161495AFD864D9090CBBF43A53`
- License Service source: unchanged
- SX source: unchanged
- No License DB access exists in RD application runtime.
- No Device private key, proof signature, or client nonce is persisted by RD.

## Real HTTP E2E

`scripts/license_e2e.py` ran against RD HTTP, License Service HTTP, and the
real PostgreSQL tenant. Fixture SQL was limited to attaching the temporary
test public key to prepared revoked/expired records and preparing the device
revocation case; all authorization and job assertions traversed the real RD
HTTP -> License Service HTTP path.

| Scenario | Result |
|---|---|
| ACTIVE | PASS |
| NOT_ACTIVATED | PASS |
| EXPIRED | PASS |
| REVOKED | PASS (`LICENSE_REVOKED`) |
| INVALID_PROOF | PASS |
| REPLAY | PASS |
| BODY_BINDING | PASS |
| QUERY_BINDING | PASS |
| SERVICE_DOWN | PASS |
| SERVICE_RECOVERED | PASS |
| TENANT_ISOLATION | PASS |
| API_KEY_BYPASS | DENIED |
| VIP_BYPASS | DENIED |
| CARDKEY_BYPASS | DENIED |
| QUOTA | PASS |
| CACHE | PASS |

## Background automation

| Case | Result |
|---|---|
| Verified device binding | PASS |
| ACTIVE entitlement creates Job | PASS |
| `LICENSE_REVOKED` | DENIED; no Job |
| `LICENSE_EXPIRED` | DENIED; no Job |
| `DEVICE_REVOKED` | DENIED; no Job |
| `DEVICE_NOT_ACTIVATED` | DENIED; no Job |
| Service down / `UNKNOWN` | DENIED; no Job; automation remains enabled |
| Service recovery | PASS; next cycle rechecks normally |
| Legacy `license_device_id = NULL` | `REAUTH_REQUIRED`; fail-closed |
| Entitlement failure and quota | PASS; entitlement is checked before quota/job creation |

Every protected scheduler and enqueue entry point is covered by
`BACKGROUND_LICENSE_PROTECTED_PATHS` / `BACKGROUND_LICENSE_PROTECTED_EXECUTORS`.
The persisted context contains only `license_device_id`; a client JSON
`device_id`, API Key, VIP expiry, or CardKey cannot create or replace it.

## Regression and production review

- `python -m pytest server/tests`: **126 passed**
- `python scripts/quality_gate.py`: **PASS**
- rc2 runtime/vendor dependency: **removed**
- Ordinary client Device Proof requirement: **preserved**
- Background service-auth entitlement: **enforced**
- Revoke/expire/device-revoke/unknown: **fail-closed**
- Secrets: **SAFE**
- SX diff: **EMPTY**
- License Service source diff: **EMPTY**

## Client cutover

The T14 client-side Device Proof V3 cutover and EXE build are complete. T15
real Desktop acceptance is tracked separately below. T16 closes the remaining
background scheduler reachability gap with a process-local deterministic E2E
discovery fixture; production discovery code is unchanged.

```text
CLIENT CUTOVER CODE COMPLETE
```

## T15 Desktop final real E2E (2026-08-11)

The T14 `dist/ResourceDownloader.exe` was exercised through its real
PyWebView native bridge against the local RD Server, License Service, and
PostgreSQL tenant. No client source or License Service source was changed.

| Scenario | Result |
|---|---|
| License Service / PostgreSQL readiness | PASS |
| RD service / `RD_E2E_DAY` plan | READY |
| Fresh Desktop activation | PASS |
| DPAPI identity persistence / restart | PASS; same redacted device fingerprint |
| Protected `POST /v1/jobs` | PASS |
| Automation save with verified device binding | PASS; `license_context_status=READY` |
| Replay / body / query / signature tamper | DENIED |
| Service down after cache expiry | FAIL-CLOSED; HTTP 503 |
| Service recovery with a new proof | PASS |
| Desktop revoke after cache expiry | DENIED; HTTP 403 `LICENSE_REVOKED` |
| Desktop UI/native error mapping | PASS; stable reasons, no traceback observed |
| Secret scan | SAFE |

T15 regression evidence: `server/tests` **126 passed**, client tests **10
passed**, **136 total**; `scripts/quality_gate.py` **PASS**.

The background scheduler could not be completed honestly in this shell. The
real Hongguo discovery provider returned zero items on every active scan
(`last_detected_count=0`, `total_enqueued_count=0`), so the scheduler had no
item to pass to `/v1/entitlements/check`. The persisted automation policy was
verified as device-bound, but no `LICENSE_REVOKED` background entitlement
decision was observed. The T15 shell run therefore did not exercise that
background entitlement decision; this historical reachability gap is closed
by the T16 deterministic background E2E below.

The earlier T13 server-side background test remains recorded above as a
separate historical result; it is not substituted for this T15 Desktop
acceptance. T16 below supplies the missing real scheduler cycle.

## T16 deterministic Background Revoke E2E (2026-08-11)

The real RD application was started with the normal lifespan and a fresh
isolated data directory. The T16 launcher patched platform lookup only inside
that E2E subprocess so `discover("new")` returned one stable
`t16-deterministic-hongguo-candidate-001`; production discovery code and
License Service source were unchanged. The candidate then traversed the real
monitor scheduler, RD `LicenseGateway`, License Service HTTP, PostgreSQL RD
tenant, quota check, and JobManager path.

| Scenario | Discovery | Entitlement / result | New Jobs | Quota |
|---|---:|---|---:|---:|
| ACTIVE scheduler cycle | 1 | ACTIVE; Job created | 1 | 0 → 1 |
| Same policy after official revoke | 1 | `LICENSE_REVOKED` / DENIED | 0 | unchanged |
| License Service application stopped | 1 | `UNKNOWN` / FAIL-CLOSED | 0 | unchanged |
| License Service recovery | 1 | ACTIVE; next cycle resumed | 1 | 0 → 1 |
| Legacy `license_device_id = NULL` | 1 | `BACKGROUND_LICENSE_CONTEXT_REQUIRED` / FAIL-CLOSED | 0 | unchanged |

The revoke assertion was made against the same policy/device and the same
deterministic candidate after resetting only the persisted E2E fixture's
discovery baseline. The no-Job result was therefore caused by the real
`LICENSE_REVOKED` entitlement decision, not zero discovery, quota exhaustion,
disabled automation, duplicate suppression, or an unexecuted scheduler.

T16 real E2E runner: `scripts/t16_background_revoke_e2e.py` (**PASS**).
Deterministic adapter unit coverage: **1 passed**. Full regression after T16:
`server/tests` **127 passed**, client tests **10 passed**, **137 total**;
`scripts/quality_gate.py` **PASS**. License Service HTTP and PostgreSQL
readiness were **PASS**, logs were secret-safe, SX diff was **EMPTY**, and
License Service source diff was **EMPTY**.

```text
BACKGROUND REVOKE: PASS
CLIENT CUTOVER: COMPLETE
RD LICENSE INTEGRATION: PASS
```
