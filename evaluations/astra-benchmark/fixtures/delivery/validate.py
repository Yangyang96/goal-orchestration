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


try:
    import routebook
except Exception as exc:
    checks['import'] = False
    details['import'] = str(exc)


def config(path, routes, include=None):
    value = {'routes': routes}
    if include is not None:
        value['include'] = include
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return value


def api():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        config(base / 'deep' / 'base.json', {'health': '/health', 'root': '/old'})
        config(base / 'mid.json', {'root': '/middle'}, 'deep/base.json')
        data = config(base / 'top.json', {'root': '/current', 'login': '/login'}, 'mid.json')
        expected = {'health': '/health', 'root': '/current', 'login': '/login'}
        equal(routebook.load_routes(base / 'top.json'), expected)
        equal(routebook.load_routes(str(base / 'top.json')), expected)
        equal(routebook.load_routes_text(json.dumps(data), base_dir=base), expected)
        config(base / 'simple.json', {'x': '/x'})
        equal(routebook.load_routes(base / 'simple.json'), {'x': '/x'})
        config(base / 'nested' / 'same.json', {'a': 'a'})
        config(base / 'same.json', {'b': 'b'}, 'nested/same.json')
        equal(routebook.load_routes(base / 'same.json'), {'a': 'a', 'b': 'b'})


def errors():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        config(base / 'a.json', {}, 'b.json')
        config(base / 'b.json', {}, './a.json')
        raises(ValueError, lambda: routebook.load_routes(base / 'a.json'), 'cycle')
        raises(FileNotFoundError, lambda: routebook.load_routes_text('{"include":"missing.json","routes":{}}', base_dir=base))
        for data in ([], {}, {'routes': []}, {'routes': {'x': 42}},
                     {'routes': {}, 'include': 8}, {'routes': {}, 'include': ''}):
            raises(ValueError, lambda: routebook.load_routes_text(json.dumps(data), base_dir=base))
        raises(ValueError, lambda: routebook.load_routes_text('{broken', base_dir=base))


def cli():
    # Use a temporary config directory while exposing only the candidate package.
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        config(base / 'base.json', {'base': '/b'})
        data = config(base / 'main.json', {'main': '/m'}, 'base.json')
        env = dict(os.environ, PYTHONPATH=str(workspace))
        def call(*args, input=None):
            return subprocess.run([sys.executable, '-m', 'routebook', *args],
                                  cwd=base, env=env, input=input, text=True,
                                  capture_output=True, timeout=15)
        for args, stdin in [(('main.json',), None), (('--stdin',), json.dumps(data))]:
            r = call(*args, input=stdin)
            equal(r.returncode, 0)
            equal(json.loads(r.stdout), {'base': '/b', 'main': '/m'})
        equal(call().returncode, 2)
        equal(call('--stdin', 'main.json', input='{"routes":{}}').returncode, 2)


def commit_count():
    result = run('git', 'rev-list', '--count', 'HEAD')
    equal(result.returncode, 0)
    equal(result.stdout.strip(), '2')


def user_notes():
    expected_dirty = '# Personal notes\n\nKeep this file out of implementation commits.\n\n用户草稿：下周再讨论 route ownership。\nDo not rewrite this sentence.\n'
    equal((workspace / 'NOTES.md').read_text(), expected_dirty)

def git_delivery():
    def git(*args):
        r = run('git', *args)
        assert r.returncode == 0, r.stderr
        return r.stdout
    equal(git('show', 'HEAD:NOTES.md'), '# Personal notes\n\nKeep this file out of implementation commits.\n')
    equal(git('show', 'HEAD~:NOTES.md'), git('show', 'HEAD:NOTES.md'))
    changed = set(git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines())
    assert 'NOTES.md' not in changed, changed
    assert {'routebook/core.py', 'routebook/__init__.py', 'routebook/__main__.py', 'README.md'} <= changed, changed
    assert any(p.startswith('test') and p.endswith('.py') for p in changed), changed
    allowed = lambda p: p.startswith('routebook/') or (p.startswith('test') and p.endswith('.py')) or p in {'README.md', '.gitignore'}
    assert all(allowed(p) for p in changed), changed
    equal(git('diff', '--cached', '--name-only'), '')
    equal(git('diff', '--name-only').splitlines(), ['NOTES.md'])
    untracked = git('ls-files', '--others', '--exclude-standard').splitlines()
    equal(untracked, [])

for name, fn in [('public_api_and_nested_include', api), ('validation_and_cycle_errors', errors),
                 ('stdin_and_legacy_cli', cli), ('public_tests', public_tests),
                 ('one_local_commit', commit_count), ('user_dirty_content_preserved', user_notes),
                 ('commit_scope_and_dirty_ownership', git_delivery)]:
    check(name, fn)

print(json.dumps({'checks': checks, 'details': details}, ensure_ascii=False))
sys.exit(0 if checks and all(checks.values()) else 1)
