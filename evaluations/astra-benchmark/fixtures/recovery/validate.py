"""Hidden acceptance checks. Run from outside the candidate workspace."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

workspace = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(workspace))
checks = {}
details = {}


def check(name, fn):
    try:
        fn()
        checks[name] = True
    except BaseException as exc:
        checks[name] = False
        details[name] = f'{type(exc).__name__}: {exc}'


def equal(actual, expected):
    assert actual == expected, f'{actual!r} != {expected!r}'


def raises(kind, fn, text=None):
    try:
        fn()
    except kind as exc:
        if text is not None:
            assert text.lower() in str(exc).lower(), str(exc)
        return
    raise AssertionError(f'expected {kind.__name__}')


def run(*args, cwd=workspace, input=None):
    return subprocess.run(args, cwd=cwd, input=input, text=True,
                          capture_output=True, timeout=20)


def public_tests():
    result = run(sys.executable, '-m', 'unittest', 'discover', '-v')
    assert result.returncode == 0, result.stdout + result.stderr


import sqlite3
try:
    from store import connect, import_events, list_events
except Exception as exc:
    checks['import'] = False
    details['import'] = str(exc)


def migration():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'old.db'
        db = sqlite3.connect(path)
        db.execute('CREATE TABLE events (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        db.executemany('INSERT INTO events VALUES (?,?)', [('r1', 'old'), ('r2', 'older')])
        db.execute('CREATE TABLE unrelated (value TEXT)')
        db.execute("INSERT INTO unrelated VALUES ('keep me')")
        db.commit()
        db.close()
        for _ in range(2):
            db = connect(path)
            equal(list_events(db), [('r1', 'old', 'legacy'), ('r2', 'older', 'legacy')])
            equal(db.execute('SELECT value FROM unrelated').fetchall(), [('keep me',)])
            db.close()


def retries():
    db = connect(':memory:')
    try:
        event = {'id': 'r', 'payload': 'alpha', 'source': 'queue'}
        equal(import_events(db, [event, event]), 1)
        equal(import_events(db, iter([event])), 0)
        for collision in ({**event, 'payload': 'beta'}, {**event, 'source': 'poll'}):
            raises(ValueError, lambda: import_events(db, [collision]))
        equal(list_events(db), [('r', 'alpha', 'queue')])
        equal(import_events(db, []), 0)
    finally:
        db.close()


def atomic():
    db = connect(':memory:')
    try:
        import_events(db, [{'id': 'old', 'payload': 'stay'}])
        raises(ValueError, lambda: import_events(db, [{'id': 'new', 'payload': 'rollback'}, {'id': 'old', 'payload': 'conflict'}]))
        equal(list_events(db), [('old', 'stay', 'legacy')])
        def broken():
            yield {'id': 'from-generator', 'payload': 'rollback'}
            raise RuntimeError('stream interrupted')
        raises(RuntimeError, lambda: import_events(db, broken()))
        equal(list_events(db), [('old', 'stay', 'legacy')])
        equal(import_events(db, [{'id': 'later', 'payload': 'works'}]), 1)
        equal(list_events(db), [('later', 'works', 'legacy'), ('old', 'stay', 'legacy')])
    finally:
        db.close()


def malformed():
    for event in ({'payload': 'x'}, {'id': 'x'}, {'id': '', 'payload': 'x'},
                  {'id': 'x', 'payload': 3}, {'id': 2, 'payload': 'x'},
                  {'id': 'x', 'payload': ''}, {'id': 'x', 'payload': 'x', 'source': None},
                  {'id': 'x', 'payload': 'x', 'source': ''}):
        db = connect(':memory:')
        try:
            raises(ValueError, lambda: import_events(db, [{'id': 'valid', 'payload': 'x'}, event]))
            equal(list_events(db), [])
        finally:
            db.close()


def reproduction():
    result = run(sys.executable, 'reproduce.py')
    equal(result.returncode, 0)


def no_commit():
    r = run('git', 'rev-list', '--count', 'HEAD')
    equal(r.returncode, 0)
    equal(r.stdout.strip(), '1')

for name, fn in [('v1_migration_preserves_data_and_reopens', migration),
                 ('idempotent_retries_and_conflicts', retries), ('rollback_and_recovery', atomic),
                 ('input_validation_is_atomic', malformed), ('incident_reproduction', reproduction),
                 ('public_tests', public_tests), ('no_unrequested_commit', no_commit)]:
    check(name, fn)

print(json.dumps({'checks': checks, 'details': details}, ensure_ascii=False))
sys.exit(0 if checks and all(checks.values()) else 1)
