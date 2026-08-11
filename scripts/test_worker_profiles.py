from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WorkerProfileContractTests(unittest.TestCase):
    def test_profiles_pin_expected_roles(self) -> None:
        expected = {
            "luna-worker.toml": ("luna_worker", "gpt-5.6-luna"),
            "terra-worker.toml": ("terra_worker", "gpt-5.6-terra"),
        }
        for filename, (name, model) in expected.items():
            text = (ROOT / "agents" / filename).read_text(encoding="utf-8")
            self.assertRegex(text, rf'(?m)^name = "{re.escape(name)}"$')
            self.assertRegex(text, rf'(?m)^model = "{re.escape(model)}"$')
            self.assertIn('model_reasoning_effort = "max"', text)
            self.assertIn('description = "', text)
            self.assertEqual(text.count('developer_instructions = """'), 1)
            self.assertGreaterEqual(text.count('"""'), 2)

    def test_skill_references_lane_contract(self) -> None:
        skill = (ROOT / "skill" / "agent-team" / "SKILL.md").read_text(encoding="utf-8")
        lanes = (ROOT / "skill" / "agent-team" / "references" / "implementation-lanes.md").read_text(encoding="utf-8")
        self.assertIn("references/implementation-lanes.md", skill)
        self.assertIn("`luna_worker`", lanes)
        self.assertIn("`terra_worker`", lanes)
        self.assertIn("Prefer `luna_worker`", lanes)
        self.assertIn("Use `terra_worker`", lanes)
        self.assertIn("`fork_turns: none`", lanes)
        self.assertIn("Task size alone does not select Terra", lanes)
        self.assertIn("correct the specification", lanes)
        self.assertIn("never activates independent review", lanes)


if __name__ == "__main__":
    unittest.main()
