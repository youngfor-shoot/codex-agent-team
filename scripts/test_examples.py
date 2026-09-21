from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from routing_rules import validate_scenario

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ExampleIntegrityTests(unittest.TestCase):
    def test_preview_example_matches_executable_contract(self) -> None:
        text = (REPOSITORY_ROOT / "examples/01-preview-output.md").read_text(encoding="utf-8")
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        self.assertIsNotNone(match, "preview example requires a machine-checkable scenario")
        scenario = json.loads(match.group(1))
        self.assertEqual(validate_scenario(scenario), [])
        self.assertEqual(scenario["expect"]["wakeup"], "none")

    def test_evidence_loop_example_is_honest_and_contract_shaped(self) -> None:
        path = REPOSITORY_ROOT / "examples" / "03-evidence-loop-session.md"
        text = path.read_text(encoding="utf-8")

        self.assertIn("representative", text.casefold())
        self.assertNotIn("a real `init", text)
        self.assertNotIn("...", text)
        self.assertNotIn("<new>", text)
        self.assertNotIn("<sha256>", text)
        self.assertIsNone(re.search(r'"[a-f0-9]{4,16}\.\.\."', text))
        transcript = json.loads(re.search(r"```json\n(.*?)\n```", text, re.DOTALL).group(1))
        steps = transcript["steps"]
        self.assertEqual([step["returncode"] for step in steps], [0, 0, 2, 0, 0, 0])
        self.assertEqual([step["summary"]["revision"] for step in steps], list(range(1, 7)))
        self.assertEqual(steps[-1]["summary"]["status"], "completed")
        self.assertEqual(len({step["summary"]["contract_hash"] for step in steps}), 1)
        artifact_section = text.split("## Independent review artifact", 1)[1]
        artifact = re.search(r"```text\n(.*?)```", artifact_section, re.DOTALL).group(1)
        self.assertEqual(
            hashlib.sha256(artifact.encode()).hexdigest(),
            steps[-1]["summary"]["last_review"]["artifact_hash"],
        )


if __name__ == "__main__":
    unittest.main()
