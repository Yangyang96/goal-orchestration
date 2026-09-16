"""Fail-closed all-agent accounting; raw CLI turn usage has UNVERIFIED coverage."""
from __future__ import annotations

import json
import math
from pathlib import Path


def cli_observations(path: Path) -> dict:
    events, malformed = [], 0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    events.append(event)
                else:
                    malformed += 1
            except json.JSONDecodeError:
                malformed += 1
    completed = [e.get("usage") for e in events if e.get("type") == "turn.completed"]
    items = [e.get("item", {}) for e in events if e.get("type") == "item.completed"]
    return {
        "thread_ids": sorted({e["thread_id"] for e in events if e.get("type") == "thread.started" and e.get("thread_id")}),
        "raw_completed_turn_usage": completed,
        "raw_usage_scope": "UNVERIFIED_DO_NOT_TREAT_AS_ALL_AGENTS",
        "malformed_lines": malformed,
        "completed_shell_commands": sum(x.get("type") == "command_execution" for x in items),
        "runtime_errors": [e.get("message", e.get("error")) for e in events if e.get("type") in ("error", "turn.failed")],
    }


def account(ledger: dict | None, *, run_id: str, phase: int, model: str, effort: str, binding: dict | None = None) -> dict:
    """Consume trusted runtime-exported request deltas, NEVER model-authored estimates.

    Exporter must attest complete thread/request census, own-request scope, terminal
    state and exact runtime/config binding. This validates the envelope, not the
    truthfulness of an exporter: its real runtime adapter needs separate calibration.
    No adapter for undocumented Codex per-child usage semantics is fabricated here.
    """
    unknown = {"status": "UNKNOWN", "all_agent_tokens": None}
    if ledger is None:
        return {**unknown, "reason": "No calibrated all-agent usage export"}
    try:
        if ledger["schema"] != "goal-usage-v1" or ledger["run_id"] != run_id or ledger["phase"] != phase:
            raise ValueError("ledger binding mismatch")
        if binding is not None and ledger.get("binding") != binding:
            raise ValueError("prompt/events/runtime binding mismatch")
        coverage = ledger["coverage"]
        if coverage["source"] != "runtime" or coverage["scope"] != "own_request_delta":
            raise ValueError("not runtime own-request deltas")
        for key in ("all_threads_enumerated", "all_requests_enumerated", "all_threads_terminal", "calibrated"):
            if coverage.get(key) is not True:
                raise ValueError("incomplete coverage: " + key)
        if not coverage.get("evidence_sha256") or len(coverage["evidence_sha256"]) != 64:
            raise ValueError("missing calibration evidence hash")
        threads = {x["id"]: x for x in ledger["threads"]}
        if len(threads) != len(ledger["threads"]) or not threads:
            raise ValueError("invalid thread census")
        roots = [key for key, x in threads.items() if x.get("parent_id") is None]
        if len(roots) != 1:
            raise ValueError("require one root per phase")
        if binding is not None and binding.get("root_thread_ids") != roots:
            raise ValueError("CLI/export root thread mismatch")
        if not threads[roots[0]].get("request_ids"):
            raise ValueError("empty root request census")
        for key, t in threads.items():
            if t["model"] != model or t["reasoning_effort"] != effort:
                raise ValueError("model/effort drift")
            if t["status"] != "terminal":
                raise ValueError("unsettled thread")
            seen, current = set(), key
            while current is not None:
                if current in seen or current not in threads:
                    raise ValueError("cyclic or incomplete lineage")
                seen.add(current)
                current = threads[current].get("parent_id")
        expected_ids = []
        for t in threads.values():
            expected_ids.extend(t["request_ids"])
        if len(set(expected_ids)) != len(expected_ids):
            raise ValueError("request assigned to multiple threads")
        requests = {}
        for r in ledger["requests"]:
            ident = r["request_id"]
            if ident in requests and requests[ident] != r:
                raise ValueError("conflicting duplicate request")
            requests[ident] = r
        if set(requests) != set(expected_ids):
            raise ValueError("missing or extra request usage")
        sums = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
        for ident, r in requests.items():
            thread = threads.get(r["thread_id"])
            if thread is None or ident not in thread["request_ids"]:
                raise ValueError("wrong request owner")
            for key in sums:
                value = r[key]
                if type(value) is not int or value < 0:
                    raise ValueError("noninteger or negative usage")
                sums[key] += value
            if r["cached_input_tokens"] > r["input_tokens"]:
                raise ValueError("cached input is a subset")
        return {"status": "COMPLETE_EXPORTED", **sums,
                "uncached_input_tokens": sums["input_tokens"] - sums["cached_input_tokens"],
                "all_agent_tokens": sums["input_tokens"] + sums["output_tokens"],
                "threads": len(threads), "requests": len(requests),
                "evidence_sha256": coverage["evidence_sha256"],
                "note": "Exporter provenance and calibration must be independently reviewed."}
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return {**unknown, "reason": str(exc)}


def money(usage: dict, rates: dict | None) -> float | None:
    """Optional explicitly supplied token-only prices, not subscription quota."""
    if usage.get("status") != "COMPLETE_EXPORTED" or rates is None:
        return None
    keys = ("uncached_input_per_million", "cached_input_per_million", "output_per_million")
    if any(type(rates.get(k)) not in (int, float) or not math.isfinite(rates[k]) or rates[k] < 0 for k in keys):
        raise ValueError("all three nonnegative prices must be supplied")
    return (usage["uncached_input_tokens"] * rates[keys[0]] +
            usage["cached_input_tokens"] * rates[keys[1]] +
            usage["output_tokens"] * rates[keys[2]]) / 1_000_000
