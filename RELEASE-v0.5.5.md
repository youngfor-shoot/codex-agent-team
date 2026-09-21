# v0.5.5 — Runtime-aware Agent Team

**Date:** 2026-09-21  
**Status:** Local checks passed; protected-branch CI is required before release.

Version 0.5.5 aligns the Python package metadata with the Skill version and
documents the current controller/executor contract and runtime-aware model
routing. The ROOT controller retains authority over scope, routing, integration,
and acceptance; an EXECUTOR follows its assigned boundary and returns evidence.

The README now describes selection guidance for Spark, Luna, Sol, Terra, and
Astra, while making availability and effective model/effort runtime-dependent.
Only the Luna and Terra worker profiles are bundled, and both pin `max` effort.
The documentation also states that Agent instructions and Git worktrees provide
no native-tool or operating-system isolation, and runtime model identity or
effort is unknown unless the runtime attests it.

The model matrix is not a benchmark and makes no comparative quality, speed, or
cost guarantee. Existing install commands remain documented in `README.md` and
`README.zh-CN.md`.

## Verification

- Package regression: 92 tests, 91 passed and one Windows symlink-privilege skip.
- Repository regression: 44 tests, 43 passed and one Windows symlink-privilege skip.
- Fresh 29-file install/verify and restore cases pass in the repository suite.
- Ruff, strict mypy, Skill metadata, and all three task-packet examples pass.
- Both bundled command-line tools report version 0.5.5.
- Focused independent review identified source/runtime inconsistencies; the
  release reconciles the existing hardening, schemas, examples, tests, and CI.

Cross-platform CI is checked on the release PR before merge and publication.
Historical native model evidence is host-specific; effective worker identity
and tool isolation remain subject to the documented runtime limitations.
