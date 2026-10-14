# Hongguo Server Setup

Hongguo compatibility, signing, Frida/Java bridge and session handling are
server-owned capabilities. The Desktop Client must not contain these private
platform dependencies.

## Prerequisites

Provide the curated vendor/hongguo runtime and the required device/session
configuration through the deployment environment. Keep session tokens and
private configuration out of Git, release archives and logs.

The server environment must have a discoverable Android device, completed
Android boot, Hongguo installed, and the configured signing/runtime services
available. ADB ports are discovered at runtime and are not permanent device
identities.

## Health check

With the standalone RD Server running:

~~~powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY = "<operator key>"
python scripts/smoke_health.py
~~~

The health response should report the configured Hongguo platform readiness.

## Current acceptance flow

Platform acceptance must use the current protected flow:

1. the Desktop Client sends a Device Proof request to POST /v1/resolve;
2. the server resolves Hongguo metadata and returns a client-consumable
   DownloadDescriptor;
3. the Desktop Client DownloadManager downloads through the direct URL or
   short-lived streaming proxy and stores the file locally;
4. local SQLite history and the local download directory contain the result.

Historical e2e_hongguo.py job/poll/output-directory checks are migration
evidence only and are not release gates.
