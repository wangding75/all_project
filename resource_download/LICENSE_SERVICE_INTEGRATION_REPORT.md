# RD License Service Integration Report

## Final status

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

The server-side integration is complete. The actual RD Client remains outside
this task and therefore stays:

```text
CLIENT CUTOVER PENDING
```
