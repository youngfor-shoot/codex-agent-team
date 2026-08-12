#!/usr/bin/env python3
"""Validate Agent Team task-packet structure and completion invariants."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FIELD_RE = re.compile(r"^- `([^`]+)`: `([^`]*)`\s*$", re.MULTILINE)
HANDOFF_BLOCK_RE = re.compile(
    r"^<task_handoff>[ \t]*\r?\n(.*?)^</task_handoff>[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
HANDOFF_FIELD_RE = re.compile(r"^([a-z_]+):[ \t]*.*$")
REQUIRED_FIELDS = {
    "task_id",
    "status",
    "execution_topology",
    "wakeup_mode",
    "convergence_strategy",
    "independent_review_gate",
    "independent_review_status",
    "current_phase",
    "user_visible_objective_complete",
    "all_required_phases_verified",
    "whole_task_verified",
    "blocking_core_gaps",
}
REQUIRED_HEADINGS = {
    "## Intent Ledger",
    "## Routing Decision",
    "## Phase Gates",
    "## Objective",
    "## Completion Criteria",
    "## Integration Checklist",
    "## Final State",
}
REQUIRED_DISPATCH_HEADINGS = {
    "### Guidance",
    "### Context",
    "### Mission",
}
REQUIRED_HANDOFF_FIELDS = {
    "finding_severity:",
    "goal_alignment:",
    "new_assumptions:",
    "next_authorized_step:",
    "scope_delta:",
}
ALLOWED_TOPOLOGIES = {"single", "temporary", "persistent"}
ALLOWED_WAKEUPS = {"none", "heartbeat", "cron"}
ALLOWED_CONVERGENCE = {"single-pass", "evidence-loop", "phase-gated"}
ALLOWED_REVIEW_GATES = {"required", "not-required"}
ALLOWED_REVIEW_STATUSES = {"pending", "passed", "not-applicable"}
CONTRACT_VERSION = 1
__version__ = "0.3.0"


def exact_lines(text: str) -> set[str]:
    return {line.rstrip() for line in text.splitlines()}


def section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.rstrip() == heading),
        None,
    )
    if start is None:
        return ""

    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def bool_field(fields: dict[str, str], key: str, errors: list[str]) -> bool | None:
    value = fields.get(key)
    if value not in {"true", "false"}:
        errors.append(f"{key} must be true or false, found {value!r}")
        return None
    return value == "true"


def unchecked_items(text: str, heading: str) -> list[str]:
    return [
        line.strip()
        for line in section(text, heading).splitlines()
        if line.lstrip().startswith("- [ ]")
    ]


def validate_template(text: str) -> list[str]:
    errors: list[str] = []
    lines = exact_lines(text)
    for field in sorted(REQUIRED_FIELDS):
        if f"`{field}`" not in text:
            errors.append(f"template missing field: {field}")
    for heading in sorted(REQUIRED_HEADINGS):
        if heading not in lines:
            errors.append(f"template missing heading: {heading}")
    for heading in sorted(REQUIRED_DISPATCH_HEADINGS):
        if heading not in lines:
            errors.append(f"template missing dispatch heading: {heading}")

    handoff_blocks = HANDOFF_BLOCK_RE.findall(text)
    if len(handoff_blocks) != 1:
        errors.append(
            "template requires exactly one <task_handoff> block, "
            f"found {len(handoff_blocks)}"
        )
    handoff_fields = {
        f"{match.group(1)}:"
        for block in handoff_blocks
        for line in block.splitlines()
        if (match := HANDOFF_FIELD_RE.fullmatch(line.rstrip()))
    }
    for handoff_field in sorted(REQUIRED_HANDOFF_FIELDS):
        if handoff_field not in handoff_fields:
            errors.append(f"template missing handoff field: {handoff_field}")
    return errors


def validate_packet(text: str, require_complete: bool) -> list[str]:
    errors: list[str] = []
    fields = dict(FIELD_RE.findall(text))
    lines = exact_lines(text)

    for field in sorted(REQUIRED_FIELDS):
        if field not in fields:
            errors.append(f"missing field: {field}")
    for heading in sorted(REQUIRED_HEADINGS):
        if heading not in lines:
            errors.append(f"missing heading: {heading}")

    contract_version = fields.get("contract_version")
    if contract_version is not None and contract_version != str(CONTRACT_VERSION):
        errors.append(
            f"unsupported contract_version: {contract_version!r} "
            f"(expected {CONTRACT_VERSION})"
        )

    completion = section(text, "## Completion Criteria")
    integration = section(text, "## Integration Checklist")
    legacy_whole_checked = bool(
        re.search(r"^- \[x\].*Whole-task verification", completion, re.MULTILINE)
        or re.search(
            r"^- \[x\].*Whole-task verification", integration, re.MULTILINE
        )
    )
    legacy_user_unchecked = bool(
        re.search(
            r"^- \[ \].*user-visible objective", integration, re.MULTILINE
        )
    )
    if legacy_whole_checked and legacy_user_unchecked:
        errors.append(
            "whole-task verification is checked while the user-visible "
            "objective remains unchecked"
        )

    if errors:
        return errors

    if fields["execution_topology"] not in ALLOWED_TOPOLOGIES:
        errors.append(
            "execution_topology must be one of "
            f"{sorted(ALLOWED_TOPOLOGIES)}, found {fields['execution_topology']!r}"
        )
    if fields["wakeup_mode"] not in ALLOWED_WAKEUPS:
        errors.append(
            f"wakeup_mode must be one of {sorted(ALLOWED_WAKEUPS)}, "
            f"found {fields['wakeup_mode']!r}"
        )
    if fields["convergence_strategy"] not in ALLOWED_CONVERGENCE:
        errors.append(
            "convergence_strategy must be one of "
            f"{sorted(ALLOWED_CONVERGENCE)}, "
            f"found {fields['convergence_strategy']!r}"
        )

    review_gate = fields["independent_review_gate"]
    review_status = fields["independent_review_status"]
    if review_gate not in ALLOWED_REVIEW_GATES:
        errors.append(
            "independent_review_gate must be one of "
            f"{sorted(ALLOWED_REVIEW_GATES)}, found {review_gate!r}"
        )
    if review_status not in ALLOWED_REVIEW_STATUSES:
        errors.append(
            "independent_review_status must be one of "
            f"{sorted(ALLOWED_REVIEW_STATUSES)}, found {review_status!r}"
        )
    if review_gate == "required" and review_status == "not-applicable":
        errors.append(
            "independent_review_gate=required cannot use "
            "independent_review_status=not-applicable"
        )
    if review_gate == "not-required" and review_status != "not-applicable":
        errors.append(
            "independent_review_gate=not-required requires "
            "independent_review_status=not-applicable"
        )
    if (
        fields["convergence_strategy"] == "evidence-loop"
        and review_gate != "required"
    ):
        errors.append("evidence-loop requires independent_review_gate=required")

    user_complete = bool_field(
        fields, "user_visible_objective_complete", errors
    )
    phases_complete = bool_field(
        fields, "all_required_phases_verified", errors
    )
    whole_complete = bool_field(fields, "whole_task_verified", errors)
    no_core_gaps = fields["blocking_core_gaps"].strip().lower() == "none"

    if whole_complete is True:
        if user_complete is not True:
            errors.append(
                "whole_task_verified=true requires "
                "user_visible_objective_complete=true"
            )
        if phases_complete is not True:
            errors.append(
                "whole_task_verified=true requires "
                "all_required_phases_verified=true"
            )
        if not no_core_gaps:
            errors.append(
                "whole_task_verified=true requires blocking_core_gaps=none"
            )

    if require_complete:
        if fields["status"] != "completed":
            errors.append(
                f"completed packet requires status=completed, found {fields['status']!r}"
            )
        if user_complete is not True:
            errors.append(
                "completed packet requires user_visible_objective_complete=true"
            )
        if phases_complete is not True:
            errors.append(
                "completed packet requires all_required_phases_verified=true"
            )
        if whole_complete is not True:
            errors.append("completed packet requires whole_task_verified=true")
        if not no_core_gaps:
            errors.append("completed packet requires blocking_core_gaps=none")
        if review_gate == "required" and review_status != "passed":
            errors.append(
                "completed packet with required review requires "
                "independent_review_status=passed"
            )

        for heading in ("## Completion Criteria", "## Integration Checklist"):
            for item in unchecked_items(text, heading):
                errors.append(f"unchecked item in {heading}: {item}")

        completed_at = fields.get("completed_at", "")
        if not completed_at or completed_at.lower() == "pending":
            errors.append("completed packet requires a final completed_at value")
        remaining_risks = fields.get("remaining_risks", "")
        if remaining_risks.strip().lower() != "none":
            errors.append("completed packet requires remaining_risks=none")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--template", action="store_true")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args()

    if not args.packet.is_file():
        print(f"ERROR: task packet does not exist: {args.packet}", file=sys.stderr)
        return 2

    text = args.packet.read_text(encoding="utf-8")
    errors = (
        validate_template(text)
        if args.template
        else validate_packet(text, args.require_complete)
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    mode = "template" if args.template else "task packet"
    suffix = " completion" if args.require_complete else ""
    print(f"Valid {mode}{suffix}: {args.packet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
