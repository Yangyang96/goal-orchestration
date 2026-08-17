import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
STRICT = (ROOT / "references" / "unattended.md").read_text(encoding="utf-8")


def words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


class GoalOrchestrationContractTests(unittest.TestCase):
    def test_frontmatter_has_only_required_fields(self):
        frontmatter = SKILL.split("---", 2)[1]
        keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])

    def test_default_strict_context_is_small(self):
        self.assertLessEqual(words(SKILL), 800)
        self.assertLessEqual(words(SKILL + STRICT), 1_500)

    def test_only_five_progressive_references_remain(self):
        names = {path.name for path in (ROOT / "references").glob("*.md")}
        self.assertEqual(
            names,
            {"interactive.md", "lightweight.md", "unattended.md", "coordination.md", "returns.md"},
        )

    def test_obsolete_mechanical_backend_is_removed(self):
        scripts = list((ROOT / "scripts").glob("**/*")) if (ROOT / "scripts").exists() else []
        self.assertEqual(scripts, [])

    def test_ordinary_strict_path_is_minimal(self):
        self.assertIn("no more than one control-only step", STRICT)
        self.assertIn(".agent/GOAL.md", STRICT)
        self.assertIn("Receive a direct bounded return", STRICT)
        self.assertIn("adds no other control files", STRICT)

    def test_strict_controls_are_triggered_independently(self):
        self.assertIn("Strict does not imply all of them", SKILL)
        self.assertIn("Concurrent writers or high-risk isolation", SKILL)
        self.assertIn("Scoped paths are already dirty", SKILL)
        self.assertIn("Return cannot fit directly", SKILL)
        self.assertIn("User supplies a token budget", SKILL)

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
        self.assertIn("Repair is not a fourth mode", STRICT)
        self.assertIn("Reuse the original implementer", STRICT)
        self.assertIn("do not resend the capsule", STRICT)

    def test_startup_and_cost_slos_are_explicit(self):
        self.assertIn("at most one orchestration-only step", SKILL)
        self.assertIn("Capsules are at most 400 words", SKILL)
        self.assertIn("Do not perform exact token accounting by default", SKILL)
        self.assertIn("at most three focused", SKILL)

    def test_three_repairs_are_shared_across_light_and_strict(self):
        light = (ROOT / "references" / "lightweight.md").read_text(encoding="utf-8")
        self.assertIn("counts as the first of Strict's three automatic repairs", light)
        self.assertIn("Allow three focused repairs total", STRICT)
        self.assertIn("never reset retries", STRICT)

    def test_context_refresh_is_soft_and_reuses_state(self):
        self.assertIn("Three accepted milestones or six subagent returns", STRICT)
        self.assertIn("trigger an assessment, not an automatic reset", STRICT)
        self.assertIn("Create no extra", STRICT)
        self.assertIn("do not reset retries or rerun accepted checks", STRICT)
        self.assertIn("never create one implicitly", STRICT)

    def test_all_referenced_files_exist(self):
        for name in re.findall(r"`references/([^`]+\.md)`", SKILL):
            self.assertTrue((ROOT / "references" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
