# Memory privacy, retention and recovery

## What Aarohi stores

Memory records live in the SQLite database at:
\`<AAROHI_HOME>\\storage\\aarohi.db\`. If \`AAROHI_HOME\` is not set, the configured default is used (currently the resolved working directory). Each record can contain its text, category, scope, source, confidence, confirmation state and timestamps.

Task submission also stores a bounded snapshot of confirmed memories in \`task_context\`. This makes the task's original context inspectable and reproducible.

## Capture and access

- The current automatic capture helper accepts only explicit \`remember\` / \`yaad rakhna\`-style prefixes. Ordinary statements are not automatically ingested.
- Task context includes confirmed memories only, selected by deterministic lexical matching and scope.
- \`memory list\` and \`memory search\` show active records. Archived records are hidden unless explicitly requested.
- Memory text is stored as ordinary SQLite text. The database is local, but it is **not encrypted**. Protect the Windows account and disk; do not place the database in a public/shared folder.
- Credential detection is pattern-based and best-effort. Never intentionally store passwords, API keys, recovery codes, tokens or other secrets.

## Archive versus forget

- **Archive** marks a record archived. It is hidden from normal list/search/context retrieval but remains in the database and can still be inspected in the archived list.
- **Forget** permanently deletes the selected memory row and removes that memory ID from persisted task-context snapshots in the current database. The CLI requires typing the full memory ID, unless \`--yes\` is explicitly supplied.
- Forget does not erase copies in external backups, copied databases, filesystem snapshots or any information independently repeated in task goals, audit events, logs or other records. Review those separately if they may contain the same text.

## Retention and backups

- There is currently no automatic expiry, retention scheduler or automatic backup/export command. Active and archived memories remain until manually archived or forgotten.
- To back up, stop Aarohi processes first, then copy the complete \`aarohi.db\` file to a private, access-controlled location. Keep backups encrypted using a trusted disk/archive tool. A raw copy of a live SQLite database is not the recommended procedure.
- To restore, stop Aarohi, preserve the current database separately, then replace it with the chosen backup. Migration and backup-integrity automation are not yet implemented.
- Deleting a memory from the live database does not delete it from older backups. Expire or securely delete those backups according to your own retention policy.

## CLI examples

\`\`\`powershell
python -c "from aarohi.cli import main; main(['memory', 'list'])"
python -c "from aarohi.cli import main; main(['memory', 'search', 'WealthCodeX', '--scope', 'wealthcodex'])"
python -c "from aarohi.cli import main; main(['memory', 'update', '<MEMORY_ID>', '--content', 'Corrected statement'])"
python -c "from aarohi.cli import main; main(['memory', 'archive', '<MEMORY_ID>'])"
python -c "from aarohi.cli import main; main(['memory', 'list', '--include-archived'])"
python -c "from aarohi.cli import main; main(['memory', 'forget', '<MEMORY_ID>'])"
\`\`\`

Permanent deletion prints the record and asks for the full ID. Use \`--yes\` only when the deletion has already been deliberately confirmed.
