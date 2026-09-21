from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate_skill.py"
CANONICAL_SKILL = REPOSITORY_ROOT / "skill" / "agent-team" / "SKILL.md"


class SkillMetadataValidationTests(unittest.TestCase):
    def run_validator(self, skill_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(skill_path)],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_canonical_skill_metadata_is_supported(self) -> None:
        result = self.run_validator(CANONICAL_SKILL)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_unsupported_top_level_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_path = Path(temporary_directory) / "SKILL.md"
            skill_path.write_text(
                "---\n"
                "name: agent-team\n"
                "version: 0.3.0\n"
                "description: Test Skill.\n"
                "---\n\n"
                "# Agent Team\n",
                encoding="utf-8",
            )

            result = self.run_validator(skill_path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("unsupported top-level field: version", result.stderr)

    def test_rejects_duplicate_metadata_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_path = Path(temporary_directory) / "SKILL.md"
            skill_path.write_text(
                "---\n"
                "name: agent-team\n"
                "description: Test Skill.\n"
                "metadata:\n"
                "  version: 0.3.0\n"
                "  version: 9.9.9\n"
                "---\n\n"
                "# Agent Team\n",
                encoding="utf-8",
            )

            result = self.run_validator(skill_path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate metadata field: version", result.stderr)


if __name__ == "__main__":
    unittest.main()

