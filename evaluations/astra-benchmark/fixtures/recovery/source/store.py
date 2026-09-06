"""Small SQLite event store, upgraded in place from schema v1."""
import sqlite3


def connect(path):
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL, source TEXT NOT NULL DEFAULT "legacy")')
    db.commit()
    return db


def import_events(db, events):
    """Atomically import a batch; identical retries are idempotent.

    Return number of newly inserted records. Existing identical records count
    as zero. A reused id with different payload or source raises ValueError.
    Missing source means 'legacy'. Every id/payload/source must be a nonempty
    string. A failure must leave ALL rows in this batch unapplied.
    """
    inserted = 0
    for event in events:
        db.execute('INSERT INTO events (id,payload,source) VALUES (?,?,?)',
                   (event['id'], event['payload'], event.get('source', 'legacy')))
        db.commit()
        inserted += 1
    return inserted


def list_events(db):
    return db.execute('SELECT id,payload,source FROM events ORDER BY id').fetchall()
