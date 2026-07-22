# Self-test report

## Reused evidence-gate scripts

The following four scripts are copied from the v3 package that was executed under Windows PowerShell on 2026-07-22:

- `collect-native-crash.ps1`
- `run-native-ab-matrix.ps1`
- `validate-native-diagnostics.ps1`
- `test-gate1-fixtures.ps1`

Observed result supplied by the user:

```text
[+] PowerShell parser and automatic-variable preflight passed.
[+] All 19 fixture cases passed.
```

## New Quark automation scripts

The following scripts were added:

- `run-quark-diagnostics.ps1`
- `summarize-quark-diagnostics.ps1`
- `test-quark-automation-scripts.ps1`

Before packaging they passed local static checks for:

- PowerShell lexer errors: 0;
- unmatched parentheses/braces/brackets: 0;
- unclosed strings/here-strings detected by lexer: 0;
- declarations or direct assignments to read-only `$PID`/`$Host`: 0;
- trailing characters after line-continuation backticks: 0.

The package also performs a real PowerShell parser pass over all seven `.ps1` files before any ADB or matrix operation. Any parser or read-only automatic-variable error exits non-zero and blocks execution.

The current file-generation environment does not include Windows PowerShell, so no claim is made that the three new scripts were executed end-to-end against ADB here. Runtime execution is deliberately gated on the target Windows machine by `test-quark-automation-scripts.ps1`.
