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
    from ledger import summarize, render
except Exception as exc:
    checks['import'] = False
    details['import'] = str(exc)


def normalize():
    equal(summarize('\ufeff customer , amount , status \n  Zed  , 1.25 , PAID \nAda,2, paid\nZed,0.75,paid\n'), {'Ada': 200, 'Zed': 200})


def precise():
    equal(summarize('customer,amount,status\nA,0.145,paid\nA,-0.005,paid\nA,0.005,paid\nB,90071992547409.93,paid\n'), {'A': 15, 'B': 9007199254740993})


def invalid():
    for amount in ('NaN', 'Infinity', '-Infinity', 'oops'):
        raises(ValueError, lambda: summarize('customer,amount,status\nA,1,paid\nB,' + amount + ',paid\n'), 'row 3')
    raises(ValueError, lambda: summarize('customer,amount,status\n"multi\nline",nope,paid\n'), 'row 3')


def compatibility():
    values = summarize('customer,amount,status\nZ, ,paid\nA,not money,open\nB,1.01,paid\n')
    equal(list(values), ['B', 'Z'])
    equal(values, {'B': 101, 'Z': 0})
    equal(render(values), 'B\t101\nZ\t0\n')
    equal(summarize('customer,amount,status\n'), {})


def no_commit():
    r = run('git', 'rev-list', '--count', 'HEAD')
    assert r.returncode == 0, r.stderr
    equal(r.stdout.strip(), '1')

for name, fn in [('normalization', normalize), ('exact_money', precise),
                 ('invalid_amount_row_numbers', invalid), ('legacy_api', compatibility),
                 ('public_tests', public_tests), ('no_unrequested_commit', no_commit)]:
    check(name, fn)

print(json.dumps({'checks': checks, 'details': details}, ensure_ascii=False))
sys.exit(0 if checks and all(checks.values()) else 1)
