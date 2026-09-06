# Event store recovery
Python standard library only. Run `python3 reproduce.py` and
`python3 -m unittest -v`.

A deployed v1 database has `events(id TEXT PRIMARY KEY, payload TEXT NOT NULL)`.
New deployments include `source TEXT NOT NULL DEFAULT 'legacy'`. Connecting to
v1 must migrate it in place, preserve all records, and assign legacy to old rows.
Migration must be safe to repeat after close/reopen. Never delete the database.

The first incident failure from `python3 reproduce.py` is:
`sqlite3.OperationalError: table events has no column named source`.
After migration, queue retries currently fail with UNIQUE constraint errors.
A further reported issue: an invalid/conflicting record late in a batch leaves
its earlier records committed. Fix these underlying problems and finish recovery.

Preserve connect(path), import_events(db, events), and list_events(db) APIs.
import_events is atomic, including when events is a generator that raises.
Identical (id,payload,source) retries are ignored; conflicts raise ValueError.
New record count excludes identical retries, including within the same batch.
Missing source defaults to legacy. id, payload and source must be nonempty
strings; missing id/payload, wrong types or empty values raise ValueError.
Unrelated existing data must remain untouched on failure; the same connection
must work for a later successful import. Scope is a dedicated store connection
with no caller transaction active. No nested-transaction support is required.
