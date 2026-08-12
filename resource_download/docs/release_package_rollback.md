# T39 RD Release Package Rollback

Rollback is performed by package directory, not by copying files from a
source checkout.

1. Stop `ResourceDownloader.exe` and `RDServer.exe`.
2. Preserve the deployment data directory, SQLite database, job files,
   outputs, and device identity state.  Back up the deployment directory
   before replacement.
3. Replace only the application package with the previously accepted RD ZIP.
   Keep the protected secret-manager values and runtime data in their
   operator-managed locations.
4. Do not force a destructive database downgrade.  The RD schema migration
   is forward-compatible for rollback recovery: if the older binary cannot
   open a newer schema, restore the last database backup or deploy the
   documented forward-recovery binary before retrying the old package.
5. Start the selected package using its own `scripts/start_rd_server.ps1`,
   verify `/health`, then start the thin client.
6. Verify activation/status, a read-only job smoke, and preservation of
   existing License/Plan/Usage records.

The release gate records both the package rollback and the forward-recovery
path.  A rollback is not complete if it only changes documentation or if it
destroys existing usage data.
