"""Offline contract, fixture and accounting tests. No model calls or simulated scores."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fixtures
import runner
import telemetry


def example_ledger():
    # Synthetic REQUEST-ACCOUNTING unit data, not an Astra evaluation result.
    return {
        "schema":"goal-usage-v1", "run_id":"unit", "phase":1,
        "coverage":{"source":"runtime","scope":"own_request_delta",
                    "all_threads_enumerated":True,"all_requests_enumerated":True,
                    "all_threads_terminal":True,"calibrated":True,"evidence_sha256":"a"*64},
        "threads":[{"id":"parent","parent_id":None,"model":"gpt-6-astra","reasoning_effort":"xhigh",
                    "status":"terminal","request_ids":["r1"]},
                   {"id":"child","parent_id":"parent","model":"gpt-6-astra","reasoning_effort":"xhigh",
                    "status":"terminal","request_ids":["r2"]}],
        "requests":[{"request_id":"r1","thread_id":"parent","input_tokens":100,"cached_input_tokens":80,"output_tokens":10},
                    {"request_id":"r2","thread_id":"child","input_tokens":200,"cached_input_tokens":120,"output_tokens":20}]}


def count(ledger):
    return telemetry.account(ledger, run_id="unit", phase=1, model="gpt-6-astra", effort="xhigh")


class AccountingTests(unittest.TestCase):
    def test_counts_parent_and_child_without_double_counting_cache(self):
        r=count(example_ledger())
        self.assertEqual(r["all_agent_tokens"],330)
        self.assertEqual(r["uncached_input_tokens"],100)
        self.assertEqual(r["threads"],2)

    def test_identical_duplicate_request_is_deduplicated(self):
        x=example_ledger();x["requests"].append(copy.deepcopy(x["requests"][0]))
        self.assertEqual(count(x)["all_agent_tokens"],330)

    def test_conflicting_duplicate_is_rejected(self):
        x=example_ledger();r=copy.deepcopy(x["requests"][0]);r["output_tokens"]=99;x["requests"].append(r)
        self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_missing_child_usage_is_not_zero(self):
        x=example_ledger();x["requests"].pop()
        self.assertIsNone(count(x)["all_agent_tokens"])

    def test_model_drift_is_not_comparable(self):
        x=example_ledger();x["threads"][1]["model"]="another-model"
        self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_effort_drift_is_not_comparable(self):
        x=example_ledger();x["threads"][1]["reasoning_effort"]="medium"
        self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_aggregate_parent_scope_is_not_added_to_child_usage(self):
        x=example_ledger();x["coverage"]["scope"]="parent_plus_descendants"
        self.assertIsNone(count(x)["all_agent_tokens"])

    def test_unsettled_or_uncalibrated_exports_are_unknown(self):
        for key in ("all_threads_enumerated","all_requests_enumerated","all_threads_terminal","calibrated"):
            x=example_ledger();x["coverage"][key]=False
            with self.subTest(key=key): self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_wrong_trial_or_phase_rejected(self):
        for key,value in (("run_id","different"),("phase",2)):
            x=example_ledger();x[key]=value
            with self.subTest(key=key): self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_lineage_cycle_rejected(self):
        x=example_ledger();x["threads"][1]["parent_id"]="child"
        self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_bad_counts_rejected(self):
        for key,value in (("input_tokens",-1),("input_tokens",True),("cached_input_tokens",999)):
            x=example_ledger();x["requests"][0][key]=value
            with self.subTest(key=key):self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_missing_export_never_becomes_a_saving(self):
        r=count(None)
        self.assertIsNone(r["all_agent_tokens"])
        self.assertIsNone(telemetry.money(r,{"uncached_input_per_million":1,"cached_input_per_million":.1,"output_per_million":5}))

    def test_prices_are_supplied_not_invented(self):
        self.assertIsNone(telemetry.money(count(example_ledger()),None))
        rates={"uncached_input_per_million":1,"cached_input_per_million":.1,"output_per_million":5}
        self.assertAlmostEqual(telemetry.money(count(example_ledger()),rates),.00027)

    def test_wrong_trace_binding_is_rejected(self):
        x=example_ledger()
        r=telemetry.account(x,run_id="unit",phase=1,model="gpt-6-astra",effort="xhigh",binding={"events_sha256":"b"*64})
        self.assertEqual(r["status"],"UNKNOWN")

    def test_empty_root_usage_cannot_certify_zero_cost(self):
        x=example_ledger();x["threads"][0]["request_ids"]=[];x["requests"].pop(0)
        self.assertEqual(count(x)["status"],"UNKNOWN")

    def test_nonfinite_prices_are_rejected(self):
        with self.assertRaises(ValueError):
            telemetry.money(count(example_ledger()),{"uncached_input_per_million":float("nan"),"cached_input_per_million":1,"output_per_million":1})

    def test_raw_cli_usage_is_explicitly_unverified(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"events.jsonl"
            p.write_text('{"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":5}}\nnot-json\n')
            r=telemetry.cli_observations(p)
            self.assertEqual(r["malformed_lines"],1)
            self.assertIn("UNVERIFIED",r["raw_usage_scope"])
            self.assertNotIn("all_agent_tokens",r)


class DesignTests(unittest.TestCase):
    def test_three_arm_prompt_difference_is_controlled(self):
        skill=runner.REPO/"skills/goal-orchestration"
        a=runner.task_prompt("A","TASK")
        b=runner.task_prompt("B","TASK")
        c=runner.task_prompt("C","TASK",skill)
        self.assertEqual(b.replace(runner.HINT+"\n",""),a)
        self.assertNotIn("$goal-orchestration",a)
        self.assertNotIn("$goal-orchestration",b)
        self.assertNotIn("不要委派",a)
        self.assertNotIn("do not delegate",a.lower())
        self.assertIn((skill/"SKILL.md").read_text(),c)
        self.assertNotIn("TINY_REF",c)

    def test_schedule_balanced_and_reproducible(self):
        tasks=["tiny","parallel","handoff"]
        jobs=runner.schedule(tasks,3,42)
        self.assertEqual(jobs,runner.schedule(tasks,3,42))
        self.assertEqual(len(jobs),27)
        for task in tasks:
            ordered=[[j["arm"] for j in jobs if j["task"]==task and j["repeat"]==r] for r in (1,2,3)]
            for position in range(3):self.assertEqual({o[position] for o in ordered},set(runner.ARMS))

    def test_invalid_schedules_fail(self):
        for tasks,n in (([],1),(["tiny"],0),(["tiny","tiny"],1),(["unknown"],1)):
            with self.subTest(tasks=tasks,n=n), self.assertRaises(ValueError):runner.schedule(tasks,n,1)

    def test_all_arms_have_same_runtime_options(self):
        m={"model":"gpt-6-astra","effort":"xhigh"}
        args=runner.cli_args("codex",m,Path("/workspace"),Path("/last.txt"))
        self.assertIn("agents.enabled=true",args)
        self.assertIn("features.multi_agent=true",args)
        self.assertIn('agents.default_subagent_model="gpt-6-astra"',args)
        self.assertIn('agents.default_subagent_reasoning_effort="xhigh"',args)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox",args)
        self.assertNotIn("danger-full-access",args)

    def test_preflight_missing_cli_is_blocked_without_inference(self):
        r=runner.preflight("__nonexistent_goal_test_cli__",None)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertEqual(r["model_calls"],0)

    def test_home_with_instructions_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/"AGENTS.md").write_text("not a clean benchmark home")
            r=runner.preflight("__nonexistent_goal_test_cli__",p)
            self.assertIn("DEDICATED_HOME_HAS_EXTRA_INSTRUCTIONS",r["problems"])

    def test_frozen_tampering_and_overwrite_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"campaign"
            m=runner.make_plan(out,runner.REPO/"skills/goal-orchestration",["tiny"],1,1,"gpt-6-astra","xhigh",60)
            runner.verify_frozen(out,m)
            with self.assertRaises(ValueError):runner.make_plan(out,runner.REPO/"skills/goal-orchestration",["tiny"],1,1,"gpt-6-astra","xhigh",60)
            (out/"frozen/skill/SKILL.md").write_text("changed")
            with self.assertRaises(ValueError):runner.verify_frozen(out,m)

    def test_prepared_case_contains_no_grader_or_reference(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"campaign"
            m=runner.make_plan(out,runner.REPO/"skills/goal-orchestration",["dirty"],1,1,"gpt-6-astra","xhigh",60)
            root,meta=runner.prepare_case(out,m["jobs"][0])
            w=root/"workspace"
            self.assertEqual((w/"ledgerkit/contract.py").read_text(),'ID_FIELD = "event_id"\n')
            self.assertEqual(runner.git(w,"show","HEAD:ledgerkit/contract.py"),'ID_FIELD = "id"')
            self.assertFalse((w/"fixtures.py").exists())
            self.assertEqual((w/"ledgerkit/store.py").read_text(),fixtures.STUBS["ledgerkit/store.py"])
            with self.assertRaises(ValueError):runner.prepare_case(out,m["jobs"][0])

    def test_not_run_cases_not_reported_as_model_failures_or_zero_tokens(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"campaign"
            runner.make_plan(out,runner.REPO/"skills/goal-orchestration",["tiny"],1,1,"gpt-6-astra","xhigh",60)
            r=runner.report(out)
            self.assertEqual(r["cases_recorded"],0)
            self.assertTrue(all(x["accepted"] is None for x in r["trials"]))
            self.assertTrue(all(x["median_all_agent_tokens"] is None for x in r["summary"]))
            self.assertEqual(r["performance_verdict"],"NOT_ESTABLISHED")


class FixtureTests(unittest.TestCase):
    def test_all_broken_and_reference_cases(self):
        r=runner.selfcheck()
        self.assertEqual(r["model_calls"],0)
        self.assertEqual(r["broken_cases_rejected"],6)
        self.assertEqual(len(r["reference_stage_checks"]),7)

    def make(self,root,task,phase=1):
        f=fixtures.fixture(task);fixtures.write_files(root,f["files"]);fixtures.write_files(root,f["dirty"])
        fixtures.apply_reference(root,task,phase)

    def test_early_successful_exit_does_not_fool_grader(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/"config_flag.py").write_text("raise SystemExit(0)\n")
            self.assertFalse(fixtures.grade(p,"tiny",1)["passed"])

    def test_dirty_input_loss_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,"dirty")
            (p/"ledgerkit/contract.py").write_text(fixtures.STUBS["ledgerkit/contract.py"])
            self.assertFalse(fixtures.grade(p,"dirty",1)["passed"])

    def test_handoff_cannot_implement_stage_two_early(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,"handoff",2)
            r=fixtures.grade(p,"handoff",1)
            self.assertFalse(r["passed"])
            self.assertIn("stage scope violation",r["stderr"])

    def test_handoff_phase_two_has_no_repeated_business_contract(self):
        f=fixtures.fixture("handoff")
        self.assertIn("--group-tag",f["prompts"][0])
        self.assertNotIn("--group-tag",f["prompts"][1])

    def test_non_atomic_import_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,"parallel")
            s=p/"ledgerkit/store.py"
            s.write_text(s.read_text().replace("db.rollback()","db.commit()"))
            self.assertFalse(fixtures.grade(p,"parallel",1)["passed"])

    def test_stale_overwrite_behavior_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.make(p,"stale")
            s=p/"ledgerkit/store.py"
            s.write_text(s.read_text().replace('raise ValueError("conflicting duplicate id")',
                          'db.execute("UPDATE entries SET cents=?, tag=? WHERE id=?", (cents, tag, ident))'))
            self.assertFalse(fixtures.grade(p,"stale",1)["passed"])


if __name__=="__main__":
    unittest.main()
