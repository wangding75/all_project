# RD API Contract

This document describes the live RD Server contract. The authoritative
ownership rules are in [`ARCHITECTURE_BOUNDARY.md`](./ARCHITECTURE_BOUNDARY.md).

The current flow is:

```text
Desktop Client --Device Proof--> RD Server --platform/runtime--> descriptor
Desktop Client --direct or proxy--> upstream --local file--> Client SQLite
```

The Desktop Client owns download tasks, queueing, progress, retry/resume,
local files and history. RD Server owns platform compatibility, License,
Quota, Idempotency, resource discovery and only the necessary download
resolution/streaming work.

## Endpoint summary

| Method | Path | Boundary | Notes |
|---|---|---|---|
| GET | `/health` | Public | Service and platform readiness |
| GET | `/v1/version` | Identity | Client update metadata |
| GET | `/v1/search` | Device License | Platform-neutral search |
| GET | `/v1/detail` | Device License | Resource details |
| GET | `/v1/discover` | Device License | Live hot/new/ranking data; no server scheduler |
| POST | `/v1/batch/resolve` | Device License | Batch resource identification |
| POST | `/v1/image/recognize` | Device License | Cover recognition |
| GET | `/v1/hongguo/people` | Device License | Hongguo people index |
| GET | `/v1/license/status` | Device License | Verified License context and RD quota |
| POST | `/v1/resolve` | Device License | Returns `DownloadDescriptor`; charges quota once on successful resolve |
| GET | `/v1/downloads/proxy/{token}` | Device License | Short-lived streaming proxy; never writes a server download file |
| POST | `/v1/license/activate` | Device Proof body | Current Desktop activation entry point |
| GET | `/v1/covers/{cover_id}.jpg` | Registered cover | Presentation-only resized cover cache |

The live route set does not contain `/v1/jobs`, `/v1/files`, or
`/v1/automation/*`. Those endpoints are removed, not compatibility routes.

## Device-Protected requests

The Desktop Client's native HTTP layer adds these headers to protected
requests:

```http
X-Device-Id: dev_<64 lowercase hex>
X-Device-Key-Algorithm: ED25519
X-Device-Proof-Timestamp: <unix seconds>
X-Device-Proof-Nonce: <fresh nonce>
X-Device-Proof-Signature: <base64url-no-padding>
```

The proof covers the final HTTP method, path plus query, and SHA-256 of the
exact raw request body. A retry creates a new timestamp, nonce and signature.
The browser UI cannot perform protected calls without the Desktop native
bridge and fails closed with `DESKTOP_DEVICE_IDENTITY_REQUIRED`.

`/v1/license/activate` carries an activation proof in its JSON body. The
client does not call License Service directly and never contains RD Service
credentials or License Service private keys.

## POST `/v1/resolve`

Request:

```json
{
  "platform": "hongguo",
  "resource_id": "series-or-episode-id",
  "title": "Example",
  "media_type": "video/mp4",
  "suggested_filename": "example.mp4",
  "range": "all",
  "options": {}
}
```

Response shape:

```json
{
  "descriptor": {
    "platform": "hongguo",
    "resource_id": "series-or-episode-id",
    "title": "Example",
    "media_type": "video/mp4",
    "suggested_filename": "example.mp4",
    "expires_at": "2026-08-13T12:00:00+00:00",
    "download_mode": "direct",
    "url": "https://cdn.example.invalid/example.mp4",
    "headers": {},
    "range_supported": true
  },
  "descriptors": [],
  "quota": {"used": 1, "limit": 50},
  "idempotent_replay": false
}
```

`descriptors` contains one or more client-consumable descriptors. In
`direct` mode the URL is short-lived and only safe temporary headers are
returned. In `proxy` mode the descriptor contains a short-lived RD proxy URL
and ticket. Platform cookies, App sessions, signing secrets and service
credentials are never returned to the client.

The same `Idempotency-Key` may be retried with the same request body. A
successful replay returns the cached descriptor and does not call the
platform adapter or charge quota again. Reusing the key with a different body
returns `409 IDEMPOTENCY_CONFLICT`.

Quota is authoritative on RD Server and is keyed by `license_id`. It is
reserved before platform resolution, committed only after a valid descriptor
is produced, and released on failed resolution. Client-reported file bytes or
download completion are not billing inputs.

## Streaming proxy

`GET /v1/downloads/proxy/{token}` is used only when the client cannot safely
access the upstream resource directly. The proxy streams bytes as they arrive,
does not create a Job or server output file, and releases the upstream
connection when the client disconnects. A client `Range` header is forwarded
when the upstream supports it.

## Legacy authentication endpoints

The following endpoints remain only for explicit legacy migration/test
environments and are marked deprecated in OpenAPI:

- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `GET /v1/auth/me`
- `POST /v1/auth/redeem`

They are not the Desktop download path. The legacy user/JWT and local CardKey
models are not License authority; production authorization comes from the
License Service through RD Server.

## Operations

Admin routes require the configured operations API key and are not part of the
Desktop client contract:

- `GET /v1/admin/health`
- `GET /v1/admin/metrics`
- `GET /v1/admin/sign-pool`
- `GET /v1/admin/users`
- `GET /v1/admin/users/{user_id}`
- `POST /v1/admin/users/{user_id}/status`
- `POST /v1/admin/card-keys/invalidate-batch`

Use the running FastAPI OpenAPI document at `/docs` for request validation
details and response schemas.
