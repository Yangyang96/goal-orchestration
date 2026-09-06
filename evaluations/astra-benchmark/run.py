#!/usr/bin/env python3
"""Run a frozen three-arm coding pilot; never modifies the installed skill/config."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(workspace, *args):
    return subprocess.check_output(['git', '-C', str(workspace), *args], text=True).strip()


def freeze(root):
    target = root / 'frozen'
    if target.exists():
        raise RuntimeError('Refusing to replace a frozen campaign')
    shutil.copytree(HERE / 'fixtures', target / 'fixtures')
    for variant in ['old', 'new']:
        for relative in ['SKILL.md', 'references/state.md', 'references/coordination.md']:
            dest = target / 'skills' / variant / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            source = 'skills/goal-orchestration/' + relative
            content = (subprocess.check_output(['git', 'show', '7845565:' + source], cwd=REPO)
                       if variant == 'old' else (REPO / source).read_bytes())
            dest.write_bytes(content)
    hashes = {str(p.relative_to(target)): digest(p) for p in sorted(target.rglob('*')) if p.is_file()}
    (root / 'hashes.json').write_text(json.dumps(hashes, indent=2))
    return target


def prepare(root, frozen, task, variant, repeat, number):
    manifest = json.loads((frozen / 'fixtures' / task / 'manifest.json').read_text())
    run_dir = root / 'runs' / f'{number:02d}-{task}-{variant}-r{repeat}'
    workspace = run_dir / 'workspace'
    fixture = frozen / 'fixtures' / task
    shutil.copytree(fixture / manifest['source'], workspace)
    git(workspace, 'init', '-q')
    git(workspace, 'config', 'user.name', 'Benchmark Fixture')
    git(workspace, 'config', 'user.email', 'benchmark@example.invalid')
    (workspace / '.git' / 'info' / 'exclude').write_text('__pycache__/\n*.pyc\n')
    git(workspace, 'add', '.')
    git(workspace, 'commit', '-qm', 'Initial fixture')
    base = git(workspace, 'rev-parse', 'HEAD')
    for path, content in manifest['dirty_files'].items():
        dest = workspace / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
    request = (fixture / manifest['prompt']).read_text()
    common = ('只在当前工作目录中完成下述真实代码任务。其他目录有独立工作，不能修改。'
              '不要读取工作目录之外的项目、测试判卷器、其他候选结果或全局 Skill。'
              '本任务只允许使用当前提供的 Skill（如有）；不要委派子 Agent，也不要调用外部应用。'
              '你可以使用本地 shell、文件工具和 Git。遵守现有权限限制。\n\n')
    treatment = ''
    if variant != 'native':
        skill_dir = run_dir / 'supplied-skill'
        shutil.copytree(frozen / 'skills' / variant, skill_dir)
        treatment = ('请使用 $goal-orchestration 完成本任务。以下是本次唯一指定版本；'
                     '必要时可以读取该目录中的引用文件。\n'
                     f'<skill path="{skill_dir / "SKILL.md"}">\n'
                     + (skill_dir / 'SKILL.md').read_text() + '\n</skill>\n\n')
    prompt = common + treatment + '用户请求：\n' + request
    (run_dir / 'prompt.txt').write_text(prompt)
    meta = dict(run_id=run_dir.name, task=task, variant=variant, repeat=repeat,
                workspace=str(workspace), base_commit=base, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                initial_status=git(workspace, 'status', '--short'))
    (run_dir / 'metadata.json').write_text(json.dumps(meta, indent=2))
    return run_dir, fixture, meta


def execute(job, options, timeout, validator_name="validate.py"):
    run_dir, fixture, meta = job
    workspace = Path(meta['workspace'])
    env = os.environ.copy()
    for key in ['CODEX_APP_TOOLS_PIPE_PATH', 'CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CODEX_INTERNAL_ORIGINATOR_OVERRIDE']:
        env.pop(key, None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    cmd = ['codex', 'exec', *options, '-C', str(workspace), '-o', str(run_dir / 'final.txt'), '-']
    start = time.monotonic()
    meta['started_at'] = datetime.now(timezone.utc).isoformat()
    (run_dir / 'metadata.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({'event': 'start', 'run': meta['run_id']}), flush=True)
    with (run_dir / 'events.jsonl').open('w') as out, (run_dir / 'stderr.txt').open('w') as err:
        p = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True, start_new_session=True)
        try:
            p.communicate((run_dir / 'prompt.txt').read_text(), timeout=timeout)
            meta['timed_out'] = False
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
            meta['timed_out'] = True
    meta['returncode'] = p.returncode
    meta['elapsed_seconds'] = round(time.monotonic() - start, 3)
    events = []
    for line in (run_dir / 'events.jsonl').read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    meta['usage'] = next((e.get('usage') for e in reversed(events) if e['type'] == 'turn.completed'), None)
    commands = [e['item'] for e in events if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution']
    meta['commands'] = len(commands)
    meta['failed_commands'] = sum(c.get('exit_code') not in (0, None) for c in commands)
    meta['runtime_errors'] = [e.get('message', e.get('item', {}).get('message')) for e in events
                              if e.get('type') == 'error' or e.get('item', {}).get('type') == 'error']
    # Persist execution evidence even when the grader or Git inspection fails.
    (run_dir / 'metadata.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    try:
        validation = subprocess.run([sys.executable, str(fixture / validator_name), str(workspace)], capture_output=True, text=True, env=env, timeout=45)
        (run_dir / 'validation.json').write_text(validation.stdout)
        (run_dir / 'validation.stderr').write_text(validation.stderr)
        meta['validation_returncode'] = validation.returncode
        try:
            meta['validation'] = json.loads(validation.stdout)
        except json.JSONDecodeError:
            meta['validation'] = {'error': validation.stdout[-2000:]}
    except subprocess.TimeoutExpired:
        meta['validation_returncode'] = 124
        meta['validation'] = {'checks': {'grader_finished': False}, 'details': {'grader_finished': 'Grader timed out after 45 seconds'}}
    meta['accepted'] = meta['validation_returncode'] == 0 and p.returncode == 0 and not meta['timed_out']
    try:
        meta['final_status'] = git(workspace, 'status', '--short')
        meta['commits_added'] = int(git(workspace, 'rev-list', '--count', meta['base_commit'] + '..HEAD'))
        (run_dir / 'diff.patch').write_text(git(workspace, 'diff', meta['base_commit']))
        (run_dir / 'commits.txt').write_text(git(workspace, 'log', '--format=%h %s', meta['base_commit'] + '..HEAD'))
    except subprocess.CalledProcessError as exc:
        meta['git_inspection_error'] = str(exc)
        meta['accepted'] = False
    (run_dir / 'metadata.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({'event': 'done', 'run': meta['run_id'], 'accepted': meta['accepted'], 'seconds': meta['elapsed_seconds'], 'usage': meta['usage']}), flush=True)
    return meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--options', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=360)
    parser.add_argument('--tasks', nargs='+', default=['ordinary', 'delivery', 'recovery'])
    parser.add_argument('--after', type=Path)
    args = parser.parse_args()
    while args.after and not args.after.exists():
        time.sleep(10)
    args.output.mkdir(parents=True, exist_ok=True)
    frozen = freeze(args.output)
    options = json.loads(args.options.read_text())
    (args.output / 'options.json').write_text(json.dumps(options, indent=2))
    rng = random.Random(20260907)
    schedule = []
    for repeat in [1, 2]:
        for task in args.tasks:
            variants = ['native', 'old', 'new']
            rng.shuffle(variants)
            schedule.extend((task, variant, repeat) for variant in variants)
    (args.output / 'schedule.json').write_text(json.dumps(schedule, indent=2))
    jobs = [prepare(args.output, frozen, *item, i) for i, item in enumerate(schedule, 1)]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda job: execute(job, options, args.timeout), jobs))
    (args.output / 'results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
