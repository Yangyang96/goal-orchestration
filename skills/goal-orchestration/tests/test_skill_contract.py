import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
REFS = {
    path.name: path.read_text(encoding="utf-8")
    for path in (ROOT / "references").glob("*.md")
}
ALL_RUNTIME = "\n".join([SKILL, *REFS.values()])
OPENAI_YAML = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")


def words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


class GoalOrchestrationContractTests(unittest.TestCase):
    def require(self, text, *fragments):
        text = re.sub(r"\s+", " ", text)
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(re.sub(r"\s+", " ", fragment), text)

    def test_package_exposes_two_conditional_controls(self):
        frontmatter = SKILL.split("---", 2)[1]
        keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])
        self.assertEqual(set(REFS), {"state.md", "coordination.md"})
        for name in REFS:
            self.assertIn(f"references/{name}", SKILL)
        for obsolete in ("returns.md", "unattended.md", "commits.md"):
            self.assertFalse((ROOT / "references" / obsolete).exists())

    def test_discovery_is_narrow_without_runtime_overpromises(self):
        frontmatter = SKILL.split("---", 2)[1]
        self.assertIn("Explicit invocation always applies", frontmatter)
        self.assertNotIn("enforced independent review", frontmatter)
        self.assertNotIn("across Agents or repositories", frontmatter)
        self.assertIn("allow_implicit_invocation: true", OPENAI_YAML)

    def test_each_loaded_route_has_a_budget(self):
        self.assertLessEqual(words(SKILL), 550)
        self.assertLessEqual(words(SKILL + REFS["state.md"]), 775)
        self.assertLessEqual(words(SKILL + REFS["coordination.md"]), 800)
        self.assertLessEqual(words(ALL_RUNTIME), 1_000)

    def test_runtime_capabilities_are_conditional_hints(self):
        self.require(
            SKILL,
            "request `fork_turns=none`",
            "history preference",
            "otherwise use a generic Agent",
            "otherwise inherit the runtime setting",
            "do not prove permissions or effective compute",
            "hard read-only requires a user-configured sandbox or custom Agent",
        )

    def test_acceptance_commit_and_repair_cross_one_interface(self):
        self.require(
            SKILL,
            "VALIDATION = check | covered paths/artifact | result",
            "The main Agent alone",
            "defaults to one local commit after each accepted",
            "only attributable task paths",
            "Never push, open a PR, amend, or rewrite history",
            "three focused repairs per active unit",
        )

    def test_state_and_coordination_preserve_safety(self):
        state = REFS["state.md"]
        coordination = REFS["coordination.md"]
        self.require(
            state,
            ".agent/STATE.md",
            "checkpoint normally changes only Status",
            "complete file under 12 KiB",
            "Resume from State",
        )
        self.require(
            coordination,
            "Writable paths must be disjoint",
            "not a security sandbox",
            "Never stash, commit, reset, clean, relocate, copy, or overwrite user changes",
        )
        for obsolete in ("GOAL.md", "PLAN.md", "STATUS.md", ".agent/inbox"):
            self.assertNotIn(obsolete, ALL_RUNTIME)


if __name__ == "__main__":
    unittest.main()
