#!/usr/bin/env python3
"""Combine the preregistered cohorts without counting blocked delivery twice.

Acceptance here is mechanical. The report adds independent behavior review,
including whether handoff wave 1 stayed within its requested scope.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import tomllib

VARIANTS = ['native', 'old', 'new']
TASKS = ['ordinary', 'delivery', 'recovery']


def check_cohort(name, rows):
    tasks = TASKS if name == 'campaign' else ['handoff' if name == 'handoff' else 'delivery']
    expected = Counter((task, variant, repeat) for task in tasks for variant in VARIANTS for repeat in [1, 2])
    actual = Counter((row['task'], row['variant'], row['repeat']) for row in rows)
    if actual != expected:
        raise ValueError(f'{name}: missing/duplicate/unexpected cases: {actual - expected}, {expected - actual}')
    runs = []
    for row in rows:
        if name == 'handoff':
            first, second = row['phase1'], row['phase2']
            key = (row['task'], row['variant'], row['repeat'])
            for phase in [first, second]:
                if (phase['task'], phase['variant'], phase['repeat']) != key:
                    raise ValueError('Handoff phase identity differs from pair')
            if second['run_id'] != first['run_id'] + '-wave2' or second.get('wave') != 2:
                raise ValueError('Handoff phase IDs do not match')
            if first['workspace'] != second['workspace'] or first['base_commit'] != second['base_commit']:
                raise ValueError('Handoff phases do not share the original workspace/base')
            runs.extend([first, second])
        else:
            runs.append(row)
    if len({run['run_id'] for run in runs}) != len(runs):
        raise ValueError(f'{name}: duplicate run IDs')
    for run in runs:
        if not isinstance(run.get('accepted'), bool):
            raise ValueError(f'{name}: unfinished run {run["run_id"]}')


def normalize_options(options, corrected=False):
    flags, config = {}, {}
    iterator = iter(options)
    for option in iterator:
        if option == '-c':
            key, value = next(iterator).split('=', 1)
            if key in config:
                raise ValueError(f'Duplicate config option: {key}')
            config[key] = tomllib.loads('value=' + value)['value']
        elif option in ['--model', '--sandbox']:
            flags[option] = next(iterator)
        else:
            flags[option] = True
    if flags.get('--model') != 'gpt-6-astra' or config.get('model_reasoning_effort') != 'xhigh':
        raise ValueError('Unexpected model or reasoning effort')
    if corrected:
        if flags.pop('--approve-for-me', None) is not True or '--sandbox' in flags:
            raise ValueError('Corrected delivery does not use the declared approval mode')
        flags['--sandbox'] = 'workspace-write'
    elif '--approve-for-me' in flags or flags.get('--sandbox') != 'workspace-write':
        raise ValueError('Unexpected base sandbox/approval mode')
    for key in ['log_dir', 'sqlite_home']:
        config.pop(key, None)
    return flags, config


def verify_inputs(root, names):
    hashes = {}
    for name in names:
        folder = root / name
        hashes[name] = json.loads((folder / 'hashes.json').read_text())
        required = {f'skills/{v}/{path}' for v in ['old', 'new']
                    for path in ['SKILL.md', 'references/state.md', 'references/coordination.md']}
        required_tasks = TASKS + ([] if name == 'campaign' else ['handoff'])
        for task in required_tasks:
            required.update(f'fixtures/{task}/{p}' for p in ['manifest.json', 'validate.py'])
            required.add(f'fixtures/{task}/prompt1.txt' if task == 'handoff' else f'fixtures/{task}/prompt.txt')
            manifest = json.loads((folder / 'frozen/fixtures' / task / 'manifest.json').read_text())
            required.update(f'fixtures/{task}/{manifest["source"]}/{p}' for p in ['README.md'])
            if task == 'handoff':
                required.update(['fixtures/handoff/prompt2.txt', 'fixtures/handoff/validate_phase1.py'])
        if not required <= hashes[name].keys():
            raise ValueError(f'{name}: missing required frozen inputs {required - hashes[name].keys()}')
        actual_paths = {str(path.relative_to(folder / 'frozen')) for path in (folder / 'frozen').rglob('*') if path.is_file()}
        if actual_paths != hashes[name].keys():
            raise ValueError(f'{name}: frozen file set differs from manifest')
        for path, expected in hashes[name].items():
            if hashlib.sha256((folder / 'frozen' / path).read_bytes()).hexdigest() != expected:
                raise ValueError(f'{name}: changed frozen input {path}')
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            for path in hashes[first].keys() & hashes[second].keys():
                if hashes[first][path] != hashes[second][path]:
                    raise ValueError(f'{first}/{second}: differing frozen input {path}')
            for prefix in ['skills/'] + [f'fixtures/{task}/' for task in TASKS]:
                if {p for p in hashes[first] if p.startswith(prefix)} != {p for p in hashes[second] if p.startswith(prefix)}:
                    raise ValueError(f'{first}/{second}: differing required file sets under {prefix}')
    shared_handoff = [{p for p in hashes[name] if p.startswith('fixtures/handoff/')} for name in ['handoff', 'delivery-corrected']]
    if shared_handoff[0] != shared_handoff[1]:
        raise ValueError('Later cohorts have different handoff input sets')
    options = [normalize_options(json.loads((root / name / 'options.json').read_text()), name == 'delivery-corrected') for name in names]
    if any(option != options[0] for option in options[1:]):
        raise ValueError('Undeclared CLI option difference between cohorts')


def summarize(cases):
    runs = [run for case in cases for run in case['runs']]
    usage_complete = all(run.get('usage') is not None for run in runs)
    cache_complete = usage_complete and all('cached_input_tokens' in run['usage'] for run in runs)
    case_seconds = [sum(run['elapsed_seconds'] for run in case['runs']) for case in cases]
    return {
        'cases': len(cases),
        'mechanically_accepted_cases': sum(case['accepted'] for case in cases),
        'invocations': len(runs),
        'cumulative_seconds': round(sum(run['elapsed_seconds'] for run in runs), 3),
        'median_case_seconds': round(statistics.median(case_seconds), 3),
        'usage_complete': usage_complete,
        'input_plus_output_tokens': sum(run['usage']['input_tokens'] + run['usage']['output_tokens'] for run in runs) if usage_complete else None,
        'cached_input_tokens_subset': sum(run['usage']['cached_input_tokens'] for run in runs) if cache_complete else None,
        'uncached_input_tokens': sum(run['usage']['input_tokens'] - run['usage']['cached_input_tokens'] for run in runs) if cache_complete else None,
        'output_tokens': sum(run['usage']['output_tokens'] for run in runs) if usage_complete else None,
        'commands': sum(run['commands'] for run in runs),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path, help='Contains campaign, handoff, delivery-corrected')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cohorts = {name: json.loads((args.root / name / 'results.json').read_text())
               for name in ['campaign', 'handoff', 'delivery-corrected']}
    for name, rows in cohorts.items():
        check_cohort(name, rows)
    verify_inputs(args.root, list(cohorts))
    cases = []
    blocked = []
    for name in ['campaign', 'delivery-corrected']:
        for run in cohorts[name]:
            if name == 'campaign' and run['task'] == 'delivery':
                blocked.append(run)
                continue
            cases.append({'task': run['task'], 'variant': run['variant'], 'repeat': run['repeat'],
                          'accepted': run['accepted'], 'runs': [run]})
    for pair in cohorts['handoff']:
        cases.append({'task': 'handoff', 'variant': pair['variant'], 'repeat': pair['repeat'],
                      'accepted': pair['phase1']['accepted'] and pair['phase2']['accepted'],
                      'runs': [pair['phase1'], pair['phase2']],
                      'phase1_full_validation': pair['phase1_full_validation']})
    by_variant, by_task = defaultdict(list), defaultdict(list)
    for case in cases:
        by_variant[case['variant']].append(case)
        by_task[(case['task'], case['variant'])].append(case)
    paired = []
    indexed = {(case['task'], case['repeat'], case['variant']): case for case in cases}
    for task, repeat in sorted({(case['task'], case['repeat']) for case in cases}):
        revised = summarize([indexed[(task, repeat, 'new')]])
        for baseline in ['native', 'old']:
            prior = summarize([indexed[(task, repeat, baseline)]])
            paired.append({
                'task': task, 'repeat': repeat, 'comparison': 'new_minus_' + baseline,
                'accepted_case_delta': revised['mechanically_accepted_cases'] - prior['mechanically_accepted_cases'],
                'seconds_delta': round(revised['cumulative_seconds'] - prior['cumulative_seconds'], 3),
                'input_plus_output_token_delta': revised['input_plus_output_tokens'] - prior['input_plus_output_tokens']
                if revised['usage_complete'] and prior['usage_complete'] else None,
            })
    result = {
        'scope': 'Mechanical acceptance; consult independent grades for scope and workflow behavior.',
        'frozen_common_inputs_equal': True,
        'primary_groups': {variant: summarize([case for case in items if case['task'] != 'handoff']) for variant, items in sorted(by_variant.items())},
        'handoff_groups': {variant: summarize([case for case in items if case['task'] == 'handoff']) for variant, items in sorted(by_variant.items())},
        'supplementary_all_task_groups': {variant: summarize(items) for variant, items in sorted(by_variant.items())},
        'by_task': {task: {variant: summarize(by_task[(task, variant)]) for variant in sorted(by_variant)}
                    for task in sorted({case['task'] for case in cases})},
        'cases': cases,
        'paired_differences': paired,
        'infrastructure_limited_delivery_runs': blocked,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({key: result[key] for key in ['primary_groups', 'handoff_groups', 'by_task']}, indent=2))


if __name__ == '__main__':
    main()
