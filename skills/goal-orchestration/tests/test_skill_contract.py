import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
REFS = {
    path.name: path.read_text(encoding="utf-8")
    for path in (ROOT / "references").glob("*.md")
}
OPENAI_YAML = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")


class GoalOrchestrationContractTests(unittest.TestCase):
    def test_package_exposes_two_conditional_controls(self):
        frontmatter = SKILL.split("---", 2)[1]
        keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])
        self.assertEqual(set(REFS), {"state.md", "coordination.md"})
        for name in REFS:
            self.assertIn(f"references/{name}", SKILL)
        for obsolete in ("returns.md", "unattended.md", "commits.md"):
            self.assertFalse((ROOT / "references" / obsolete).exists())

    def test_discovery_metadata_matches_package(self):
        self.assertIn('name: goal-orchestration', SKILL.split('---', 2)[1])
        self.assertIn('$goal-orchestration', OPENAI_YAML)
        self.assertIn('allow_implicit_invocation: false', OPENAI_YAML)


if __name__ == "__main__":
    unittest.main()
