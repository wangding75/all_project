# RD License Service Integration Report

## Final status

**BLOCKED**

The real RD HTTP E2E ran against the local License Service and PostgreSQL
tenant. The remaining blockers are frozen-contract/background-context issues,
not an unavailable environment or a Mock-only test.

## Environment and boundaries

- RD commit under test: `28bbef8`
- RD HTTP: dynamic local loopback port `8767`
- License Service HTTP: `http://127.0.0.1:18081`
- License Service health identity: `1.0.0-rc2`
- License Service tenant: `rd`
- Plan: `RD_E2E_DAY`
- SDK: `license_service_client-1.0.0rc2`
- License Service source: unchanged
- SX source: unchanged
- No License Service secret, Device private key, complete signature, or DB
  credential is recorded in this report.

RD reads the License Service base URL, Service Credential, `audience`, timeout,
TLS settings, and cache TTL from environment-backed `server/app/config.py`.
There is no `127.0.0.1:18081` fixed host in production Python source.

## Real HTTP E2E result

The existing `scripts/license_e2e.py` was extended as the single runner. It
uses RD HTTP for registration/login, redeem, protected jobs, proof validation,
quota, and all business assertions. PostgreSQL was used only to attach the
runner's temporary public key to the already-prepared expired/revoked fixture;
the authorization decisions still came through RD HTTP -> License Service
HTTP.

| Scenario | Result | Evidence |
|---|---|---|
| RD Server HTTP | PASS | `/health` returned 200 |
| License Service HTTP | PASS | `/health/live` and `/health/ready` returned 200 |
| Activation | PASS | RD `/v1/auth/redeem` -> License Service activation |
| ACTIVE | PASS | Device Proof V3 protected `POST /v1/jobs` allowed |
| NOT_ACTIVATED | PASS | `403 DEVICE_NOT_ACTIVATED` |
| EXPIRED | PASS | Prepared expired License denied by real `/v1/check` |
| REVOKED | FAIL | HTTP 403, but `/v1/check` returned `DEVICE_NOT_ACTIVATED`; T11 requires `LICENSE_REVOKED` |
| INVALID_PROOF | PASS | Modified signature and wrong device key denied |
| REPLAY | PASS | Reused timestamp/nonce/signature denied as `DEVICE_PROOF_REPLAYED` |
| BODY_BINDING | PASS | Modified raw POST body denied |
| QUERY_BINDING | PASS | Proof for query A denied when sent with query B |
| SERVICE_DOWN | PASS | After cache TTL, License Service stop produced HTTP 503 |
| SERVICE_RECOVERED | PASS | Official container start, healthy, new nonce, ACTIVE request allowed |
| TENANT_ISOLATION | PASS | `service_id`/`tenant_id` request parameters did not switch RD tenant |
| API_KEY_BYPASS | DENIED | API Key plus unactivated Device Proof was denied |
| VIP_BYPASS | DENIED | Future `vip_expires_at` did not authorize the Device |
| CARDKEY_BYPASS | DENIED | Unused legacy CardKey remained unused and did not activate the Device |
| QUOTA | PASS | License ACTIVE still reached the existing RD quota denial |
| CACHE | PASS | Remote ACTIVE, fresh-proof cache hit, TTL expiry remote recheck |
| BACKGROUND_AUTOMATION | BLOCKED | `BACKGROUND_LICENSE_CONTEXT_REQUIRED` |

The strict runner passed every scenario through quota and stopped at the
REVOKED assertion. A preceding complete real HTTP run also passed EXPIRED and
all service/cache scenarios.

## Contract blocker: revoked check reason

The License Service `check_device` implementation filters for
`License.status == ACTIVE` before evaluating the binding. A revoked License
therefore produces no row and returns `DEVICE_NOT_ACTIVATED`. The public check
contract does not define `LICENSE_REVOKED` as a `/v1/check` result. RD must not
invent or reinterpret that frozen service decision. This requires a
License Service contract/source decision before T11 can be PASS.

## Background automation blocker

The call chain in `server/app/automation/hongguo_monitor.py` is:

```text
_enqueue_item
  -> synthesize Identity from saved policy
  -> check_job_quota
  -> JobManager.create_job
```

The scheduled path has no Device Proof or safely expressible device License
context. It must not become a new bypass. The correct result for this current
model is `BLOCKED BACKGROUND_LICENSE_CONTEXT_REQUIRED`; resolving it requires a
decision about the background business authorization model.

## Security and regression checks

- Secrets: **SAFE**. Handoff variables were loaded only in local processes and
  checked as PRESENT/NOT PRESENT; no secret was written to source, report, or
  logs.
- RD/License logs: **SAFE**. RD log/data files and License Service container
  logs were scanned for private keys, master keys, DB passwords, DSNs, and
  complete proof-signature logging; no sensitive-pattern hit was found.
- `python -m pytest server/tests`: **PASS**, 111 passed
- `python scripts/quality_gate.py`: **PASS**
- `SX` diff: **EMPTY**
- License Service source diff: **EMPTY**

## Client cutover

The server-side real-proof path is implemented and tested. The runner remains
the temporary proof-generating client, so the existing transitional state is:

```text
SERVER INTEGRATION PASS
CLIENT CUTOVER PENDING
```
