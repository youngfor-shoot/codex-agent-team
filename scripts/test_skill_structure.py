from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skill" / "agent-team"
SKILL_PATH = SKILL_ROOT / "SKILL.md"


class SkillStructureTests(unittest.TestCase):
    def test_entrypoint_is_a_compact_router(self) -> None:
        lines = SKILL_PATH.read_text(encoding="utf-8").splitlines()

        self.assertGreater(len(lines), 20)

    def test_entrypoint_reference_links_resolve_one_level_deep(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        references = set(re.findall(r"\]\((references/[^)]+\.md)\)", text))

        self.assertGreaterEqual(len(references), 6)
        for relative_path in references:
            with self.subTest(reference=relative_path):
                self.assertTrue((SKILL_ROOT / relative_path).is_file())


if __name__ == "__main__":
    unittest.main()
