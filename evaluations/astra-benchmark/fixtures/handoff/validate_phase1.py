"""Hidden checks; invoke outside the execution model's worktree."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

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


def cli(*args, stdin=None):
    return subprocess.run([sys.executable, '-m', 'notebatch', *args], cwd=workspace,
                          input=stdin, text=True, capture_output=True, timeout=15)


def public_tests():
    p = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v'], cwd=workspace,
                       capture_output=True, text=True, timeout=20)
    assert p.returncode == 0, p.stdout + p.stderr


def normalization():
    from notebatch import normalize_entries, read_entries, render_json
    source = [{'title': '  Inbox  ', 'tags': [' z ', '', 'a', 'z', ' A '], 'ignored': True},
              {'title': '中文'}]
    before = copy.deepcopy(source)
    expected = [{'title': 'Inbox', 'tags': ['A', 'a', 'z']}, {'title': '中文', 'tags': []}]
    equal(normalize_entries(source), expected)
    equal(source, before)
    equal(read_entries(json.dumps(source)), expected)
    equal(json.loads(render_json(expected)), expected)
    equal(normalize_entries([]), [])


def invalid_entries():
    from notebatch import normalize_entries
    for value in ({}, [None], [{}], [{'title': '  '}], [{'title': 2}],
                  [{'title': 'x', 'tags': None}], [{'title': 'x', 'tags': [2]}],
                  [{'title': 'x', 'tags': 'home'}]):
        try:
            normalize_entries(value)
        except ValueError:
            continue
        raise AssertionError(f'expected ValueError for {value!r}')


def legacy_cli():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'notes.json'
        path.write_text('[{"title":"  File note  "}]')
        p = cli(str(path))
        equal(p.returncode, 0)
        equal(json.loads(p.stdout), [{'title': 'File note', 'tags': []}])


def no_commit():
    p = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], cwd=workspace,
                       capture_output=True, text=True, timeout=10)
    equal(p.returncode, 0)
    equal(p.stdout.strip(), '1')

for name, fn in [('normalization_and_nonmutation', normalization),
                 ('input_contract', invalid_entries), ('legacy_file_cli', legacy_cli),
                 ('public_tests', public_tests), ('no_unrequested_commit', no_commit)]:
    check(name, fn)

print(json.dumps({'checks': checks, 'details': details}, ensure_ascii=False))
sys.exit(0 if checks and all(checks.values()) else 1)
