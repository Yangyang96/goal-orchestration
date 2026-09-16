#!/usr/bin/env python3
"""Three-arm Codex baseline. Standard library; offline checks are NOT model trials."""
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
import uuid

import fixtures
from telemetry import account, cli_observations

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ARMS = ("A", "B", "C")
HINT = "必要时可将独立工作交给子 Agent，以收益是否超过协调开销为准。\n"
COMMON = ("Complete the task below. Correctness and preserving user changes come first; "
          "avoid unnecessary token use and elapsed time. Use only the assigned model "
          "and reasoning setting for this run, including any spawned agents. "
          "Use the task workspace, its local temporary worktrees, and supplied references only. "
          "Do not inspect other trials, controller code, hidden graders, reference solutions, "
          "global skills or external apps. Do not start nested Codex clients. "
          "Use normal platform tools and respect all platform security policies.\n\n")
SKILL_FILES = ("SKILL.md", "references/coordination.md", "references/state.md", "agents/openai.yaml")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE).strip()


def schedule(tasks: list[str], repeats: int, seed: int) -> list[dict]:
    """Every 3 repeats each arm occupies each order position once, within each task."""
    if repeats < 1 or not tasks or len(set(tasks)) != len(tasks) or set(tasks) - set(fixtures.TASKS):
        raise ValueError("invalid task/repeat selection")
    rng = random.Random(seed)
    orders = {t: rng.sample(list(ARMS), 3) for t in tasks}
    jobs = []
    for repeat in range(1, repeats + 1):
        for task in rng.sample(tasks, len(tasks)):
            order = orders[task]
            offset = (repeat - 1) % 3
            for arm in order[offset:] + order[:offset]:
                jobs.append({"run_id": f"{len(jobs)+1:03d}-{task}-{arm}-r{repeat}",
                             "task": task, "arm": arm, "repeat": repeat})
    return jobs


def make_plan(out: Path, skill: Path, tasks: list[str], repeats: int, seed: int,
              model: str, effort: str, timeout: int) -> dict:
    if out.exists():
        raise ValueError("Refusing to overwrite a campaign; choose a NEW output path")
    if out.resolve().is_relative_to(REPO):
        raise ValueError("Put campaign output outside the source repository")
    for name in SKILL_FILES:
        if not (skill / name).is_file():
            raise ValueError("Missing skill file: " + name)
    jobs = schedule(tasks, repeats, seed)
    out.mkdir(parents=True)
    for name in SKILL_FILES:
        dest = out / "frozen/skill" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(skill / name, dest)
    for name in ("runner.py", "fixtures.py", "telemetry.py"):
        shutil.copyfile(HERE / name, out / "frozen" / name)
    try:
        source_commit = git(REPO, "rev-parse", "HEAD")
    except subprocess.CalledProcessError:
        source_commit = None
    manifest = {
        "schema": "goal-baseline-v2", "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PLANNED_NOT_EXECUTED", "model": model, "effort": effort,
        "timeout_per_phase_seconds": timeout, "seed": seed, "repeats": repeats,
        "tasks": tasks, "source_commit": source_commit,
        "source_commit_note": "Content hashes bind working-tree bytes even if Git HEAD differs.",
        "jobs": jobs, "cases": len(jobs),
        "phase_invocations": sum(len(fixtures.fixture(j["task"])["prompts"]) for j in jobs),
        "hashes": {str(p.relative_to(out)): sha(p) for p in sorted((out/"frozen").rglob("*")) if p.is_file()},
        "metric_preference": ["functional_acceptance", "all_agent_tokens", "elapsed_time"],
        "policy": "No composite winner; report quality/cost/latency tradeoffs by task.",
        "notes": ["No model trials are run by plan/selfcheck/preflight.",
                  "A has the SAME subagent tools as B/C; it is not forced to stay single-agent.",
                  "C uses frozen CURRENT skill, not optimizations edited during measurement.",
                  "No outcome-based retries or silent exclusion of failures."]}
    dump(out/"manifest.json", manifest)
    return manifest


def verify_frozen(out: Path, m: dict) -> None:
    for rel, expected in m["hashes"].items():
        if sha(out/rel) != expected:
            raise ValueError("Frozen input changed: " + rel)
    for name in ("runner.py", "fixtures.py", "telemetry.py"):
        if sha(HERE/name) != m["hashes"]["frozen/"+name]:
            raise ValueError("Runner changed since plan; use frozen runner or create a new campaign")


def task_prompt(arm: str, request: str, supplied: Path | None = None) -> str:
    if arm not in ARMS:
        raise ValueError(arm)
    treatment = ""
    if arm == "B":
        treatment = HINT + "\n"
    elif arm == "C":
        if supplied is None:
            raise ValueError("C requires frozen skill")
        treatment = ("Use $goal-orchestration for this task. This is the only supplied version. "
                     f"Resolve relative references from {supplied.resolve()}.\n<skill>\n" +
                     (supplied/"SKILL.md").read_text(encoding="utf-8") + "</skill>\n\n")
    return COMMON + treatment + "Task:\n" + request


def prepare_case(out: Path, job: dict) -> tuple[Path, dict]:
    root = out / "runs" / job["run_id"]
    if root.exists():
        raise ValueError("Refusing to overwrite an existing trial")
    workspace = root / "workspace"
    workspace.mkdir(parents=True)
    fixture = fixtures.fixture(job["task"])
    fixtures.write_files(workspace, fixture["files"])
    git(workspace, "init", "-q")
    git(workspace, "config", "user.name", "Baseline Fixture")
    git(workspace, "config", "user.email", "fixture@example.invalid")
    git(workspace, "add", ".")
    git(workspace, "-c", "commit.gpgsign=false", "commit", "-qm", "Fixture base")
    (workspace/".git/info/exclude").write_text("__pycache__/\n*.pyc\n.worktrees/\n")
    base = git(workspace, "rev-parse", "HEAD")
    fixtures.write_files(workspace, fixture["dirty"])
    supplied = None
    if job["arm"] == "C":
        supplied = root / "supplied-skill"
        shutil.copytree(out / "frozen/skill", supplied)
    for n, request in enumerate(fixture["prompts"], 1):
        prompt = task_prompt(job["arm"], request, supplied)
        dest = root / f"phase-{n}"
        dest.mkdir()
        (dest/"prompt.txt").write_text(prompt, encoding="utf-8")
    meta = {**job, "base_commit": base, "initial_status": git(workspace, "status", "--short"),
            "initial_files": {str(p.relative_to(workspace)): sha(p) for p in workspace.rglob("*")
                              if p.is_file() and ".git" not in p.relative_to(workspace).parts},
            "phases": [], "status": "PREPARED", "accepted": False}
    dump(root/"result.json", meta)
    return root, meta


def cli_args(binary: str, m: dict, workspace: Path, output: Path) -> list[str]:
    return [binary, "exec", "--ignore-user-config", "--json", "--sandbox", "workspace-write",
            "--model", m["model"], "-c", "model_reasoning_effort="+json.dumps(m["effort"]),
            "-c", "features.multi_agent=true", "-c", "agents.enabled=true",
            "-c", "agents.default_subagent_model="+json.dumps(m["model"]),
            "-c", "agents.default_subagent_reasoning_effort="+json.dumps(m["effort"]),
            "-c", "features.plugins=false", "-c", "features.memories=false",
            "-C", str(workspace), "-o", str(output), "-"]


def preflight(binary: str, codex_home: Path | None) -> dict:
    """No inference call, no installation, no copying/printing credential contents."""
    resolved = shutil.which(binary)
    problems = []
    result = {"schema": "goal-preflight-v1", "model_calls": 0,
              "codex_executable_found": resolved is not None,
              "git_available": shutil.which("git") is not None,
              "dedicated_codex_home_supplied": codex_home is not None,
              "runtime_delegation_verified": False,
              "all_agent_telemetry_verified": False}
    if not resolved:
        problems.append("CODEX_EXECUTABLE_MISSING")
    if not result["git_available"]:
        problems.append("GIT_MISSING")
    if codex_home is None:
        problems.append("DEDICATED_CODEX_HOME_REQUIRED")
    elif not codex_home.is_dir():
        problems.append("CODEX_HOME_NOT_FOUND")
    else:
        # Conservative: don't accidentally load another installed skill or custom agent.
        contamination = []
        for rel in ("AGENTS.md", "AGENTS.override.md", "skills", "agents", "hooks.json"):
            p = codex_home/rel
            if p.is_file() or (p.is_dir() and any(p.iterdir())):
                contamination.append(rel)
        result["extra_instruction_paths"] = contamination
        if contamination:
            problems.append("DEDICATED_HOME_HAS_EXTRA_INSTRUCTIONS")
    if resolved:
        env = os.environ.copy()
        if codex_home:
            env["CODEX_HOME"] = str(codex_home.resolve())
        try:
            version = subprocess.run([resolved, "--version"], capture_output=True, text=True, timeout=15, env=env)
            result["cli_version"] = version.stdout.strip()
            help_result = subprocess.run([resolved,"exec","--help"], capture_output=True, text=True, timeout=15, env=env)
            help_text = help_result.stdout + help_result.stderr
            missing = [x for x in ("--json", "--ignore-user-config", "--sandbox", "--model") if x not in help_text]
            result["unsupported_required_flags"] = missing
            if version.returncode or help_result.returncode or missing:
                problems.append("CLI_INTERFACE_MISMATCH")
            auth = subprocess.run([resolved,"login","status"], capture_output=True, text=True, timeout=15, env=env)
            result["authenticated"] = auth.returncode == 0
            if auth.returncode:
                problems.append("CODEX_NOT_AUTHENTICATED")
            # Deliberately do not store stdout/stderr from authentication.
        except (OSError, subprocess.TimeoutExpired) as exc:
            problems.append(type(exc).__name__)
    result["problems"] = problems
    result["status"] = "BLOCKED" if problems else "CLI_READY_RUNTIME_CALIBRATION_REQUIRED"
    return result


def terminate(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def execute_phase(root: Path, m: dict, job: dict, phase: int, binary: str, home: Path) -> dict:
    phase_root, workspace = root/f"phase-{phase}", root/"workspace"
    cmd = cli_args(binary, m, workspace, phase_root/"final.txt")
    env = os.environ.copy()
    for name in ("CODEX_APP_TOOLS_PIPE_PATH", "CODEX_THREAD_ID", "CODEX_SESSION_ID", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE"):
        env.pop(name, None)
    env["CODEX_HOME"] = str(home.resolve())
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    record = {"phase": phase, "started_at": datetime.now(timezone.utc).isoformat(),
              "command": cmd, "prompt_sha256": sha(phase_root/"prompt.txt"),
              "timed_out": False, "interrupted": False}
    dump(phase_root/"execution.json", record)
    start = time.monotonic()
    try:
        with (phase_root/"events.jsonl").open("w") as stdout, (phase_root/"stderr.txt").open("w") as stderr:
            p = subprocess.Popen(cmd, cwd=workspace, env=env, stdin=subprocess.PIPE,
                                 stdout=stdout, stderr=stderr, text=True, start_new_session=True)
            try:
                p.communicate((phase_root/"prompt.txt").read_text(encoding="utf-8"),
                              timeout=m["timeout_per_phase_seconds"])
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
                terminate(p)
            except KeyboardInterrupt:
                record["interrupted"] = True
                terminate(p)
            record["returncode"] = p.returncode
    except OSError as exc:
        record.update(returncode=None, launch_error=str(exc))
    record["observed_cli_seconds"] = time.monotonic() - start
    record["cli"] = cli_observations(phase_root/"events.jsonl")
    record["all_agent_usage"] = account(None, run_id=job["run_id"], phase=phase,
                                        model=m["model"], effort=m["effort"])
    dump(phase_root/"execution.json", record)
    # Grades never go back into model history. No retry after seeing the result.
    record["grade"] = fixtures.grade(workspace, job["task"], phase)
    record["accepted"] = (record["returncode"] == 0 and not record["timed_out"] and
                          not record["interrupted"] and record["grade"]["passed"])
    try:
        record["git_status"] = git(workspace,"status","--short")
        record["commits_added"] = int(git(workspace,"rev-list","--count",job["base_commit"]+"..HEAD"))
        if record["commits_added"]:
            record["accepted"] = False
        (phase_root/"diff.patch").write_text(git(workspace,"diff",job["base_commit"]),encoding="utf-8")
    except subprocess.CalledProcessError as exc:
        record["git_error"] = str(exc)
        record["accepted"] = False
    # Track new/untracked artifact bytes via hashes, not only git diff.
    record["artifact_hashes"] = {str(p.relative_to(workspace)): sha(p) for p in workspace.rglob("*")
                                if p.is_file() and not p.is_symlink() and
                                not any(x in p.relative_to(workspace).parts for x in (".git","__pycache__"))}
    dump(phase_root/"execution.json", record)
    return record


def run_campaign(out: Path, binary: str, home: Path | None) -> dict:
    m = load(out/"manifest.json")
    verify_frozen(out,m)
    pf = preflight(binary,home)
    dump(out/("preflight-"+uuid.uuid4().hex[:8]+".json"),pf)
    if pf["problems"]:
        return {"status":"BLOCKED", "model_calls":0, "preflight":pf}
    if (out/"runs").exists():
        raise ValueError("Campaign already started; preserve it and create a new campaign")
    assert home is not None
    m["status"] = "RUNNING"
    m["preflight"] = pf
    dump(out/"manifest.json",m)
    interrupted = False
    for job in m["jobs"]:
        verify_frozen(out,m)
        root, result = prepare_case(out,job)
        result["status"] = "RUNNING"
        dump(root/"result.json",result)
        for phase in range(1,len(fixtures.fixture(job["task"])["prompts"])+1):
            record = execute_phase(root,m,result,phase,binary,home)
            result["phases"].append(record)
            dump(root/"result.json",result)
            # Still run stage 2 after a completed but failed stage 1. The E2E case
            # fails, so a later success cannot erase a stage-1 contract violation.
            if record["interrupted"] or record["timed_out"] or record["returncode"] != 0:
                interrupted = bool(record["interrupted"])
                break
        result["accepted"] = (len(result["phases"]) == len(fixtures.fixture(job["task"])["prompts"]) and
                              all(p["accepted"] for p in result["phases"]))
        result["status"] = "INTERRUPTED" if interrupted else "FINISHED"
        dump(root/"result.json",result)
        print(json.dumps({"run_id":job["run_id"],"accepted":result["accepted"],"status":result["status"]}),flush=True)
        if interrupted:
            break
    m["status"] = "INTERRUPTED" if interrupted else "EXECUTIONS_FINISHED_REVIEW_REQUIRED"
    dump(out/"manifest.json",m)
    return report(out)


def report(out: Path) -> dict:
    m = load(out/"manifest.json")
    rows, groups = [], defaultdict(list)
    request_owners = {}
    for job in m["jobs"]:
        path = out/"runs"/job["run_id"]/"result.json"
        if not path.exists():
            rows.append({**job,"status":"NOT_RUN","accepted":None})
            continue
        r = load(path)
        request_ids = set()
        totals, complete = 0, len(r["phases"]) == len(fixtures.fixture(job["task"])["prompts"])
        for phase in r["phases"]:
            lp = path.parent/f"phase-{phase['phase']}"/"usage-ledger.json"
            ledger = load(lp) if lp.exists() else None
            events = lp.parent/"events.jsonl"
            binding = {"prompt_sha256":phase["prompt_sha256"],
                       "events_sha256":sha(events) if events.exists() else None,
                       "root_thread_ids":phase["cli"]["thread_ids"],
                       "cli_version":m.get("preflight",{}).get("cli_version")}
            usage = account(ledger, run_id=job["run_id"], phase=phase["phase"],
                            model=m["model"],effort=m["effort"],binding=binding)
            if usage["status"] == "COMPLETE_EXPORTED":
                phase_ids = {q["request_id"] for q in ledger["requests"]}
                if request_ids & phase_ids:
                    complete = False
                request_ids |= phase_ids
            phase["all_agent_usage"] = usage
            complete = complete and usage["status"] == "COMPLETE_EXPORTED"
            totals += usage["all_agent_tokens"] or 0
        row = {**job, "status":r["status"], "accepted":r["accepted"],
               "observed_cli_seconds":sum(p["observed_cli_seconds"] for p in r["phases"]),
               "all_agent_tokens":totals if complete else None,
               "all_agent_usage_complete":complete}
        for ident in request_ids:
            if ident in request_owners:
                previous = request_owners[ident]
                previous["all_agent_tokens"] = None
                previous["all_agent_usage_complete"] = False
                row["all_agent_tokens"] = None
                row["all_agent_usage_complete"] = False
            request_owners[ident] = row
        rows.append(row)
        groups[(job["task"],job["arm"])].append(row)
    summary = []
    for task in m["tasks"]:
        for arm in ARMS:
            items = groups[(task,arm)]
            seconds = [x["observed_cli_seconds"] for x in items]
            tokens = [x["all_agent_tokens"] for x in items if x["all_agent_tokens"] is not None]
            all_ran = len(items)==m["repeats"] and all(x["status"]=="FINISHED" for x in items)
            summary.append({"task":task,"arm":arm,"scheduled":m["repeats"],"recorded":len(items),
                            "passed":sum(x["accepted"] is True for x in items),
                            "all_trials_finished":all_ran,
                            "median_observed_cli_seconds":statistics.median(seconds) if seconds else None,
                            "median_all_agent_tokens":statistics.median(tokens) if all_ran and len(tokens)==len(items) else None})
    result = {"schema":"goal-baseline-report-v2", "campaign_status":m["status"],
              "cases_scheduled":m["cases"],"cases_recorded":sum(x["status"]!="NOT_RUN" for x in rows),
              "summary":summary,"trials":rows,
              "performance_verdict":"NOT_ESTABLISHED",
              "caveats":["Runtime capability/config equivalence requires trace review.",
                         "CLI time is not certified all-thread quiescent wall time.",
                         "Null tokens mean unavailable, not zero. Never rank partial telemetry.",
                         "Small pilot; no statistical-significance or universal-winner claim."]}
    dump(out/"comparison-v2.json",result)
    return result


def selfcheck() -> dict:
    rows = []
    for task in fixtures.TASKS:
        with tempfile.TemporaryDirectory(prefix="goal-fixture-") as d:
            root=Path(d); fixture=fixtures.fixture(task)
            fixtures.write_files(root,fixture["files"]); fixtures.write_files(root,fixture["dirty"])
            negative=fixtures.grade(root,task,1)
            if negative["passed"]:
                raise AssertionError("Broken baseline unexpectedly passes: "+task)
            for phase in range(1,len(fixture["prompts"])+1):
                fixtures.apply_reference(root,task,phase)
                positive=fixtures.grade(root,task,phase)
                if not positive["passed"]:
                    raise AssertionError(task+": "+positive["stderr"])
                rows.append({"task":task,"phase":phase,"reference_passes":True})
    return {"type":"OFFLINE_FIXTURE_SELFCHECK_NOT_MODEL_EXECUTION","model_calls":0,
            "broken_cases_rejected":len(fixtures.TASKS),"reference_stage_checks":rows,"passed":True}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="action",required=True)
    plan=sub.add_parser("plan")
    plan.add_argument("--output",type=Path,required=True)
    plan.add_argument("--skill",type=Path,default=REPO/"skills/goal-orchestration")
    plan.add_argument("--tasks",nargs="+",choices=fixtures.TASKS,default=list(fixtures.TASKS))
    plan.add_argument("--repeats",type=int,default=3)
    plan.add_argument("--seed",type=int,default=20260916)
    plan.add_argument("--model",default="gpt-6-astra")
    plan.add_argument("--effort",choices=("low","medium","high","xhigh","max"),default="xhigh")
    plan.add_argument("--timeout",type=int,default=900)
    for name in ("preflight","run"):
        sp=sub.add_parser(name)
        sp.add_argument("--codex",default="codex")
        sp.add_argument("--codex-home",type=Path)
        if name=="run": sp.add_argument("--output",type=Path,required=True)
    sub.add_parser("selfcheck")
    rp=sub.add_parser("report");rp.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        if a.action=="plan":
            if a.timeout<=0: raise ValueError("timeout must be positive")
            result=make_plan(a.output.resolve(),a.skill.resolve(),a.tasks,a.repeats,a.seed,a.model,a.effort,a.timeout)
        elif a.action=="preflight": result=preflight(a.codex,a.codex_home)
        elif a.action=="selfcheck": result=selfcheck()
        elif a.action=="report": result=report(a.output.resolve())
        else: result=run_campaign(a.output.resolve(),a.codex,a.codex_home)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 2 if result.get("status")=="BLOCKED" else 0
    except (ValueError,OSError,AssertionError,subprocess.SubprocessError) as exc:
        print(json.dumps({"status":"ERROR","reason":str(exc)},ensure_ascii=False),file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
