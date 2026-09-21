#!/usr/bin/env python3
"""Reproduce a real local fail/repair/pass loop, then await an external review.

The helper owns a newly created disposable repository only. It does not spawn a
reviewer or attest reviewer identity; completion requires a controller-supplied
review artifact and run identity. Test fixtures are not independent reviews.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CLI = Path(__file__).resolve().parents[1] / "skill/agent-team/scripts/evidence_loop.py"


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def save(root: Path, transcript: dict[str, Any]) -> None:
    (root / "transcript.json").write_text(
        json.dumps(transcript, indent=2) + "\n", encoding="utf-8"
    )


def step(root: Path, transcript: dict[str, Any], command: str,
         extra: list[str], expected: int = 0) -> None:
    args = [sys.executable, "-B", str(CLI), command,
            "--state-file", str(root / "state/state.json")]
    if command != "init":
        previous = transcript["steps"][-1]["summary"]
        args.extend(["--expected-contract-hash", previous["contract_hash"],
                     "--expected-state-hash", previous["state_hash"]])
    args.extend(extra)
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=60)
    if result.returncode != expected:
        raise RuntimeError(f"{command}: exit {result.returncode}: {result.stderr}")
    summary = json.loads(result.stdout)
    transcript["steps"].append({
        "command": command, "returncode": result.returncode, "summary": summary,
    })
    save(root, transcript)


def prepare(directory: Path) -> dict[str, Any]:
    root = directory.resolve()
    root.mkdir(parents=True, exist_ok=False)
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Walkthrough Fixture")
    git(repo, "config", "user.email", "walkthrough@example.invalid")
    (repo / "answer.py").write_text("answer = 41\n", encoding="utf-8")
    git(repo, "add", "answer.py")
    git(repo, "commit", "-m", "Seed failing walkthrough")
    worktree = root / "worktree"
    git(repo, "worktree", "add", "-b", "walkthrough", str(worktree))
    harness = root / "acceptance.py"
    harness.write_text(
        "from pathlib import Path\n"
        "import runpy\n"
        "actual = runpy.run_path(str(Path.cwd() / 'answer.py'))['answer']\n"
        "assert actual == 42, f'expected 42, got {actual}'\n"
        "print('acceptance passed: answer == 42')\n",
        encoding="utf-8",
    )
    transcript: dict[str, Any] = {
        "provenance": "Real CLI execution in a disposable linked worktree; source repair by this helper, not an agent benchmark.",
        "helper_sha256": hashlib.sha256(CLI.read_bytes()).hexdigest(),
        "acceptance_sha256": hashlib.sha256(harness.read_bytes()).hexdigest(),
        "steps": [],
    }
    step(root, transcript, "init", [
        "--run-id", "issue2-walkthrough", "--objective", "Return the required answer 42",
        "--worktree", str(worktree), "--check-json", json.dumps([sys.executable, "-B", str(harness)]),
        "--controller-harness", str(harness), "--max-iterations", "3",
        "--max-minutes", "60", "--review-grace-minutes", "60", "--command-timeout", "10",
    ])
    step(root, transcript, "next", ["--worker-run-id", "scripted-baseline"])
    step(root, transcript, "verify", [], expected=2)
    step(root, transcript, "next", ["--worker-run-id", "scripted-repair"])
    (worktree / "answer.py").write_text("answer = 42\n", encoding="utf-8")
    step(root, transcript, "verify", [])
    return transcript


def complete(directory: Path, artifact: Path, reviewer_run_id: str) -> dict[str, Any]:
    root = directory.resolve()
    review_bytes = artifact.read_bytes()
    if not review_bytes.strip():
        raise ValueError("review artifact must not be empty")
    transcript = json.loads((root / "transcript.json").read_text(encoding="utf-8"))
    if transcript["steps"][-1]["summary"]["status"] != "verification_passed":
        raise ValueError("prepare must end with passing verification before review")
    step(root, transcript, "review", [
        "--result", "pass", "--reviewer-run-id", reviewer_run_id,
        "--reviewer-backend", "native-verifier",
        "--artifact-hash", hashlib.sha256(review_bytes).hexdigest(),
    ])
    return dict(transcript)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "complete"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--review-artifact", type=Path)
    parser.add_argument("--reviewer-run-id")
    args = parser.parse_args()
    if args.mode == "prepare":
        transcript = prepare(args.directory)
    else:
        if not args.review_artifact or not args.reviewer_run_id:
            parser.error("complete requires --review-artifact and --reviewer-run-id")
        transcript = complete(args.directory, args.review_artifact, args.reviewer_run_id)
    print(json.dumps(transcript, indent=2))


if __name__ == "__main__":
    main()
