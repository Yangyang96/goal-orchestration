#!/usr/bin/env python3
"""Summarize observed runs, preserving individual failures and paired outcomes."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

p = argparse.ArgumentParser()
p.add_argument('campaign', type=Path)
p.add_argument('--output', type=Path)
a = p.parse_args()
rows = [json.loads(f.read_text()) for f in sorted((a.campaign / 'runs').glob('*/metadata.json'))]
rows = [r for r in rows if 'accepted' in r]
groups = defaultdict(list)
for row in rows:
    groups[row['variant']].append(row)
summary = {}
for variant, items in groups.items():
    usage_complete = all(i.get('usage') is not None for i in items)
    cache_complete = usage_complete and all('cached_input_tokens' in i['usage'] for i in items)
    totals = [i['usage']['input_tokens'] + i['usage']['output_tokens'] for i in items] if usage_complete else []
    summary[variant] = {
        'n': len(items), 'accepted': sum(i['accepted'] for i in items),
        'median_seconds': round(statistics.median(i['elapsed_seconds'] for i in items), 1),
        'cumulative_seconds': round(sum(i['elapsed_seconds'] for i in items), 1),
        'input_plus_output_tokens': sum(totals) if usage_complete else None,
        'cached_input_tokens_subset': sum(i['usage']['cached_input_tokens'] for i in items) if cache_complete else None,
        'uncached_input_tokens': sum(i['usage']['input_tokens'] - i['usage']['cached_input_tokens'] for i in items) if cache_complete else None,
        'output_tokens': sum(i['usage']['output_tokens'] for i in items) if usage_complete else None,
        'median_input_plus_output_tokens': statistics.median(totals) if totals else None,
        'commands': sum(i['commands'] for i in items),
        'failed_commands': sum(i['failed_commands'] for i in items),
        'failures': [{'run': i['run_id'], 'checks': i.get('validation', {}).get('details', {}), 'timed_out': i['timed_out']} for i in items if not i['accepted']],
    }
result = {'completed_runs': len(rows), 'summary': summary, 'runs': rows}
text = json.dumps(result, indent=2, ensure_ascii=False)
if a.output:
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(text)
print(json.dumps({'completed_runs': len(rows), 'summary': summary}, indent=2, ensure_ascii=False))
