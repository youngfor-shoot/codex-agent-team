from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evidence_walkthrough import complete, prepare


class WalkthroughTests(unittest.TestCase):
    def test_real_cli_failure_repair_and_explicit_review(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-team-walkthrough-") as parent:
            root = Path(parent) / "run"
            transcript = prepare(root)
            steps = transcript["steps"]
            self.assertEqual([step["returncode"] for step in steps], [0, 0, 2, 0, 0])
            self.assertFalse(steps[2]["summary"]["last_verification"]["passed"])
            self.assertTrue(steps[4]["summary"]["last_verification"]["passed"])
            self.assertEqual(steps[-1]["summary"]["status"], "verification_passed")
            self.assertEqual(len({step["summary"]["contract_hash"] for step in steps}), 1)
            self.assertEqual(len({step["summary"]["state_hash"] for step in steps}), 5)
            self.assertTrue((root / "worktree" / ".git").is_file())
            self.assertEqual((root / "repo" / "answer.py").read_text(), "answer = 41\n")
            with self.assertRaises(FileNotFoundError):
                complete(root, root / "missing-review.md", "test-review")
            # Fixture provenance is explicit: this is not an independent agent review.
            artifact = root / "test-review.md"
            artifact.write_text("Synthetic review fixture for CLI regression only.\n")
            final = complete(root, artifact, "test-fixture-review")
            review = final["steps"][-1]["summary"]["last_review"]
            self.assertEqual(final["steps"][-1]["summary"]["status"], "completed")
            self.assertEqual(review["artifact_hash"], hashlib.sha256(artifact.read_bytes()).hexdigest())
            self.assertEqual(review["reviewer_run_id"], "test-fixture-review")
            self.assertEqual(json.loads((root / "transcript.json").read_text()), final)

    def test_existing_output_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-team-walkthrough-") as parent:
            root = Path(parent)
            marker = root / "keep.txt"
            marker.write_text("keep")
            with self.assertRaises(FileExistsError):
                prepare(root)
            self.assertEqual(marker.read_text(), "keep")

    def test_source_change_after_verification_rejects_completion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-team-walkthrough-") as parent:
            root = Path(parent) / "run"
            prepare(root)
            (root / "worktree" / "answer.py").write_text("answer = 99\n")
            artifact = root / "test-review.md"
            artifact.write_text("Synthetic fixture; changed source must not complete.\n")
            with self.assertRaises(RuntimeError):
                complete(root, artifact, "test-fixture-review")
            state = json.loads((root / "state" / "state.json").read_text())
            self.assertNotEqual(state["status"], "completed")


if __name__ == "__main__":
    unittest.main()
