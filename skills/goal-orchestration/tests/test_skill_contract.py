import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
STRICT = (ROOT / "references" / "unattended.md").read_text(encoding="utf-8")
OPENAI_YAML = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")


def words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


class GoalOrchestrationContractTests(unittest.TestCase):
    def test_frontmatter_has_only_required_fields(self):
        frontmatter = SKILL.split("---", 2)[1]
        keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])

    def test_default_strict_context_is_small(self):
        self.assertLessEqual(words(SKILL), 800)
        self.assertLessEqual(words(SKILL + STRICT), 1_600)

    def test_only_complex_orchestration_references_remain(self):
        names = {path.name for path in (ROOT / "references").glob("*.md")}
        self.assertEqual(names, {"unattended.md", "coordination.md", "returns.md"})

    def test_fast_and_light_are_not_modes_or_files(self):
        self.assertFalse((ROOT / "references" / "interactive.md").exists())
        self.assertFalse((ROOT / "references" / "lightweight.md").exists())
        self.assertNotIn("Fast Path", SKILL)
        self.assertNotIn("Light Delegation", SKILL)

    def test_activation_is_explicit_or_narrowly_implicit(self):
        frontmatter = SKILL.split("---", 2)[1]
        self.assertIn("Explicit invocation always applies", frontmatter)
        self.assertIn("controls beyond native execution", frontmatter)
        self.assertIn("allow_implicit_invocation: true", OPENAI_YAML)
        shared = re.sub(r"\s+", " ", SKILL)
        hard_triggers = (
            "concurrent writers require ownership boundaries or worktree isolation",
            "state must recover across a task or runtime boundary",
            "share a contract and require an integration gate",
            "multiple checkpoint-and-repair waves",
            "independent review followed by enforced repair",
        )
        for trigger in hard_triggers:
            self.assertIn(trigger, shared)

    def test_complexity_labels_do_not_activate_by_themselves(self):
        shared = re.sub(r"\s+", " ", SKILL)
        self.assertIn(
            "Durable, parallel, unattended, cross-repository, and high-risk are signals, not triggers by themselves",
            shared,
        )
        exclusions = (
            "ordinary same-task Goals",
            "independent read-only parallelism",
            "simple sequential cross-repository work",
            "a standalone review",
        )
        for exclusion in exclusions:
            self.assertIn(exclusion, shared)

    def test_obsolete_mechanical_backend_is_removed(self):
        scripts = list((ROOT / "scripts").glob("**/*")) if (ROOT / "scripts").exists() else []
        self.assertEqual(scripts, [])

    def test_ordinary_strict_path_is_minimal(self):
        self.assertIn("no more than one control-only step", STRICT)
        self.assertIn(".agent/GOAL.md", STRICT)
        self.assertIn("Receive a direct bounded return", STRICT)
        self.assertIn("adds no other control files", STRICT)

    def test_critical_decision_chain_stays_in_main_thread(self):
        shared = re.sub(r"\s+", " ", SKILL)
        self.assertIn("Independent:", SKILL)
        self.assertIn("Parallelizable:", SKILL)
        self.assertIn("Local:", SKILL)
        self.assertIn("Keep the critical decision chain in the main thread", shared)
        self.assertIn("dispatch would leave the main Agent waiting", shared)
        self.assertIn("Use high reasoning in the main thread for critical decisions", shared)
        self.assertIn("continue non-overlapping critical-path work", shared)

    def test_strict_invalidates_only_covered_evidence(self):
        strict = re.sub(r"\s+", " ", STRICT)
        self.assertIn("covered artifact and relevant inputs remain unchanged", strict)
        self.assertIn("otherwise rerun the smallest affected check", strict)

    def test_strict_first_artifact_gate_is_conditional_and_non_persistent(self):
        strict = re.sub(r"\s+", " ", STRICT)
        self.assertIn("## Conditional First-Artifact Gate", STRICT)
        self.assertIn("copy an unproven pattern or shared contract", strict)
        self.assertIn("before further implementation dispatch", strict)
        self.assertIn("creates no state, commit, or extra review", strict)

    def test_strict_controls_are_triggered_independently(self):
        self.assertIn("Activation does not imply all of them", SKILL)
        self.assertIn("Concurrent writers or high-risk isolation", SKILL)
        self.assertIn("Scoped paths are already dirty", SKILL)
        self.assertIn("Return cannot fit directly", SKILL)
        self.assertIn("User supplies a token budget", SKILL)
        self.assertIn("Explicit Goal commit authority", SKILL)

    def test_accepted_wave_autocommit_reuses_existing_acceptance(self):
        strict = re.sub(r"\s+", " ", STRICT)
        self.assertIn("accepted wave is also a commit boundary", strict)
        self.assertIn("stages only the exact accepted paths", strict)
        self.assertIn("do not message Agents, extend returns, rerun checks", strict)
        self.assertIn("never repair-dispatch, commit per Agent", strict)
        self.assertIn("final aggregate Goal commit", strict)
        self.assertIn("pre-existing user changes", strict)

    def test_worktree_triggers_location_and_dirty_rules_are_explicit(self):
        coordination = (ROOT / "references" / "coordination.md").read_text(encoding="utf-8")
        self.assertIn("one isolated worktree per writable implementer", coordination)
        self.assertIn("<repo-parent>/<repo-name>-worktrees/<task-id>/", coordination)
        self.assertIn("Do not place worktrees", coordination)
        self.assertIn("Dirty but unrelated, disjoint paths", coordination)
        self.assertIn("Dirty changes required by, or overlapping", coordination)
        self.assertIn("Never stash, commit, reset, clean, relocate, or copy", coordination)
        self.assertIn("run them sequentially", coordination)

    def test_repair_is_continuation_not_mode(self):
        self.assertIn("Repair is continuation, not a separate mode", STRICT)
        self.assertIn("Reuse the implementer", STRICT)
        self.assertIn("do not resend the capsule", STRICT)

    def test_startup_and_cost_slos_are_explicit(self):
        self.assertIn("at most one orchestration-only step", SKILL)
        self.assertIn("Capsules are at most 400 words", SKILL)
        self.assertIn("Do not perform exact token accounting by default", SKILL)
        self.assertIn("at most three focused", SKILL)

    def test_context_isolation_has_an_explicit_fallback(self):
        shared = re.sub(r"\s+", " ", SKILL)
        strict = re.sub(r"\s+", " ", STRICT)
        self.assertIn("If supported, set `fork_turns=none`", shared)
        self.assertIn("limits turns, not bootstrap context", shared)
        self.assertIn("Context control is never a security boundary", shared)
        self.assertIn("ignore unrelated inherited context", shared)
        self.assertIn("do not claim isolation", strict)

    def test_read_only_review_does_not_overclaim_enforcement(self):
        shared = re.sub(r"\s+", " ", SKILL)
        strict = re.sub(r"\s+", " ", STRICT)
        self.assertIn("reviewer must not write", shared)
        self.assertIn("hard read-only needs a user-configured", shared)
        self.assertIn("Never create it automatically", strict)

    def test_repairs_are_bounded_per_active_unit(self):
        self.assertIn("Allow three focused repairs total", STRICT)
        self.assertIn("Never reset retries within the active unit", STRICT)

    def test_context_refresh_is_soft_and_reuses_state(self):
        strict = re.sub(r"\s+", " ", STRICT)
        self.assertIn("Three accepted milestones or six subagent returns", STRICT)
        self.assertIn("trigger an assessment, not an automatic reset", STRICT)
        self.assertIn("Create no extra", STRICT)
        self.assertIn("do not reset retries or rerun accepted checks", strict)
        self.assertIn("never create one implicitly", strict)

    def test_all_referenced_files_exist(self):
        for name in re.findall(r"`references/([^`]+\.md)`", SKILL):
            self.assertTrue((ROOT / "references" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
