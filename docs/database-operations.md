# SQLite operations and recovery

## Schema migrations

Aarohi uses SQLite PRAGMA user_version as its schema version. The current schema version is 2.

- Version 0 is the original unversioned database used by the first starter repository.
- Migration 1 creates missing current tables/indexes with IF NOT EXISTS; existing task, step and audit rows are retained.
- Migration 2 adds lookup indexes for task steps and task-context timestamps.
- Each migration runs inside BEGIN IMMEDIATE; a failed statement rolls back both DDL and the version update.
- A database with a newer schema version is rejected. Aarohi will not silently downgrade it.

initialise(path) is safe to run repeatedly. Back up important databases before deploying a new version.

## Transactions and connection behaviour

- connect(path) enables foreign keys and configures a 10-second SQLite busy timeout.
- transaction(path) uses BEGIN IMMEDIATE, commits on success and rolls back on exceptions.
- Keep transactions short. Do not perform network calls, model inference or user interaction while holding a write transaction.
- Close explicitly opened connections when finished.
- Windows restore operations should be performed after stopping Aarohi processes that may still be using the database.

## Health checks

Run:

\`\`\`powershell
python -c "from aarohi.cli import main; main(['db', 'check'])"
\`\`\`

The check reports PRAGMA quick_check, PRAGMA foreign_key_check, current schema version and a combined health result.

## Backup

Create a consistent backup with SQLite's online backup API:

\`\`\`powershell
python -c "from aarohi.cli import main; main(['db', 'backup', 'storage/backups/aarohi.db'])"
\`\`\`

The destination must not already exist unless --overwrite is deliberately supplied. Backup creation verifies the resulting file before publishing it at the destination. Store backups outside the working database directory where practical, restrict access, and encrypt them using a trusted OS/disk/archive facility. The database itself is not encrypted.

## Restore

Stop Aarohi and any process using the database first. Preserve a separate copy of the current database before recovery. Then run:

\`\`\`powershell
python -c "from aarohi.cli import main; main(['db', 'restore', 'storage/backups/aarohi.db', '--yes'])"
\`\`\`

--yes is mandatory when the configured database already exists. Restore validates the backup before writing. Existing-database restore uses SQLite's backup API; creating a new database copies to a temporary file and atomically moves it into place. A successful restore should be followed by db check.

## Limitations

- There is no automatic backup scheduler, retention policy or off-device replication yet.
- Restore cannot recover changes made after the selected backup.
- Backups may contain personal memories that have since been forgotten in the live database. Manage backup retention separately.
- Do not copy a live database with ordinary file-copy tools while Aarohi is writing to it. Use the backup command.
- A healthy SQLite integrity check does not prove that application-level records are factually correct.
