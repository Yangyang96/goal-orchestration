"""Request accounting contract. No undocumented Codex usage exporter is fabricated."""
from __future__ import annotations
import json
from pathlib import Path


def read_events(path: Path) -> dict:
    events, malformed = [], 0
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                e = json.loads(line)
                if not isinstance(e, dict):
                    raise ValueError('not an object')
                events.append(e)
            except ValueError:
                malformed += 1
    return {'root_threads': sorted({e['thread_id'] for e in events
                                     if e.get('type') == 'thread.started' and e.get('thread_id')}),
            'raw_turn_usage': [e.get('usage') for e in events if e.get('type') == 'turn.completed'],
            'raw_usage_scope': 'UNVERIFIED_NOT_ALL_AGENT_TOTAL',
            'malformed_lines': malformed,
            'errors': [e for e in events if e.get('type') in ('error', 'turn.failed')]}


def account(ledger: dict | None, binding: dict, model: str, effort: str) -> dict:
    """Validate a trusted, separately calibrated runtime export; unknown is NOT zero.

    Schema example is in test_baseline.py. Coverage assertions are not self-proving;
    exporter implementation and calibration evidence must be independently reviewed.
    input_tokens includes cached_input_tokens; output includes reasoning if supplied.
    Each request must be its OWN delta, never parent-plus-descendants aggregates.
    """
    unknown = {'status': 'UNKNOWN', 'all_agent_tokens': None}
    if ledger is None:
        return {**unknown, 'reason': 'No calibrated runtime all-agent usage export'}
    try:
        if ledger['schema'] != 'goal-usage-v1' or ledger['binding'] != binding:
            raise ValueError('schema or trace binding mismatch')
        c = ledger['coverage']
        if c['source'] != 'runtime' or c['scope'] != 'own_request_delta':
            raise ValueError('unverified source or aggregate usage scope')
        for k in ('all_threads', 'all_requests', 'all_terminal', 'calibrated'):
            if c[k] is not True:
                raise ValueError('incomplete coverage: ' + k)
        evidence = c['evidence_sha256']
        if not isinstance(evidence, str) or len(evidence) != 64 or any(x not in '0123456789abcdef' for x in evidence):
            raise ValueError('missing calibration evidence digest')
        threads = {t['id']: t for t in ledger['threads']}
        if not threads or len(threads) != len(ledger['threads']):
            raise ValueError('invalid thread census')
        roots = sorted(t['id'] for t in threads.values() if t['parent_id'] is None)
        if len(roots) != 1 or roots != binding['root_threads']:
            raise ValueError('wrong root threads')
        expected = {}
        for ident, t in threads.items():
            if t['model'] != model or t['effort'] != effort or t['status'] != 'terminal':
                raise ValueError('model/effort drift or unsettled thread')
            seen, current = set(), ident
            while current is not None:
                if current in seen or current not in threads:
                    raise ValueError('invalid lineage')
                seen.add(current)
                current = threads[current]['parent_id']
            for rid in t['request_ids']:
                if rid in expected:
                    raise ValueError('duplicate request ownership')
                expected[rid] = ident
        if not threads[roots[0]]['request_ids']:
            raise ValueError('empty root usage census')
        requests = {}
        for r in ledger['requests']:
            rid = r['request_id']
            if rid in requests and requests[rid] != r:
                raise ValueError('conflicting duplicate request')
            requests[rid] = r
        if set(expected) != set(requests):
            raise ValueError('missing or extra request usage')
        totals = {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0}
        for rid, r in requests.items():
            if r['thread_id'] != expected[rid]:
                raise ValueError('incorrect request owner')
            for k in totals:
                if type(r[k]) is not int or r[k] < 0:
                    raise ValueError('invalid token count')
                totals[k] += r[k]
            if r['cached_input_tokens'] > r['input_tokens']:
                raise ValueError('cached input exceeds input')
        return {'status': 'COMPLETE_EXPORTED', **totals,
                'uncached_input_tokens': totals['input_tokens'] - totals['cached_input_tokens'],
                'all_agent_tokens': totals['input_tokens'] + totals['output_tokens'],
                'request_ids': sorted(requests), 'thread_count': len(threads),
                'evidence_sha256': evidence}
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        return {**unknown, 'reason': str(exc)}
