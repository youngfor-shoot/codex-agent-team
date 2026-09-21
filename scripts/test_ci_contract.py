from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPOSITORY_ROOT / ".github" / "workflows"
ACTION_REF_RE = re.compile(r"\buses:\s*[^\s#]+@([^\s#]+)")
FULL_SHA_RE = re.compile(r"^[a-f0-9]{40}$")


class ContinuousIntegrationContractTests(unittest.TestCase):
    def test_external_actions_are_pinned_to_full_commit_sha(self) -> None:
        failures: list[str] = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            for reference in ACTION_REF_RE.findall(text):
                if not FULL_SHA_RE.fullmatch(reference):
                    failures.append(f"{path.name}: {reference}")

        self.assertEqual(failures, [])

    def test_ci_enforces_skill_coverage_and_powershell_contracts(self) -> None:
        text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("scripts/validate_skill.py", text)
        self.assertIn("--branch", text)
        self.assertIn("--fail-under=90", text)
        self.assertIn("--fail-under=80", text)
        self.assertIn("evidence_loop.py", text)
        self.assertIn("sync-agent-team.py", text)
        self.assertIn("PSScriptAnalyzer", text)
        self.assertIn("Invoke-ScriptAnalyzer", text)


if __name__ == "__main__":
    unittest.main()

