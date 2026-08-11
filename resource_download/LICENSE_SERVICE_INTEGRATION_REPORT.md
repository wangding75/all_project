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

## T17 Final Global Review and Delivery Closeout (2026-08-11)

### Final result

```text
RD License Integration: PASS
Client Cutover: COMPLETE
Ready for formal functional/UI acceptance or production deployment preparation.
```

### Review matrix

| Area | Result | Evidence |
|---|---|---|
| Architecture and source boundaries | PASS | RD routes through RD `LicenseGateway`; no RD License DB access; License Service source unchanged |
| Authorization truth | PASS | License / Device / Binding / Plan / Activation truth remains License Service; `vip_expires_at` and CardKey are display/migration-only |
| Protected routes | PASS | `POST /v1/jobs`, batch, bulk retry, job retry, automation PUT and scan use the same Device Proof guard |
| Client Device Proof V3 | PASS | One persistent DPAPI identity, public-key-derived `device_id`, fresh nonce per proof, method/query/raw-body binding, retry re-signing |
| Background entitlement | PASS | Verified saved `license_device_id` → entitlement → quota → Job; `UNKNOWN` and every non-ACTIVE state fail closed |
| E2E fixture isolation | PASS | T16 deterministic discovery is subprocess-local; production discovery code has no fixture switch or hardcoded candidate |
| SDK runtime | PASS | rc3 wheel only; pinned SHA-256 `30EC6E2FFA86627A7F1E6DD2E9AE7F2A07FE44161495AFD864D9090CBBF43A53`; no rc2 in runtime/build/package paths |
| Fail closed and reason semantics | PASS | Timeout, connection failure, 401/409/429/5xx, malformed response and invalid proof cannot become ACTIVE or create a Job |
| Quota ordering | PASS | License/entitlement ACTIVE precedes quota check; denied entitlement does not consume quota |
| Production configuration | PASS | License Service URL, credential, audience, timeout, cache TTL and TLS verification are environment/config driven; `18081` appears only in local E2E harness/docs |
| Secrets | SAFE | No plaintext secret values in tracked source, build/dist, E2E logs or retained fixtures; EXE marker scan clean |
| Documentation | PASS | Release status corrected to `RD LICENSE INTEGRATION PASS / CLIENT CUTOVER COMPLETE`; historical T15/T16 notes retained explicitly |
| Git boundaries | PASS | SX unchanged; License Service source unchanged |

### Executed verification

- `python -m pytest server/tests client/tests -q`: **137 passed**.
- `python scripts/quality_gate.py`: **PASS**; 5 phases passed, server suite 126 passed and 1 expected nested-gate skip.
- Real isolated HTTP Activation + protected `POST /v1/jobs`: **PASS**.
- T16 real background E2E: **PASS** — ACTIVE created one Job; official `LICENSE_REVOKED` created zero Jobs and consumed no quota; Service Down was `UNKNOWN`/fail-closed; recovery resumed; legacy null binding remained fail-closed.
- `python scripts/build_exe.py`: **PASS**; `dist/ResourceDownloader.exe` rebuilt at 28.90 MB.
- EXE startup smoke: **PASS**; the rebuilt EXE and WebView child process remained alive during the smoke window and were cleanly terminated afterward.
- Secret and binary marker audit: **SAFE**; no Master Key, Service Credential, License Key, private key, DSN, full signature, or rc2 marker in the final EXE.

### Delivery package

The final source backup is generated under `dist/` as
`resource_download_license_integration_final_<timestamp>.zip`. It contains a
Git-tracked source snapshot, the final report, test and Quality Gate evidence,
Git commit/tree metadata, and a SHA-256 manifest. `.env`, E2E secrets, private
keys, database files/dumps, logs, runtime data, `tmp/`, `build/`, and `dist/`
outputs are excluded from the archive.
