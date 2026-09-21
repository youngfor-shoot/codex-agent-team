from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ExampleIntegrityTests(unittest.TestCase):
    def test_evidence_loop_example_is_honest_and_contract_shaped(self) -> None:
        path = REPOSITORY_ROOT / "examples" / "03-evidence-loop-session.md"
        text = path.read_text(encoding="utf-8")

        self.assertIn("representative", text.casefold())
        self.assertNotIn("a real `init", text)
        self.assertNotIn("...", text)
        self.assertNotIn("<new>", text)
        self.assertNotIn("<sha256>", text)
        self.assertIsNone(re.search(r'"[a-f0-9]{4,16}\.\.\."', text))


if __name__ == "__main__":
    unittest.main()

