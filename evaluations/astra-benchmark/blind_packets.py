#!/usr/bin/env python3
"""Hide explicit treatment labels while retaining behavior and artifacts for review."""
import argparse
import json
from pathlib import Path
import random

p=argparse.ArgumentParser()
p.add_argument('campaign',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
metas=[]
for f in sorted((a.campaign/'runs').glob('*/metadata.json')):
    m=json.loads(f.read_text())
    if 'accepted' in m:
        metas.append((f.parent,m))
rng=random.Random(2026090717)
rng.shuffle(metas)
mapping={}
for index,(folder,m) in enumerate(metas,1):
    sample=f'sample-{index:02d}'
    mapping[sample]=m['run_id']
    request=(a.campaign/'frozen/fixtures'/m['task']/('prompt2.txt' if m.get('wave')==2 else 'prompt1.txt' if m['task']=='handoff' else 'prompt.txt')).read_text()
    events=[]
    for line in (folder/'events.jsonl').read_text().splitlines():
        try: event=json.loads(line)
        except json.JSONDecodeError: continue
        if event.get('type')=='item.completed':
            item=event.get('item',{})
            if item.get('type') in ['agent_message','command_execution','file_change','error']:
                events.append(item)
    packet={'sample':sample,'task':m['task'],'wave':m.get('wave',1),'user_request':request,
            'full_handoff_request_for_grader':(a.campaign/'frozen/fixtures/handoff/prompt1.txt').read_text() if m['task']=='handoff' else None,
            'mechanical_acceptance':m['accepted'],'validation':m.get('validation'),
            'phase1_full_validation':json.loads((folder/'phase1_full_validation.json').read_text()) if (folder/'phase1_full_validation.json').exists() else None,
            'commits_added':m.get('commits_added'),'final_status':m.get('final_status'),
            'final_message':(folder/'final.txt').read_text() if (folder/'final.txt').exists() else None,
            'events':events,'runtime_stderr':(folder/'stderr.txt').read_text() if (folder/'stderr.txt').exists() else None,'diff':(folder/'diff.patch').read_text() if (folder/'diff.patch').exists() else None}
    artifact_root = folder / 'phase1_snapshot' if (folder / 'phase1_snapshot').exists() else Path(m['workspace'])
    artifacts = {}
    for path in sorted(artifact_root.rglob('*')):
        if not path.is_file() or any(part in {'.git', '__pycache__'} for part in path.relative_to(artifact_root).parts):
            continue
        try:
            artifacts[str(path.relative_to(artifact_root))] = path.read_text()
        except UnicodeDecodeError:
            pass  # Binary fixture data is covered by the retained workspace and validators.
    packet['artifact_text'] = artifacts
    raw=json.dumps(packet,indent=2,ensure_ascii=False)
    # Replace every cohort run path, including cross-reference occurrences.
    for other,other_meta in metas:
        raw=raw.replace(str(other),'[RUN]').replace(other_meta['run_id'],'[RUN-ID]')
    raw=raw.replace(str(a.campaign),'[CAMPAIGN]')
    (a.output/(sample+'.json')).write_text(raw)
(a.output.parent/(a.output.name+'-mapping.json')).write_text(json.dumps(mapping,indent=2))
print('packets',len(metas),'labels withheld; behavior may itself reveal treatment')
