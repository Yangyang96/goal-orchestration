"""Deterministic fixtures and private graders. Never copy this file into a task workspace."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import textwrap

TASKS = ("tiny", "parallel", "dirty", "review", "handoff", "stale")

SPEC = '''Implement ledgerkit using the Python standard library only.
Public interfaces:
- csv_reader.read_csv(text) and jsonl_reader.read_jsonl(text) return normalized rows.
  Input fields: id, amount, tag (optional, defaults to empty string). Ignore blank
  JSONL lines. Trim string fields. Require nonempty string id and string tag.
  amount is a string decimal: finite, exactly representable in cents (extra trailing
  zeros are allowed). Reject bools/numbers and fractions of a cent with ValueError.
  A normalized row has {ID_FIELD: id, "cents": integer, "tag": string}; import
  ID_FIELD from contract.py. Parsers reject missing/extra CSV cells, missing required
  headers, malformed JSON and non-object JSON. ValueError must include "line N",
  where N is the physical input line (CSV header is line 1; multiline quoted fields
  use the last physical line of the record).
- store.import_rows(db_path, rows) imports an iterable in one atomic transaction.
  Return number of newly inserted rows. Reimporting identical id/cents/tag is a no-op;
  conflicting duplicate id raises ValueError and rolls back the ENTIRE import,
  including rows inserted before the conflict or before an iterator error.
  Existing data must survive failures. Independent calls against the same SQLite
  file must not overwrite each other's data. No global temporary DB filenames.
- store.summary(db_path, tag=None) returns {"rows": count, "total_cents": sum,
  "by_tag": {tag: cents_sum}}; optional tag filters ALL three aggregates.
- python -m ledgerkit --format csv|jsonl --db PATH [--group-tag TAG] reads stdin,
  imports it, and emits only one JSON summary on stdout. Parsing or import failure:
  nonzero exit, diagnostic on stderr, no successful-looking JSON, no partial import.
Do not rename these APIs. Add useful tests and update README. Do not commit changes.
'''

CLI_STUB = 'raise SystemExit("CLI is not implemented")\n'
STUBS = {
    "ledgerkit/__init__.py": '"""Small ledger import package."""\n',
    "ledgerkit/contract.py": 'ID_FIELD = "id"\n',
    "ledgerkit/normalize.py": 'def normalize(row):\n    raise NotImplementedError\n',
    "ledgerkit/csv_reader.py": 'def read_csv(text):\n    raise NotImplementedError\n',
    "ledgerkit/jsonl_reader.py": 'def read_jsonl(text):\n    raise NotImplementedError\n',
    "ledgerkit/store.py": ('def import_rows(db_path, rows):\n    raise NotImplementedError\n\n'
                            'def summary(db_path, tag=None):\n    raise NotImplementedError\n'),
    "ledgerkit/__main__.py": CLI_STUB,
    "README.md": "# Ledgerkit\nStandard-library ledger importer. Implementation pending.\n",
    ".gitignore": "__pycache__/\n*.pyc\n*.db\n",
}

REFERENCE = {
    "ledgerkit/normalize.py": '''from decimal import Decimal, InvalidOperation
from .contract import ID_FIELD

def normalize(row):
    if not isinstance(row, dict):
        raise ValueError("object required")
    ident, amount, tag = row.get("id"), row.get("amount"), row.get("tag", "")
    if not isinstance(ident, str) or not ident.strip() or not isinstance(tag, str):
        raise ValueError("invalid id/tag")
    if not isinstance(amount, str):
        raise ValueError("amount must be a string")
    try:
        value = Decimal(amount.strip())
        if not value.is_finite():
            raise ValueError("non-finite amount")
        cents = value * 100
        if cents != cents.to_integral_value():
            raise ValueError("fraction of a cent")
        return {ID_FIELD: ident.strip(), "cents": int(cents), "tag": tag.strip()}
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc
''',
    "ledgerkit/csv_reader.py": '''import csv
import io
from .normalize import normalize

def read_csv(text):
    reader = csv.DictReader(io.StringIO(text), strict=True)
    out = []
    try:
        fields = reader.fieldnames
        if not fields or not {"id", "amount"}.issubset(fields) or len(fields) != len(set(fields)):
            raise ValueError("required headers")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("wrong cell count")
            out.append(normalize(row))
    except (ValueError, csv.Error) as exc:
        raise ValueError(f"line {max(1, reader.line_num)}: {exc}") from exc
    return out
''',
    "ledgerkit/jsonl_reader.py": '''import json
from .normalize import normalize

def read_jsonl(text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip():
            try:
                out.append(normalize(json.loads(line)))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"line {n}: {exc}") from exc
    return out
''',
    "ledgerkit/store.py": '''import sqlite3
from .contract import ID_FIELD

def connect(path):
    db = sqlite3.connect(path, timeout=15)
    db.execute("CREATE TABLE IF NOT EXISTS entries (id TEXT PRIMARY KEY, cents INTEGER, tag TEXT)")
    db.commit()
    return db

def import_rows(db_path, rows):
    db = connect(db_path)
    try:
        db.execute("BEGIN IMMEDIATE")
        count = 0
        for row in rows:
            ident, cents, tag = row[ID_FIELD], row["cents"], row["tag"]
            old = db.execute("SELECT cents, tag FROM entries WHERE id=?", (ident,)).fetchone()
            if old is not None:
                if old != (cents, tag):
                    raise ValueError("conflicting duplicate id")
            else:
                db.execute("INSERT INTO entries VALUES (?, ?, ?)", (ident, cents, tag))
                count += 1
        db.commit()
        return count
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

def summary(db_path, tag=None):
    db = connect(db_path)
    try:
        query, args = "SELECT tag, cents FROM entries", ()
        if tag is not None:
            query, args = query + " WHERE tag=?", (tag,)
        rows = db.execute(query, args).fetchall()
        by_tag = {}
        for key, amount in rows:
            by_tag[key] = by_tag.get(key, 0) + amount
        return {"rows": len(rows), "total_cents": sum(a for _, a in rows), "by_tag": by_tag}
    finally:
        db.close()
''',
    "ledgerkit/__main__.py": '''import argparse
import json
import sys
from .csv_reader import read_csv
from .jsonl_reader import read_jsonl
from .store import import_rows, summary

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--format", choices=["csv", "jsonl"], required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--group-tag")
    a = p.parse_args()
    try:
        rows = (read_csv if a.format == "csv" else read_jsonl)(sys.stdin.read())
        import_rows(a.db, rows)
        print(json.dumps(summary(a.db, a.group_tag), sort_keys=True))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''',
}

TINY_SPEC = '''Repair config_flag.parse_flag(value). Accept bool unchanged, exact int
0/1 as False/True, and strings true/false/1/0 (case-insensitive, trimmed).
Reject every other value with ValueError, including other integers, floats and None.
Preserve the function name. Add regression tests; do not commit changes.'''
TINY_REF = '''def parse_flag(value):
    if type(value) is bool:
        return value
    if type(value) is int and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "1", "false", "0"):
            return v in ("true", "1")
    raise ValueError("invalid flag")
'''
REVIEW_SPEC = '''Review and repair allocation.allocate(total, weights) and its
consumer invoice.split_invoice(total, weights). total is a nonnegative exact int,
weights is a nonempty list of nonnegative exact ints with positive sum; bool is
invalid. Reject invalid input with ValueError. Allocate integer cents using the
largest-remainder method: floor each exact quota, then distribute remaining cents
by descending fractional remainder, ties by original index. Never mutate weights.
split_invoice returns {"allocations": list, "total": sum(allocations)} using the
same contract, not another rounding algorithm. Must work with integers > 2**53.
Add regression tests. Do not commit. Inspect the implementation rather than trusting
its existing comments or the optimistic README.'''
REVIEW_REF = '''def allocate(total, weights):
    if type(total) is not int or total < 0 or not isinstance(weights, list) or not weights:
        raise ValueError("invalid input")
    if any(type(x) is not int or x < 0 for x in weights) or sum(weights) == 0:
        raise ValueError("invalid weights")
    divisor = sum(weights)
    pairs = [divmod(total * w, divisor) for w in weights]
    out = [p[0] for p in pairs]
    order = sorted(range(len(weights)), key=lambda i: (-pairs[i][1], i))
    for i in order[:total - sum(out)]:
        out[i] += 1
    return out
'''


def fixture(task: str) -> dict:
    if task not in TASKS:
        raise ValueError(task)
    if task == "tiny":
        return {"files": {"config_flag.py": "def parse_flag(value):\n    return bool(value)\n"},
                "dirty": {}, "prompts": [TINY_SPEC]}
    if task == "review":
        return {"files": {
            "allocation.py": "# Exact and safe rounding.\ndef allocate(total, weights):\n    return [round(total * w / sum(weights)) for w in weights]\n",
            "invoice.py": "def split_invoice(total, weights):\n    return {\"allocations\": [int(total*w/sum(weights)) for w in weights], \"total\": total}\n",
            "README.md": "# Allocation\nThe current implementation is believed to preserve all cents.\n"},
            "dirty": {}, "prompts": [REVIEW_SPEC]}
    files, dirty, prompts = dict(STUBS), {}, [SPEC]
    if task == "dirty":
        dirty = {"ledgerkit/contract.py": 'ID_FIELD = "event_id"\n',
                 "USER_DRAFT.md": "Customer notes — not part of this task.\nKEEP EXACTLY.\n"}
        prompts[0] += ("\nThe uncommitted contract.py is authoritative. Keep its exact bytes and "
                       "USER_DRAFT.md unchanged. Do not reset or commit user edits. Input still uses id.")
    if task == "stale":
        files["pending/README.md"] = ("Recovered draft from contract v1; not integrated. "
                                      "v1 allowed replacement on conflicting duplicate IDs.\n")
        files["pending/store_v1.py"] = ('def resolve_duplicate(old, new):\n'
                                         '    # Old v1 behavior: replace existing values.\n    return new\n')
        prompts[0] += ("\nThere is a recovered v1 draft in pending/. The current contract above is v2: "
                       "conflicting IDs must never replace existing values. Reuse only applicable work.")
    if task == "handoff":
        prompts = [SPEC + ("\nThis is stage 1 of 2. Implement and validate only normalization, both parsers "
                          "and store. Leave ledgerkit/__main__.py EXACTLY unchanged. Do not implement the "
                          "CLI early. Stage 2 will use a fresh process with the same filesystem but no chat "
                          "history, and must implement the full CLI contract above, including --group-tag. "
                          "Preserve whatever project-local facts it will need. Stop after stage 1."),
                   "Continue with stage 2 agreed previously. Use the surviving project artifacts."]
    return {"files": files, "dirty": dirty, "prompts": prompts}


def write_files(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


def apply_reference(root: Path, task: str, stage: int) -> None:
    """Fixture selfcheck only; this is NOT a model execution."""
    if task == "tiny":
        write_files(root, {"config_flag.py": TINY_REF})
    elif task == "review":
        write_files(root, {"allocation.py": REVIEW_REF,
                          "invoice.py": 'from allocation import allocate\n\ndef split_invoice(total, weights):\n    a = allocate(total, weights)\n    return {"allocations": a, "total": sum(a)}\n'})
    else:
        files = dict(REFERENCE)
        if task == "handoff" and stage == 1:
            files.pop("ledgerkit/__main__.py")
            files["PROGRESS.md"] = "Stage 1 complete. Stage 2 requirements:\n" + SPEC
        write_files(root, files)


LEDGER_CHECKS = r'''
from ledgerkit.csv_reader import read_csv
from ledgerkit.jsonl_reader import read_jsonl
from ledgerkit.store import import_rows, summary
from ledgerkit.contract import ID_FIELD
import concurrent.futures
import tempfile

expected = [{ID_FIELD: "a", "cents": 123, "tag": "x"},
            {ID_FIELD: "b", "cents": -2, "tag": "y"}]
assert read_csv('id,amount,tag\n a ,1.230,x\nb,-0.02,y\n') == expected
assert read_jsonl('\n{"id":" a ","amount":"1.23","tag":"x"}\n{"id":"b","amount":"-0.02","tag":"y"}\n') == expected
assert read_csv('id,amount,tag\na,1.00,"line1\nline2"\n')[0]["tag"] == "line1\nline2"
assert read_csv('id,amount\na,0\n') == [{ID_FIELD:"a", "cents":0, "tag":""}]
assert read_jsonl('  \n\n') == []
for text, line in [('id,amount\na,0.001\n', 2), ('id,amount\na,1,extra\n', 2),
                   ('id,amount\na\n',2), ('id,tag\na,x\n',1), ('id,amount\na,NaN\n',2)]:
    raises_line(lambda: read_csv(text), line)
for bad in ['[]', '{"id":"","amount":"1"}', '{"id":"x","amount":true}',
            '{"id":"x","amount":1.2}', '{"id":"x","amount":"Infinity"}',
            '{"id":"x","amount":"1.001"}', '{"id":"x","amount":"1","tag":1}', '{']:
    raises_line(lambda: read_jsonl('\n'+bad), 2)
with tempfile.TemporaryDirectory() as td:
    db = str(Path(td) / 'test.sqlite')
    assert import_rows(db, iter(expected)) == 2
    assert import_rows(db, iter(expected)) == 0
    assert summary(db) == {"rows":2,"total_cents":121,"by_tag":{"x":123,"y":-2}}
    assert summary(db,"x") == {"rows":1,"total_cents":123,"by_tag":{"x":123}}
    new = {ID_FIELD:"new", "cents":50, "tag":"z"}
    conflict = {ID_FIELD:"a", "cents":999, "tag":"x"}
    raises(ValueError, lambda: import_rows(db,[new,conflict]))
    assert summary(db)["rows"] == 2
    def broken():
        yield new
        raise RuntimeError("interrupted iterator")
    raises(RuntimeError, lambda: import_rows(db,broken()))
    assert summary(db)["rows"] == 2
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda i: import_rows(db,[{ID_FIELD:f'c{i}',"cents":i,"tag":"z"}]), range(12)))
    assert results == [1]*12
    assert summary(db)["rows"] == 14
if final_stage:
    with tempfile.TemporaryDirectory() as td:
        db = str(Path(td)/'cli.sqlite')
        def cli(text, fmt='jsonl', extra=()):
            return subprocess.run([sys.executable,'-m','ledgerkit','--format',fmt,'--db',db,*extra],
                                  input=text,text=True,capture_output=True,timeout=15)
        q=cli('id,amount,tag\na,1.23,x\nb,-0.02,y\n','csv', ['--group-tag','x'])
        assert q.returncode == 0, q.stderr
        assert json.loads(q.stdout) == {"rows":1,"total_cents":123,"by_tag":{"x":123}}
        q=cli('{"id":"new","amount":"9","tag":"z"}\n{"id":"a","amount":"8","tag":"x"}')
        assert q.returncode != 0 and q.stderr.strip() and not q.stdout.strip()
        assert summary(db)["rows"] == 2
        q=cli('{"id":"new","amount":"9","tag":"z"}\n{broken')
        assert q.returncode != 0 and 'line 2' in q.stderr and not q.stdout.strip()
        assert summary(db)["rows"] == 2
'''
TINY_CHECKS = '''from config_flag import parse_flag
for x,y in [(True,True),(False,False),(1,True),(0,False),(" TRUE ",True),("false",False),("0",False),("1",True)]:
    assert parse_flag(x) is y
for x in [None,2,-1,0.0,1.0,"yes","",[],{}]:
    raises(ValueError,lambda: parse_flag(x))
'''
REVIEW_CHECKS = '''from allocation import allocate
from invoice import split_invoice
import random

def oracle(t,w):
    den=sum(w)
    q=[t*x//den for x in w]
    order=sorted(range(len(w)),key=lambda i:(-(t*w[i]%den),i))
    for i in order[:t-sum(q)]: q[i]+=1
    return q
rng=random.Random(61026)
for t,w in [(1,[1,1,1]),(2,[1,1,1]),(10,[0,1,1]),(2**60+17,[3,7,9])]+[(rng.randrange(10**18),[rng.randrange(1,100) for _ in range(7)]) for _ in range(100)]:
    before=w[:]
    answer=oracle(t,w)
    assert allocate(t,w)==answer and w==before
    assert split_invoice(t,w)=={"allocations":answer,"total":t}
for t,w in [(True,[1]),(-1,[1]),(1.0,[1]),(1,[]),(1,[0,0]),(1,[True]),(1,[-1,2]),(1,[1.0])]:
    raises(ValueError,lambda: allocate(t,w))
    raises(ValueError,lambda: split_invoice(t,w))
'''


def grade(workspace: Path, task: str, stage: int) -> dict:
    """Run assertions in a NEW interpreter, outside the model execution phase."""
    final_stage = task != "handoff" or stage == 2
    checks = TINY_CHECKS if task == "tiny" else REVIEW_CHECKS if task == "review" else LEDGER_CHECKS
    script = '''import sys,json,subprocess,traceback
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
def raises(cls, fn):
    try: fn()
    except cls: return
    raise AssertionError("expected " + cls.__name__)
def raises_line(fn,n):
    try: fn()
    except ValueError as exc:
        assert "line " + str(n) in str(exc), str(exc)
        return
    raise AssertionError("expected ValueError with physical line")
'''
    script += f'final_stage={final_stage!r}\n' + checks
    if task == "dirty":
        for p, body in fixture(task)["dirty"].items():
            script += f'assert Path({p!r}).read_bytes() == {body.encode()!r}, "user input modified"\n'
    if task == "handoff" and stage == 1:
        script += f'assert Path("ledgerkit/__main__.py").read_bytes() == {CLI_STUB.encode()!r}, "stage scope violation"\n'
    script += 'print("BASELINE_GRADER_OK")\n'
    # No user credentials or provider tokens are passed to grading subprocesses.
    import os
    clean_env = {k: v for k, v in os.environ.items()
                 if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "LANG")}
    clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        p = subprocess.run([sys.executable, "-I", "-c", script], cwd=workspace,
                           capture_output=True, text=True, timeout=60, env=clean_env)
        return {"passed": p.returncode == 0 and p.stdout.rstrip().endswith("BASELINE_GRADER_OK"), "returncode": p.returncode,
                "stdout": p.stdout[-8000:], "stderr": p.stderr[-8000:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "returncode": 124, "stderr": "grader timeout"}
