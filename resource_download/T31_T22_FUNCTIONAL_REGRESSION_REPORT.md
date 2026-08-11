# T31 T22 Functional Regression Report

Date: 2026-08-11

## Functional results

- **Fanqie: PASS.** Through the real RD HTTP process and License Service
  Device-Proof path, a real Fanqie book ID was resolved through `/v1/search`,
  followed by `/v1/detail`, and one real Web-mode chapter downloaded to a
  non-empty TXT file.
- **Hongguo: PASS.** The real RD HTTP process obtained a live upstream
  Hongguo candidate through the current `discover/new` feed, then completed
  `/v1/detail` and one real episode download to a non-empty MP4 file. The
  current guest session's keyword-search endpoint returned an empty/unstable
  upstream result; this was recorded without changing product code, while the
  live candidate/detail/download path passed.
- **Cookie: SAFE.** A runtime-only cookie sentinel was accepted for the
  Fanqie Web request and was absent from the API response, persisted job/data
  files, RD log, and the same Job response after an RD restart.
- **Identity: PASS.** A second Device sharing the License could not read the
  first Device's Job or File listing; License quota remained License-scoped.
- **Idempotency: PASS.** Two concurrent HTTP submissions with the same
  Idempotency-Key returned one Job ID.
- **License E2E: PASS.** T30's real cross-service suite remained PASS for
  BASIC/PRO plans, quota, device limits, isolation, durable idempotency,
  automation revocation, cache TTL fail-closed behavior, and recovery. T31's
  real run additionally completed platform Jobs through the same gateway.

The T31 runner used real RD HTTP, real License Service HTTP, PostgreSQL-backed
tenant data, a real Android/Frida-backed Hongguo runtime, and real upstream
content. It did not use an SX fixture or a mock License Gateway. Temporary
Device keys, License keys, RD data, and the generated Hongguo session config
were removed after the run; no secret values are recorded here.

## Regression checks

- RD server tests: `157 passed, 10 warnings`.
- RD client tests: `10 passed`.
- Quality Gate: **PASS**, all five phases passed; nested regression was
  `156 passed, 1 skipped, 10 warnings` because the recursive gate test is
  intentionally skipped.
- EXE Build: **PASS**, `ResourceDownloader.exe`, 29.35 MB.
- Startup Smoke: **PASS**, the EXE remained alive for 5 seconds and was then
  stopped by the smoke harness.

## Git result

No source change was required by T31. This commit contains only this report.
