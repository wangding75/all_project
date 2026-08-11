# RD Global Code Review Fix Report (T19)

Baseline: `a23a61b51e3f135d94609a11b02913397124ae42` (`main == origin/main` at review start)

## Finding disposition

| Finding | Status | Verification |
| --- | --- | --- |
| F01 Fanqie complete download | FIXED | Durable/fsynced aggregate artifact, sanitized output path, deterministic non-empty download test |
| F02 Hongguo concurrent isolation | FIXED | Vendor module-global `OUT`/`STATE_DIR` protected by a serialized critical section; concurrent isolation test |
| F03 Fanqie TLS | FIXED | Requests use certificate verification by default; explicit CA bundle only |
| F04 JobFile boundary | FIXED | Adapter paths outside `outputs_dir` are rejected; persisted/loaded paths are revalidated |
| F05 Server file open | FIXED | Server-side open is opt-in and loopback-only; desktop native bridge remains the normal path |
| F06 Sensitive job options | FIXED | Sensitive options are runtime-only; persisted JSON is scrubbed and scanned by regression test |
| F07 `AUTH_MODE` fail-open | FIXED | Invalid values fail startup/request validation; no silent `dev` fallback |
| F08 Quota atomicity | FIXED | Single-worker reservation lock closes check/increment races; failed creation releases reservation |
| F09 Input bounds | FIXED | Platform option allow-list, range limits, naming limits, and concurrency/retry bounds |
| F10 Error sanitization | FIXED | Stable platform errors redact credentials, secret query values, and absolute paths |
| F11 Job retention | FIXED | Terminal records and their outputs are retained within the configured history cap |
| F12 Miscellaneous | PASS | Health/detail responses no longer expose installation paths; additive SQLite migration is idempotent |

## Verification

- `python -m pytest server/tests client/tests -q`: **145 passed** (48 warnings).
- `python scripts/quality_gate.py`: **PASS** (134 passed, 1 skipped in the server gate; all phases passed).
- `python scripts/build_exe.py`: **PASS** (`dist/ResourceDownloader.exe` produced).
- Fresh uvicorn startup and `GET /health`: **PASS** (`STARTUP_SMOKE_PASS`).
- Deterministic Fanqie download and Hongguo concurrent isolation: **PASS**.
- Live License Service E2E (RD HTTP -> License Service HTTP -> PostgreSQL RD Tenant): **PASS**.
  - Activation: **PASS**
  - Protected Job: **PASS**
  - Background ACTIVE: **PASS**
  - Background REVOKED: **DENIED / PASS**
  - Service Down: **FAIL-CLOSED**
  - Recovery: **PASS**
- License authorization/background/revocation/recovery deterministic contract suite: **PASS** in the regression suite.
- Fanqie/Hongguo live upstream scripts correctly reported **SKIP** because no live content ID was configured.

## Security review

`verify=False`, TLS warning suppression, unbounded job options, unsafe JobFile paths, fail-open `AUTH_MODE`, persisted secrets, raw exception responses, and unbounded terminal history were removed or guarded. `/health` and Hongguo detail payloads expose capability flags only, not local filesystem paths.

## Scope

Only `resource_download` was modified. `sx` diff is empty and the License Service workspace is unchanged.
