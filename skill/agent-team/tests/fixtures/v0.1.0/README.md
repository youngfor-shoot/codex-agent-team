# v0.1.0 Evidence-Loop Fixture Provenance

- Classification: `file-backed fixture`
- Owner: Agent Team maintainers
- Review cadence: per release
- Source: `D:/Another_me/Projects/codex-agent-team/tests/fixtures/v0.1.0/`
- Source status: untracked at repository HEAD `cc4ac9f0422bf397d4283b1c824157b7f52795f8`
- `evidence-loop-contract.json` SHA-256: `8ab433d54531fdfbfc50a7a1d7db31393b6507bb10486affd32aaaf9d32e5f32`
- `evidence-loop-state-verification-passed.json` SHA-256: `e720def9d54c847181ed73e0efb493dc498b517f5b4467d941092276ee8da27e`
- Output contract: preserve the v0.1.0 contract and `verification_passed` state shapes for compatibility testing.
- Rollback boundary: remove this fixture directory and restore the prior test fixture root.

The JSON files were copied byte-for-byte on 2026-09-05. Environment-specific
paths, Git identity, hashes, and the Python executable remain explicit
placeholders that the compatibility test replaces in its temporary run.
