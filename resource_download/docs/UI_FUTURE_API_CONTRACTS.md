# UI Future API Contracts (Non-normative)

Status: design notes only. The live contract is docs/api.md and the
normative responsibility boundary is docs/ARCHITECTURE_BOUNDARY.md.

## Current capabilities

| UI capability | Current owner and contract |
| --- | --- |
| Discovery, ranking and latest content | RD Server resource APIs |
| Batch resource resolution | POST /v1/batch/resolve |
| Download queue, pause, retry and reorder | Desktop Client DownloadManager |
| Download files and history | Desktop Client local directory and SQLite |
| Periodic discovery | Desktop Client ClientDiscoveryTimer |

## Rules for future features

Future subscription, auto-refresh or auto-download features must be driven by
the Desktop Client timer and local queue. The server may expose protected
read-only resource APIs or resolve descriptors, but must not regain ownership
of download jobs, download files, history or an automation scheduler.

Future server APIs must not reintroduce:

- /v1/jobs;
- /v1/files;
- /v1/automation/*;
- server output directories or permanent media storage.

Any proposal that changes this boundary must first update the normative
architecture document and the release gate; adding a route alone is not an
architecture decision.
