"""Reproduce the incident against a disposable legacy database."""
import sqlite3
import tempfile
from pathlib import Path
from store import connect, import_events, list_events

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / 'events.db'
    old = sqlite3.connect(path)
    old.execute('CREATE TABLE events (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    old.execute("INSERT INTO events VALUES ('old-1', 'existing')")
    old.commit()
    old.close()
    db = connect(path)
    batch = [{'id': 'new-1', 'payload': 'hello', 'source': 'queue'}]
    assert import_events(db, batch) == 1
    assert import_events(db, batch) == 0
    assert list_events(db) == [('new-1', 'hello', 'queue'), ('old-1', 'existing', 'legacy')]
    db.close()
    print('Recovery reproduced and verified')
