#!/usr/bin/env python3
"""A/B/C Codex pilot. Offline selfchecks and planned samples are NOT model results."""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time

import fixtures
import telemetry

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKILL_FILES = ('SKILL.md', 'references/coordination.md', 'references/state.md', 'agents/openai.yaml')
HINT = '必要时可将独立工作交给子 Agent，以收益是否超过协调开销为准。\n\n'
COMMON = ('Complete the task. Correctness and preserving user edits come first; avoid unnecessary '
          'token use and elapsed time. Use the assigned model/effort for all agents. Use only the '
          'task workspace, its local temporary worktrees, and supplied references. Do not read '
          'other trials, controller code, hidden graders, reference solutions or global skills. '
          'Do not use external apps or launch nested Codex clients. Respect platform permissions.\n\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.PIPE).strip()


def schedule(tasks, repeats, seed):
    if repeats < 1 or not tasks or len(set(tasks)) != len(tasks) or set(tasks) - set(fixtures.TASKS):
        raise ValueError('invalid task/repeat selection')
    rng = random.Random(seed)
    orders = {t: rng.sample(list('ABC'), 3) for t in tasks}
    jobs = []
    for repeat in range(1, repeats + 1):
        for task in rng.sample(tasks, len(tasks)):
            order, offset = orders[task], (repeat - 1) % 3
            for arm in order[offset:] + order[:offset]:
                jobs.append(dict(run_id=f'{len(jobs)+1:03d}', task=task, arm=arm, repeat=repeat))
    return jobs


def plan(out, skill, tasks, repeats, seed, model, effort, timeout):
    if out.exists() or out.resolve().is_relative_to(REPO):
        raise ValueError('Use a NEW output directory outside this repository')
    if timeout <= 0:
        raise ValueError('timeout must be positive')
    for name in SKILL_FILES:
        if not (skill/name).is_file():
            raise ValueError('Missing skill file: ' + name)
    jobs = schedule(tasks, repeats, seed)
    out.mkdir(parents=True)
    for name in SKILL_FILES:
        dest = out/'frozen/skill'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(skill/name, dest)
    for name in ('runner.py', 'fixtures.py', 'telemetry.py'):
        shutil.copyfile(HERE/name, out/'frozen'/name)
    m = dict(schema='goal-baseline-v2', status='PLANNED_NOT_EXECUTED',
             created_at=datetime.now(timezone.utc).isoformat(), model=model, effort=effort,
             timeout=timeout, seed=seed, repeats=repeats, tasks=tasks, jobs=jobs,
             cases=len(jobs), parent_invocations=sum(len(fixtures.fixture(j['task'])['prompts']) for j in jobs),
             preference='Correctness first; report token/latency tradeoffs, no composite winner',
             hashes={str(p.relative_to(out)): digest(p) for p in sorted((out/'frozen').rglob('*')) if p.is_file()})
    save(out/'manifest.json', m)
    return m


def verify(out, m):
    for rel, wanted in m['hashes'].items():
        if digest(out/rel) != wanted:
            raise ValueError('Frozen input changed: ' + rel)
    for name in ('runner.py', 'fixtures.py', 'telemetry.py'):
        if digest(HERE/name) != m['hashes']['frozen/'+name]:
            raise ValueError('Runner differs from frozen campaign; create a new campaign')


def prompt(arm, request, supplied=None):
    if arm not in 'ABC' or len(arm) != 1:
        raise ValueError('invalid arm')
    extra = HINT if arm == 'B' else ''
    if arm == 'C':
        if supplied is None:
            raise ValueError('C requires the frozen skill')
        extra = ('Use $goal-orchestration. Only this frozen version is supplied. Resolve references from '
                 + str(supplied.resolve()) + '.\n<skill>\n'
                 + (supplied/'SKILL.md').read_text(encoding='utf-8') + '</skill>\n\n')
    return COMMON + extra + 'Task:\n' + request


def prepare(out, job):
    root = out/'runs'/job['run_id']
    if root.exists():
        raise ValueError('Refusing to overwrite a trial')
    workspace = root/'workspace'
    workspace.mkdir(parents=True)
    f = fixtures.fixture(job['task'])
    fixtures.write_files(workspace, f['files'])
    git(workspace, 'init', '-q')
    git(workspace, 'config', 'user.name', 'Baseline Fixture')
    git(workspace, 'config', 'user.email', 'fixture@example.invalid')
    git(workspace, 'add', '.')
    git(workspace, '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Fixture base')
    base = git(workspace, 'rev-parse', 'HEAD')
    (workspace/'.git/info/exclude').write_text('__pycache__/\n*.pyc\n.worktrees/\n')
    fixtures.write_files(workspace, f['dirty'])
    supplied = None
    if job['arm'] == 'C':
        supplied = root/'supplied-skill'
        shutil.copytree(out/'frozen/skill', supplied)
    for n, request in enumerate(f['prompts'], 1):
        p = root/f'phase-{n}'
        p.mkdir()
        (p/'prompt.txt').write_text(prompt(job['arm'], request, supplied), encoding='utf-8')
    r = {**job, 'base': base, 'initial_status': git(workspace, 'status', '--short'),
         'status': 'PREPARED', 'accepted': False, 'phases': []}
    save(root/'result.json', r)
    return root, r


def arguments(binary, m, workspace, final):
    cmd = [binary, 'exec', '--ignore-user-config', '--json', '--sandbox', 'workspace-write',
           '--model', m['model'], '-C', str(workspace), '-o', str(final)]
    settings = {'model_reasoning_effort': m['effort'], 'agents.enabled': True,
                'features.multi_agent': True, 'agents.default_subagent_model': m['model'],
                'agents.default_subagent_reasoning_effort': m['effort'],
                'features.plugins': False, 'features.memories': False}
    for key, value in settings.items():
        cmd += ['-c', key+'='+json.dumps(value)]
    return cmd + ['-']


def preflight(binary='codex', home=None):
    resolved, problems = shutil.which(binary), []
    r = dict(model_calls=0, codex_found=bool(resolved), git_found=bool(shutil.which('git')),
             runtime_delegation_verified=False, all_agent_telemetry_verified=False)
    if not resolved:
        problems.append('CODEX_EXECUTABLE_MISSING')
    if not r['git_found']:
        problems.append('GIT_MISSING')
    if home is None or not home.is_dir():
        problems.append('DEDICATED_AUTHENTICATED_CODEX_HOME_REQUIRED')
    else:
        extra = [name for name in ('AGENTS.md','AGENTS.override.md','skills','agents','hooks.json')
                 if (home/name).is_file() or ((home/name).is_dir() and any((home/name).iterdir()))]
        r['extra_instruction_paths'] = extra
        if extra:
            problems.append('EXTRA_INSTRUCTIONS_IN_DEDICATED_HOME')
    if resolved:
        env = os.environ.copy()
        if home:
            env['CODEX_HOME'] = str(home.resolve())
        try:
            v = subprocess.run([resolved,'--version'], capture_output=True, text=True, env=env, timeout=15)
            h = subprocess.run([resolved,'exec','--help'], capture_output=True, text=True, env=env, timeout=15)
            r['cli_version'] = v.stdout.strip()
            missing = [x for x in ('--json','--ignore-user-config','--sandbox','--model') if x not in h.stdout+h.stderr]
            if v.returncode or h.returncode or missing:
                problems.append('CLI_INTERFACE_MISMATCH')
            r['unsupported_flags'] = missing
            auth = subprocess.run([resolved,'login','status'], capture_output=True, env=env, timeout=15)
            r['authenticated'] = auth.returncode == 0
            if auth.returncode:
                problems.append('AUTHENTICATION_REQUIRED')
            # Never record authentication output or copy credential contents.
        except (OSError, subprocess.TimeoutExpired) as e:
            problems.append(type(e).__name__)
    return {**r, 'problems': problems, 'status': 'BLOCKED' if problems else 'CLI_READY_NOT_RUNTIME_CERTIFIED'}


def stop(p):
    if p.poll() is not None:
        return
    try:
        os.killpg(p.pid, signal.SIGTERM) if os.name == 'posix' else p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL) if os.name == 'posix' else p.kill()
            p.wait()
    except ProcessLookupError:
        pass


def phase(root, job, n, m, binary, home):
    dest, workspace = root/f'phase-{n}', root/'workspace'
    cmd = arguments(binary, m, workspace, dest/'final.txt')
    env = os.environ.copy()
    for name in ('CODEX_APP_TOOLS_PIPE_PATH','CODEX_THREAD_ID','CODEX_SESSION_ID','CODEX_INTERNAL_ORIGINATOR_OVERRIDE'):
        env.pop(name, None)
    env.update(CODEX_HOME=str(home.resolve()), PYTHONDONTWRITEBYTECODE='1')
    r = dict(phase=n, command=cmd, prompt_sha256=digest(dest/'prompt.txt'),
             started_at=datetime.now(timezone.utc).isoformat(), timed_out=False, interrupted=False)
    save(dest/'execution.json', r)
    start = time.monotonic()
    try:
        with (dest/'events.jsonl').open('w') as out, (dest/'stderr.txt').open('w') as err:
            p = subprocess.Popen(cmd, cwd=workspace, env=env, stdin=subprocess.PIPE,
                                 stdout=out, stderr=err, text=True, start_new_session=True)
            try:
                p.communicate((dest/'prompt.txt').read_text(encoding='utf-8'), timeout=m['timeout'])
            except subprocess.TimeoutExpired:
                r['timed_out'] = True
                stop(p)
            except KeyboardInterrupt:
                r['interrupted'] = True
                stop(p)
            r['returncode'] = p.returncode
    except OSError as e:
        r.update(returncode=None, launch_error=str(e))
    r['observed_cli_seconds'] = time.monotonic() - start
    r['cli'] = telemetry.read_events(dest/'events.jsonl')
    save(dest/'execution.json', r)
    r['grade'] = fixtures.grade(workspace, job['task'], n)
    r['accepted'] = r['returncode'] == 0 and not r['timed_out'] and not r['interrupted'] and r['grade']['passed']
    try:
        r['git_status'] = git(workspace, 'status', '--short')
        r['commits_added'] = int(git(workspace, 'rev-list', '--count', job['base']+'..HEAD'))
        r['accepted'] = r['accepted'] and r['commits_added'] == 0
        (dest/'diff.patch').write_text(git(workspace, 'diff', job['base']), encoding='utf-8')
    except subprocess.CalledProcessError as e:
        r.update(git_error=str(e), accepted=False)
    r['artifact_hashes'] = {str(p.relative_to(workspace)): digest(p) for p in workspace.rglob('*')
                            if p.is_file() and not p.is_symlink() and
                            not any(x in p.relative_to(workspace).parts for x in ('.git','__pycache__'))}
    save(dest/'execution.json', r)
    return r


def report(out):
    m = read(out/'manifest.json')
    rows, ownership = [], {}
    for job in m['jobs']:
        root = out/'runs'/job['run_id']
        if not (root/'result.json').exists():
            rows.append({**job, 'status': 'NOT_RUN', 'accepted': None, 'all_agent_tokens': None})
            continue
        result = read(root/'result.json')
        row = {**job, 'status': result['status'], 'accepted': result['accepted'],
               'observed_cli_seconds': sum(p['observed_cli_seconds'] for p in result['phases']),
               'all_agent_tokens': 0, 'usage': []}
        complete, own = len(result['phases']) == len(fixtures.fixture(job['task'])['prompts']), set()
        for p in result['phases']:
            dest = root/f"phase-{p['phase']}"
            binding = dict(run_id=job['run_id'], phase=p['phase'], prompt_sha256=p['prompt_sha256'],
                           events_sha256=digest(dest/'events.jsonl') if (dest/'events.jsonl').exists() else None,
                           root_threads=p['cli']['root_threads'], cli_version=m.get('preflight',{}).get('cli_version'))
            ledger = read(dest/'usage-ledger.json') if (dest/'usage-ledger.json').exists() else None
            u = telemetry.account(ledger, binding, m['model'], m['effort'])
            row['usage'].append(u)
            complete = complete and u['status'] == 'COMPLETE_EXPORTED'
            row['all_agent_tokens'] += u['all_agent_tokens'] or 0
            for rid in u.get('request_ids', []):
                if rid in own:
                    complete = False
                own.add(rid)
        if not complete:
            row['all_agent_tokens'] = None
        for rid in own:
            if rid in ownership:
                ownership[rid]['all_agent_tokens'] = None
                row['all_agent_tokens'] = None
            ownership[rid] = row
        rows.append(row)
    groups = []
    for task in m['tasks']:
        for arm in 'ABC':
            items = [r for r in rows if r['task'] == task and r['arm'] == arm]
            recorded = [r for r in items if r['status'] != 'NOT_RUN']
            times = [r['observed_cli_seconds'] for r in recorded]
            tokens = [r['all_agent_tokens'] for r in recorded if r['all_agent_tokens'] is not None]
            groups.append(dict(task=task, arm=arm, scheduled=len(items), recorded=len(recorded),
                               passed=sum(r['accepted'] is True for r in recorded),
                               median_cli_seconds=statistics.median(times) if times else None,
                               median_all_agent_tokens=statistics.median(tokens) if len(tokens)==len(items) else None))
    r = dict(schema='goal-comparison-v2', status=m['status'], cases_scheduled=m['cases'],
             cases_recorded=sum(r['status'] != 'NOT_RUN' for r in rows), groups=groups, trials=rows,
             performance_verdict='NOT_ESTABLISHED',
             limitations=['Runtime equivalence and all-thread completion need independent trace review.',
                          'Null tokens are unknown, not zero. CLI time is not certified all-agent wall time.',
                          'Mechanical acceptance is not a full quality/scope audit. Small pilot, no significance claim.'])
    save(out/'comparison.json', r)
    return r


def run(out, binary, home):
    m = read(out/'manifest.json')
    verify(out, m)
    pf = preflight(binary, home)
    save(out/'preflight.json', pf)
    if pf['problems']:
        return {'status': 'BLOCKED', 'model_calls': 0, 'preflight': pf}
    if (out/'runs').exists():
        raise ValueError('Campaign already started; preserve evidence and use a new campaign')
    m.update(status='RUNNING', preflight=pf)
    save(out/'manifest.json', m)
    interrupted = False
    for job in m['jobs']:
        verify(out, m)
        root, result = prepare(out, job)
        result['status'] = 'RUNNING'
        save(root/'result.json', result)
        for n in range(1, len(fixtures.fixture(job['task'])['prompts'])+1):
            p = phase(root, result, n, m, binary, home)
            result['phases'].append(p)
            save(root/'result.json', result)
            if p['interrupted'] or p['timed_out'] or p['returncode'] != 0:
                interrupted = p['interrupted']
                break
        result['accepted'] = (len(result['phases']) == len(fixtures.fixture(job['task'])['prompts'])
                              and all(p['accepted'] for p in result['phases']))
        result['status'] = 'INTERRUPTED' if interrupted else 'FINISHED'
        save(root/'result.json', result)
        print(json.dumps({k:result[k] for k in ('run_id','status','accepted')}), flush=True)
        if interrupted:
            break
    m['status'] = 'INTERRUPTED' if interrupted else 'EXECUTIONS_FINISHED_REVIEW_REQUIRED'
    save(out/'manifest.json', m)
    return report(out)


def selfcheck():
    checks = []
    for task in fixtures.TASKS:
        with tempfile.TemporaryDirectory(prefix='goal-fixture-') as d:
            root, f = Path(d), fixtures.fixture(task)
            fixtures.write_files(root, f['files'])
            fixtures.write_files(root, f['dirty'])
            if fixtures.grade(root, task, 1)['passed']:
                raise AssertionError('Broken fixture passed: ' + task)
            for n in range(1, len(f['prompts'])+1):
                fixtures.apply_reference(root, task, n)
                g = fixtures.grade(root, task, n)
                if not g['passed']:
                    raise AssertionError(task + ': ' + g['stderr'])
                checks.append(dict(task=task, phase=n, reference_passed=True))
    return dict(type='OFFLINE_SELFCHECK_NOT_MODEL_EXECUTION', model_calls=0,
                broken_cases_rejected=len(fixtures.TASKS), reference_checks=checks, passed=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    q = sub.add_parser('plan')
    q.add_argument('--output', type=Path, required=True)
    q.add_argument('--skill', type=Path, default=REPO/'skills/goal-orchestration')
    q.add_argument('--tasks', nargs='+', choices=fixtures.TASKS, default=list(fixtures.TASKS))
    q.add_argument('--repeats', type=int, default=3)
    q.add_argument('--seed', type=int, default=20260916)
    q.add_argument('--model', default='gpt-6-astra')
    q.add_argument('--effort', choices=('low','medium','high','xhigh','max'), default='xhigh')
    q.add_argument('--timeout', type=int, default=900)
    for name in ('preflight','run'):
        q = sub.add_parser(name)
        q.add_argument('--codex', default='codex')
        q.add_argument('--codex-home', type=Path)
        if name == 'run':
            q.add_argument('--output', type=Path, required=True)
    q = sub.add_parser('report')
    q.add_argument('--output', type=Path, required=True)
    sub.add_parser('selfcheck')
    a = p.parse_args()
    try:
        if a.action == 'plan':
            r = plan(a.output.resolve(), a.skill.resolve(), a.tasks, a.repeats, a.seed, a.model, a.effort, a.timeout)
        elif a.action == 'preflight':
            r = preflight(a.codex, a.codex_home)
        elif a.action == 'run':
            r = run(a.output.resolve(), a.codex, a.codex_home)
        elif a.action == 'report':
            r = report(a.output.resolve())
        else:
            r = selfcheck()
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 2 if r.get('status') == 'BLOCKED' else 0
    except (ValueError, OSError, AssertionError, subprocess.SubprocessError) as e:
        print(json.dumps({'status':'ERROR','reason':str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
