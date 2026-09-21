#!/usr/bin/env python3
"""Validate the dependency-free subset of Skill frontmatter used by this repo."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_TOP_LEVEL_FIELDS = {
    "allowed-tools",
    "description",
    "license",
    "metadata",
    "name",
}
REQUIRED_TOP_LEVEL_FIELDS = {"description", "metadata", "name"}
FIELD_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def validate_frontmatter(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [str(error)]
    if not lines or lines[0] != "---":
        return ["SKILL.md must start with YAML frontmatter"]
    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        return ["SKILL.md frontmatter is not closed"]

    top_level: dict[str, str] = {}
    metadata: dict[str, str] = {}
    current_field = ""
    errors: list[str] = []
    for line in lines[1:closing_index]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace():
            if current_field != "metadata":
                continue
            match = FIELD_PATTERN.match(line.strip())
            if not match:
                errors.append(f"invalid metadata entry: {line.strip()}")
                continue
            key, value = match.groups()
            if key in metadata:
                errors.append(f"duplicate metadata field: {key}")
                continue
            metadata[key] = unquote((value or "").strip())
            continue

        match = FIELD_PATTERN.match(line)
        if not match:
            errors.append(f"invalid top-level frontmatter entry: {line}")
            current_field = ""
            continue
        key, value = match.groups()
        current_field = key
        if key not in ALLOWED_TOP_LEVEL_FIELDS:
            errors.append(f"unsupported top-level field: {key}")
            continue
        if key in top_level:
            errors.append(f"duplicate top-level field: {key}")
            continue
        top_level[key] = unquote((value or "").strip())

    for field in sorted(REQUIRED_TOP_LEVEL_FIELDS - top_level.keys()):
        errors.append(f"missing required top-level field: {field}")
    for field in ("name", "description"):
        if field in top_level and not top_level[field]:
            errors.append(f"top-level field must not be empty: {field}")
    if top_level.get("metadata"):
        errors.append("top-level metadata must be a nested mapping")
    version = metadata.get("version", "")
    if not version:
        errors.append("metadata.version is required")
    elif not SEMVER_PATTERN.fullmatch(version):
        errors.append("metadata.version must be semantic version text")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_skill.py <SKILL.md>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    errors = validate_frontmatter(path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Valid Skill metadata: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

