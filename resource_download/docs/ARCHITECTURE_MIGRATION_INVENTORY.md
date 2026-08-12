# RD Architecture Migration Inventory

## T47 final release-gate disposition

**Migration Inventory: CLOSED**

All T47 blockers are **RESOLVED/CLOSED**. The T47 architecture boundary is
the accepted release boundary: the RD Server owns platform compatibility,
License/Quota enforcement, resolve, and short-lived download proxying; the
Desktop Client owns Timer polling, Download Manager, local SQLite history,
and resumable client-side download state.

| Area | T47 disposition | Evidence |
| --- | --- | --- |
| Server file storage | **CLOSED — NONE** | No server output/file-storage path in the release boundary; server full tests and quality gate pass. |
| JobFile / JobManager | **CLOSED — NONE** | No server JobFile or JobManager runtime dependency. |
| Server Download Job | **CLOSED — NONE** | `/v1/resolve` returns client-consumable descriptors; no server download-job queue. |
| Server Automation Scheduler | **CLOSED — NONE** | No background scheduler; Client Timer performs active polling. |
| Server platform adapters | **RESOLVED — KEEP_SERVER** | Fanqie/Hongguo adapters, Frida, signing, session recovery, and device discovery remain server-owned. |
| License gateway | **RESOLVED — KEEP_SERVER** | Real PostgreSQL-backed License/Quota full E2E passed. |
| Quota/idempotency/concurrency | **RESOLVED — KEEP_SERVER** | Quota, concurrent quota, failed resolve, and duplicate resolve gates passed. |
| Client Timer | **RESOLVED — MOVE_TO_CLIENT** | Real protected ranking/latest/discovery polling passed with no duplicate polling. |
| Client Download Manager | **RESOLVED — MOVE_TO_CLIENT** | Fanqie/Hongguo resolve-to-download flows passed. |
| Client SQLite/history | **RESOLVED — MOVE_TO_CLIENT** | SQLite reopen and persisted download history passed across recovery checks. |
| Independent deployment | **RESOLVED** | Standalone package smoke and cold-start checks passed. |
| Restart/recovery | **RESOLVED** | RD restart, client reopen, MuMu restart, dynamic rediscovery, and both platform resolves passed. |

### Closed blocker register

The following T47 blocker groups are closed; no item remains in
`IMPLEMENTATION_MIGRATION_REQUIRED`, `MOVE_TO_CLIENT`, or `PENDING` status:

| Blocker IDs | Scope | Status |
| --- | --- | --- |
| D-01..D-07 | Legacy server storage, jobs, files, download queue, and scheduler boundary | **RESOLVED/CLOSED** |
| S-001..S-034 | Server legacy job/storage/automation implementation and APIs | **RESOLVED/CLOSED** |
| S-060..S-061 | Fanqie/Hongguo private compatibility runtime | **RESOLVED/CLOSED — KEEP_SERVER** |
| S-090..S-091 | Server License/Quota and resolve/proxy boundary | **RESOLVED/CLOSED — KEEP_SERVER** |
| C-004 | Client legacy server-job dependency | **RESOLVED/CLOSED** |
| C-010..C-021 | Client Timer, discovery, resolve, Download Manager, and local state | **RESOLVED/CLOSED — MOVE_TO_CLIENT** |
| C-030..C-033 | Client UI automation/job polling remnants | **RESOLVED/CLOSED** |

### T47 release evidence

- License Full E2E: **PASS** — ACTIVE, REVOKED, EXPIRED, DEVICE_REVOKED,
  SERVICE_DOWN/UNKNOWN, RECOVERY, BASIC, PRO, PLAN_SNAPSHOT, MAX_DEVICES,
  ENTITLEMENT, QUOTA, IDEMPOTENCY, CONCURRENT_QUOTA,
  FAILED_RESOLVE_NO_QUOTA, and DUPLICATE_RESOLVE_NO_DOUBLE_CHARGE.
- Client Timer Real E2E: **PASS** — ranking/latest/discovery, Fanqie,
  Hongguo, no duplicate polling, and Server scheduler **NONE**.
- Restart/Recovery: **PASS** — client history persistence, SQLite reopen,
  RD restart, emulator restart with dynamic rediscovery, and both platform
  resolves after recovery.
- Package: `RD-1.0.0-T47.zip`; package integrity and secret safety verified.

**Final status: CLOSED**
