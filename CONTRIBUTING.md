# Contributing to codex-agent-team

Thanks for considering a contribution. This project has strong, non-obvious
invariants — please read this before opening a PR.

## The most important rules

- **Edit the canonical source first.** Durable Skill content lives in
  `skill/agent-team/`; the installed copy under `~/.codex/skills/agent-team`
  is a derived runtime artifact, never hand-edited.
- **Never hand-maintain both trees.** Use `scripts/sync-agent-team.ps1`
  (Windows) or `scripts/sync-agent-team.py` (cross-platform) to compare,
  install, or verify the runtime copy after changing the canonical source.
- **Do not add independent review as a default phase.** It remains a named
  residual-risk gate, never a routine step.
- **No new dependencies.** Use the Python standard library or PowerShell.
  The Skill and its helpers are dependency-free by design.
- **English only** for commits and repository documentation.
- **No unverified claims.** Do not claim adoption, usage, or compatibility
  without public evidence.

## Small changes

1. Fork and clone the repository.
2. Create a branch from `main`.
3. Make the change in the canonical source.
4. Run the verification suite (see `README.md` → Develop and verify):
   - `python -m unittest discover -s skill/agent-team/scripts -p "test_*.py"`
   - `python -m unittest discover -s scripts -p "test_*.py"`
   - template and example validation
   - `ruff check skill/agent-team/scripts scripts`
   - `mypy --strict skill/agent-team/scripts scripts`
5. If you changed the Skill surface, run the synchronizer `Verify` mode.
6. Open a PR against `main` with a clear summary and an evidence boundary
   section stating what your tests prove and what they do not.

## Larger changes

For routing-policy changes, first add or update a scenario fixture under
`tests/scenarios/` (see `tests/scenarios/README.md`). The static conformance
suite encodes the routing invariants; a behavior change without a fixture will
not be merged.

For changes that move content between `SKILL.md` and `references/`, keep
progressive disclosure: core routing stays in `SKILL.md`, detailed variants
live in one-level `references/` files, canonical templates in `templates/`.

## Review expectations

- Every PR must pass CI on Linux, macOS, and Windows.
- Commit messages and PR descriptions use English.
- Keep the "Evidence boundary" section: state plainly what is proven by CI
  and what requires fresh-task runtime evidence.
