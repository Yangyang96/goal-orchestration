#!/usr/bin/env python3
"""Two fresh-process waves over the same worktree; keeps first-wave evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

from run import execute, freeze, prepare


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--options', type=Path, required=True)
    p.add_argument('--after', type=Path)
    a = p.parse_args()
    # Wait for the first cohort so inference concurrency remains two.
    while a.after and not a.after.exists():
        time.sleep(10)
    a.output.mkdir(parents=True, exist_ok=True)
    frozen = freeze(a.output)
    options = json.loads(a.options.read_text())
    (a.output / 'options.json').write_text(json.dumps(options, indent=2))
    rng = random.Random(20260908)
    schedule = []
    for repeat in [1, 2]:
        variants = ['native', 'old', 'new']
        rng.shuffle(variants)
        schedule.extend(('handoff', v, repeat) for v in variants)
    (a.output / 'schedule.json').write_text(json.dumps(schedule, indent=2))
    jobs = [prepare(a.output, frozen, *item, i) for i, item in enumerate(schedule, 1)]

    def waves(job):
        run_dir, fixture, initial = job
        first = execute(job, options, 360, validator_name='validate_phase1.py')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        try:
            full = subprocess.run([sys.executable, str(fixture / 'validate.py'), initial['workspace']], capture_output=True, text=True, env=env, timeout=45)
            early = json.loads(full.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            early = {'error': str(exc)}
        (run_dir / 'phase1_full_validation.json').write_text(json.dumps(early, indent=2))
        shutil.copytree(initial['workspace'], run_dir / 'phase1_snapshot', ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        second_dir = a.output / 'runs' / (run_dir.name + '-wave2')
        second_dir.mkdir()
        original_prompt = (run_dir / 'prompt.txt').read_text()
        prompt = original_prompt.rsplit('用户请求：\n', 1)[0] + '用户请求：\n' + (fixture / 'prompt2.txt').read_text()
        (second_dir / 'prompt.txt').write_text(prompt)
        second_meta = dict(initial, run_id=second_dir.name, wave=2, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
        # Only task identity/base are carried in runner metadata; no history is supplied to Codex.
        for key in ['accepted','validation','usage','commands','failed_commands','elapsed_seconds','started_at','returncode','timed_out','runtime_errors','validation_returncode','final_status','commits_added']:
            second_meta.pop(key,None)
        second = execute((second_dir, fixture, second_meta), options, 360)
        return {'task': 'handoff', 'variant': initial['variant'], 'repeat': initial['repeat'],
                'phase1': first, 'phase2': second, 'phase1_full_validation': early}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(waves, jobs))
    (a.output / 'results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
