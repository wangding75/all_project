# T29 Legacy Boundary and Migration Record

## Production boundary

- Ordinary discovery, detail, batch, job, automation, and file routes authorize only through Device Proof plus the verified License Context.
- User registration, password login, JWT issuance, `/v1/auth/me`, and the old redeem route are deprecated compatibility routes and return `LEGACY_USER_AUTH_DISABLED` (HTTP 410) unless `LEGACY_USER_AUTH_ENABLED=true` is explicitly set for a migration or test environment.
- `User`, password hashes, `vip_expires_at`, `CardKey`, and `UsageDaily` remain historical/admin or compatibility data. They are not authorization facts for the production License path and are not used to bypass License state or quota.

## Durable migrations

- `license_usage_daily` is keyed by `(license_id, day)` and is created by the idempotent schema initializer.
- `idempotency_records` stores the License+Device scope, request fingerprint, bounded replay response, and expiry. Job creation uses it together with the in-process lock.
- Persisted Job JSON is migrated on load. A job is re-owned only when both `owner_kind=license_device`, `license_id`, and `device_id` were durably present. Every other historical job is rewritten as `legacy_unowned` and remains read-only to commercial License identities.
- JobFile owner fields are copied from the parent Job during persistence and response serialization; client-provided file ownership is never trusted.

## Static scan classification

| Match | Classification |
|---|---|
| `require_identity`, JWT/password helpers, `/v1/auth/*` | `LEGACY_READ_ONLY` / `TEST_ONLY`; never an ordinary business dependency |
| `User`, `vip_expires_at`, `CardKey`, `UsageDaily` | `ADMIN_ONLY` / `LEGACY_READ_ONLY` |
| `license_id`, `device_id`, `LicenseUsageDaily`, `idempotency_records` | `PRODUCTION` License-subject path |

