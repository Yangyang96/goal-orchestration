"""Offline harness tests. Synthetic accounting examples are NOT Astra measurements."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import fixtures
import runner
import telemetry


def ledger():
    return {'schema':'goal-usage-v1','binding':{'root_threads':['root']},
            'coverage':{'source':'runtime','scope':'own_request_delta','all_threads':True,
                        'all_requests':True,'all_terminal':True,'calibrated':True,'evidence_sha256':'a'*64},
            'threads':[{'id':'root','parent_id':None,'model':'gpt-6-astra','effort':'xhigh',
                        'status':'terminal','request_ids':['r1']},
                       {'id':'child','parent_id':'root','model':'gpt-6-astra','effort':'xhigh',
                        'status':'terminal','request_ids':['r2']}],
            'requests':[{'request_id':'r1','thread_id':'root','input_tokens':100,'cached_input_tokens':80,'output_tokens':10},
                        {'request_id':'r2','thread_id':'child','input_tokens':200,'cached_input_tokens':120,'output_tokens':20}]}


def account(value, binding=None):
    return telemetry.account(value, binding or {'root_threads':['root']}, 'gpt-6-astra', 'xhigh')


class AccountingTests(unittest.TestCase):
    def test_own_request_totals_and_cache_subset(self):
        r=account(ledger())
        self.assertEqual(r['all_agent_tokens'],330)
        self.assertEqual(r['uncached_input_tokens'],100)
        self.assertEqual(r['thread_count'],2)

    def test_missing_export_unknown_not_zero(self):
        self.assertIsNone(account(None)['all_agent_tokens'])

    def test_identical_duplicate_deduplicated(self):
        x=ledger(); x['requests'].append(copy.deepcopy(x['requests'][0]))
        self.assertEqual(account(x)['all_agent_tokens'],330)

    def test_conflicting_duplicate_rejected(self):
        x=ledger(); q=copy.deepcopy(x['requests'][0]); q['output_tokens']=99; x['requests'].append(q)
        self.assertEqual(account(x)['status'],'UNKNOWN')

    def test_missing_child_usage_rejected(self):
        x=ledger(); x['requests'].pop()
        self.assertIsNone(account(x)['all_agent_tokens'])

    def test_unverified_coverage_rejected(self):
        for k in ('all_threads','all_requests','all_terminal','calibrated'):
            x=ledger(); x['coverage'][k]=False
            with self.subTest(k=k): self.assertEqual(account(x)['status'],'UNKNOWN')

    def test_parent_aggregate_never_added_to_children(self):
        x=ledger(); x['coverage']['scope']='parent_plus_descendants'
        self.assertIsNone(account(x)['all_agent_tokens'])

    def test_model_and_effort_drift_rejected(self):
        for k,v in [('model','other'),('effort','medium'),('status','running')]:
            x=ledger(); x['threads'][1][k]=v
            with self.subTest(k=k): self.assertEqual(account(x)['status'],'UNKNOWN')

    def test_wrong_trace_binding_rejected(self):
        self.assertEqual(account(ledger(),{'root_threads':['different']})['status'],'UNKNOWN')

    def test_wrong_parent_lineage_rejected(self):
        for parent in ('missing','child'):
            x=ledger(); x['threads'][1]['parent_id']=parent
            with self.subTest(parent=parent): self.assertEqual(account(x)['status'],'UNKNOWN')

    def test_invalid_token_counts_rejected(self):
        for k,v in [('input_tokens',-1),('output_tokens',True),('cached_input_tokens',999)]:
            x=ledger(); x['requests'][0][k]=v
            with self.subTest(k=k): self.assertEqual(account(x)['status'],'UNKNOWN')

    def test_empty_root_usage_rejected(self):
        x=ledger(); x['threads'][0]['request_ids']=[]; x['requests'].pop(0)
        self.assertEqual(account(x)['status'],'UNKNOWN')

    def test_invalid_calibration_digest_rejected(self):
        x=ledger(); x['coverage']['evidence_sha256']='z'*64
        self.assertEqual(account(x)['status'],'UNKNOWN')

    def test_raw_cli_usage_explicitly_not_all_agent_total(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'events.jsonl'
            p.write_text('{"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":10}}\nbad\n')
            r=telemetry.read_events(p)
            self.assertEqual(r['malformed_lines'],1)
            self.assertIn('UNVERIFIED',r['raw_usage_scope'])
            self.assertNotIn('all_agent_tokens',r)


class DesignTests(unittest.TestCase):
    def make_plan(self,td,tasks=('tiny',),repeats=1):
        p=Path(td)/'campaign'
        m=runner.plan(p,runner.REPO/'skills/goal-orchestration',list(tasks),repeats,42,'gpt-6-astra','xhigh',90)
        return p,m

    def test_three_arm_difference_controlled(self):
        a=runner.prompt('A','TASK'); b=runner.prompt('B','TASK')
        self.assertEqual(b.replace(runner.HINT,''),a)
        self.assertNotIn('$goal-orchestration',a)
        self.assertNotIn('do not delegate',a.lower())
        skill=runner.REPO/'skills/goal-orchestration'
        c=runner.prompt('C','TASK',skill)
        self.assertIn((skill/'SKILL.md').read_text(),c)
        self.assertNotIn('REFERENCE =',c)

    def test_order_balanced_and_deterministic(self):
        jobs=runner.schedule(['tiny','parallel'],3,42)
        self.assertEqual(jobs,runner.schedule(['tiny','parallel'],3,42))
        for task in ['tiny','parallel']:
            rows=[[j['arm'] for j in jobs if j['task']==task and j['repeat']==r] for r in (1,2,3)]
            for position in range(3): self.assertEqual({r[position] for r in rows},set('ABC'))

    def test_invalid_schedule_rejected(self):
        for tasks,n in [([],1),(['tiny'],0),(['tiny','tiny'],1),(['unknown'],1)]:
            with self.subTest(tasks=tasks,n=n),self.assertRaises(ValueError): runner.schedule(tasks,n,1)

    def test_no_arm_specific_runtime_capability_changes(self):
        args=runner.arguments('codex',{'model':'gpt-6-astra','effort':'xhigh'},Path('/w'),Path('/o'))
        for x in ['agents.enabled=true','features.multi_agent=true','agents.default_subagent_model="gpt-6-astra"',
                  'agents.default_subagent_reasoning_effort="xhigh"','workspace-write']:
            self.assertIn(x,args)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',args)

    def test_preflight_missing_cli_no_inference(self):
        r=runner.preflight('__no_such_goal_cli__')
        self.assertEqual(r['status'],'BLOCKED')
        self.assertEqual(r['model_calls'],0)

    def test_contaminated_dedicated_home_detected(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);(home/'AGENTS.md').write_text('extra guidance')
            self.assertIn('EXTRA_INSTRUCTIONS_IN_DEDICATED_HOME',runner.preflight('__missing__',home)['problems'])

    def test_plan_counts_endpoint_cases_separately_from_phases(self):
        with tempfile.TemporaryDirectory() as td:
            p,m=self.make_plan(td,('tiny','parallel','handoff'))
            self.assertEqual((m['cases'],m['parent_invocations']),(9,12))

    def test_frozen_inputs_checked_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p,m=self.make_plan(td); runner.verify(p,m)
            with self.assertRaises(ValueError): self.make_plan(td)
            (p/'frozen/skill/SKILL.md').write_text('changed')
            with self.assertRaises(ValueError): runner.verify(p,m)

    def test_dirty_workspace_and_no_answer_leak(self):
        with tempfile.TemporaryDirectory() as td:
            p,m=self.make_plan(td,('dirty',));root,r=runner.prepare(p,m['jobs'][0]);w=root/'workspace'
            self.assertEqual((w/'ledgerkit/contract.py').read_text(),'ID_FIELD = "event_id"\n')
            self.assertEqual(runner.git(w,'show','HEAD:ledgerkit/contract.py'),'ID_FIELD = "id"')
            self.assertFalse((w/'fixtures.py').exists())
            self.assertEqual((w/'ledgerkit/store.py').read_text(),fixtures.STUBS['ledgerkit/store.py'])
            with self.assertRaises(ValueError): runner.prepare(p,m['jobs'][0])

    def test_not_run_cases_not_model_failures(self):
        with tempfile.TemporaryDirectory() as td:
            p,m=self.make_plan(td);r=runner.report(p)
            self.assertEqual(r['cases_recorded'],0)
            self.assertTrue(all(x['accepted'] is None for x in r['trials']))
            self.assertTrue(all(x['median_all_agent_tokens'] is None for x in r['groups']))

    def test_blocked_run_never_creates_model_results(self):
        with tempfile.TemporaryDirectory() as td:
            p,m=self.make_plan(td);r=runner.run(p,'__missing_goal_cli__',None)
            self.assertEqual(r['model_calls'],0)
            self.assertFalse((p/'runs').exists())

    def test_completed_phase_failure_not_erased_by_later_success(self):
        # Synthetic controller unit test, not a live evaluation or model score.
        def fake_phase(root,job,n,m,binary,home):
            return dict(phase=n,returncode=0,interrupted=False,timed_out=False,
                        accepted=n==2,observed_cli_seconds=1,
                        prompt_sha256=runner.digest(root/f'phase-{n}'/'prompt.txt'),cli={'root_threads':[]})
        with tempfile.TemporaryDirectory() as td:
            p,m=self.make_plan(td,('handoff',))
            with patch.object(runner,'preflight',return_value={'problems':[]}),patch.object(runner,'phase',side_effect=fake_phase):
                r=runner.run(p,'synthetic-controller-unit-test',Path(td))
            self.assertEqual(r['cases_recorded'],3)
            self.assertTrue(all(x['accepted'] is False for x in r['trials']))
            self.assertTrue(all(x['all_agent_tokens'] is None for x in r['trials']))


class FixtureTests(unittest.TestCase):
    def make(self,root,task,n=1):
        f=fixtures.fixture(task);fixtures.write_files(root,f['files']);fixtures.write_files(root,f['dirty'])
        fixtures.apply_reference(root,task,n)

    def test_all_broken_cases_fail_and_reference_stages_pass(self):
        r=runner.selfcheck()
        self.assertEqual(r['model_calls'],0)
        self.assertEqual(r['broken_cases_rejected'],6)
        self.assertEqual(len(r['reference_checks']),7)

    def test_early_clean_exit_cannot_pass(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'config_flag.py').write_text('raise SystemExit(0)\n')
            self.assertFalse(fixtures.grade(p,'tiny',1)['passed'])

    def test_dirty_input_loss_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,'dirty');(p/'ledgerkit/contract.py').write_text(fixtures.STUBS['ledgerkit/contract.py'])
            self.assertFalse(fixtures.grade(p,'dirty',1)['passed'])

    def test_stage_two_early_implementation_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,'handoff',2)
            r=fixtures.grade(p,'handoff',1)
            self.assertFalse(r['passed']);self.assertIn('stage scope violation',r['stderr'])

    def test_handoff_followup_does_not_repeat_business_requirements(self):
        f=fixtures.fixture('handoff')
        self.assertIn('--group-tag',f['prompts'][0])
        self.assertNotIn('--group-tag',f['prompts'][1])

    def test_transaction_rollback_mutation_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,'parallel');s=p/'ledgerkit/store.py'
            s.write_text(s.read_text().replace('db.rollback()','db.commit()'))
            self.assertFalse(fixtures.grade(p,'parallel',1)['passed'])

    def test_stale_contract_overwrite_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,'stale');s=p/'ledgerkit/store.py'
            s.write_text(s.read_text().replace('raise ValueError("conflicting duplicate id")',
                'db.execute("UPDATE entries SET cents=?, tag=? WHERE id=?", (cents, tag, ident))'))
            self.assertFalse(fixtures.grade(p,'stale',1)['passed'])


if __name__ == '__main__':
    unittest.main()
