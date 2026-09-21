from __future__ import annotations

import json
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class SchemaCompatibilityTests(unittest.TestCase):
    def load_schema(self, name: str) -> dict:
        path = REPOSITORY_ROOT / "schemas" / name
        return json.loads(path.read_text(encoding="utf-8"))

    def test_state_v1_keeps_additive_fields_optional(self) -> None:
        schema = self.load_schema("state.schema.json")

        self.assertNotIn("active_seconds", schema["required"])

    def test_contract_v1_keeps_additive_fields_optional(self) -> None:
        schema = self.load_schema("contract.schema.json")
        limits_required = schema["properties"]["limits"]["required"]

        self.assertNotIn("env_passthrough", schema["required"])
        self.assertNotIn("active_budget_seconds", limits_required)
        self.assertNotIn("review_grace_minutes", limits_required)
        self.assertNotIn("max_capture_chars", limits_required)


if __name__ == "__main__":
    unittest.main()

