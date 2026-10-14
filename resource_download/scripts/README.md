# RD Scripts

The current release contract is the frozen Server -> Desktop Client boundary
in `docs/ARCHITECTURE_BOUNDARY.md`.

## Local verification

Run the deterministic unit and architecture gate from the project root:

```powershell
python scripts/quality_gate.py
```

`quality_gate.py` creates an isolated temporary `DATA_DIR`, so a developer's
old quota, idempotency or license database cannot change the result.

With an already running server, run the health smoke:

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY = "<operator key>"
python scripts/smoke_health.py
```

`ci_smoke.ps1` and `ci_smoke.sh` run this health check followed by the local
test suite. They do not run platform E2E unless a dedicated current harness is
added for the Device Proof + `/v1/resolve` + client download flow.

## Packaging

The supported release assembly path is:

```powershell
python scripts/build_release_package.py
python scripts/package_smoke.py .\RD-1.0.0-T47.zip
```

## Legacy scripts

`e2e_fanqie.py`, `e2e_hongguo.py`, `license_e2e.py` and the `t16_*` scripts
are archived migration-era tools. They reference the removed server job/file
or automation contract and are not release gates. Do not use their success or
failure as evidence for the current architecture.
