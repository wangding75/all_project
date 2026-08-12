# RD Package Runtime Requirements

The normal production server is `RDServer.exe`; it contains the server
Python runtime and does not load modules from the source checkout.

The package also includes the auditable raw runtime tree under `server/` and
the curated Hongguo modules under `vendor/hongguo/`.  These files are not a
license to run from a developer checkout.  If an operator selects the raw
runtime profile, it must use only this package directory and the pinned SDK
wheel in `sdk/`.

Required external runtime services are PostgreSQL for License Service, the
MuMu instance named by `MUMU_INSTANCE_NAME` (default `RD测试`, discovered via
MuMuManager; its ADB endpoint is not fixed), and the configured License Service
endpoint.  The release package does not contain credentials,
cookies, session state, private keys, or activation codes.
