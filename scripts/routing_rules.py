#!/usr/bin/env python3
"""Static routing-rule conformance checks for Agent Team routing fixtures.

Encodes the cross-field routing invariants from SKILL.md as executable rules.
Each scenario fixture declares an `expect` block; this module verifies the
block is internally consistent and that the requested topology is reachable
from the declared authority and lifecycle evidence. This is the deterministic
static layer; it never calls an API. A separate manual/nightly model layer
feeds the same scenarios to a Codex session and diffs the emitted preview.
"""

from __future__ import annotations

from typing import Any

PERSISTENCE_GATES = {
    "authority",
    "future_reuse",
    "stable_responsibilities",
    "role_continuity",
    "direct_reentry_value",
    "lifecycle",
}
ALLOWED_TOPOLOGIES = {"single", "temporary", "persistent"}
ALLOWED_WAKEUPS = {"none", "heartbeat", "cron"}
ALLOWED_CONVERGENCE = {"single-pass", "evidence-loop", "phase-gated"}
ALLOWED_REVIEW_GATES = {"required", "not-required"}
ALLOWED_REVIEW_TRIGGERS = {
    "security-authorization-trust-boundary",
    "data-migration-overwrite-loss",
    "api-sync-persistence-contract",
    "deployment-publication-payment-deletion-account-permissions",
    "high-impact-insufficient-checks",
    "explicit-user-request",
}
ALLOWED_HUMAN_GATES = {
    "publication",
    "deployment",
    "deletion",
    "payment",
    "account-change",
    "permission-expansion",
    "none",
}


def _require(expect: dict[str, Any], key: str) -> Any:
    if key not in expect:
        raise AssertionError(f"scenario expect is missing required field: {key}")
    return expect[key]


def validate_expect(expect: dict[str, Any], authority: str | None = None) -> list[str]:
    errors: list[str] = []
    try:
        topology = _require(expect, "topology")
        wakeup = _require(expect, "wakeup")
        convergence = _require(expect, "convergence")
        review_gate = _require(expect, "independent_review_gate")
    except AssertionError as exc:
        return [str(exc)]

    if topology not in ALLOWED_TOPOLOGIES:
        errors.append(f"topology must be one of {sorted(ALLOWED_TOPOLOGIES)}")
    if wakeup not in ALLOWED_WAKEUPS:
        errors.append(f"wakeup must be one of {sorted(ALLOWED_WAKEUPS)}")
    if convergence not in ALLOWED_CONVERGENCE:
        errors.append(f"convergence must be one of {sorted(ALLOWED_CONVERGENCE)}")
    if review_gate not in ALLOWED_REVIEW_GATES:
        errors.append(f"review gate must be one of {sorted(ALLOWED_REVIEW_GATES)}")

    # Rule: an evidence loop always requires independent review.
    if convergence == "evidence-loop" and review_gate != "required":
        errors.append("evidence-loop requires independent_review_gate=required")

    # Rule: a required review gate needs a named trigger and a stop condition.
    if review_gate == "required":
        trigger = expect.get("review_trigger")
        if not trigger:
            errors.append("required review gate requires review_trigger")
        elif trigger not in ALLOWED_REVIEW_TRIGGERS:
            errors.append(f"unknown review_trigger: {trigger}")
        if not expect.get("review_stop_condition"):
            errors.append("required review gate requires review_stop_condition")
    else:
        if expect.get("review_trigger"):
            errors.append("not-required review gate must not declare review_trigger")
        if expect.get("independent_review_status", "not-applicable") != "not-applicable":
            errors.append(
                "not-required review gate requires independent_review_status=not-applicable"
            )

    # Rule: persistent topology requires every persistence gate to pass.
    if topology == "persistent":
        for gate in sorted(PERSISTENCE_GATES):
            value = expect.get(f"persistence_{gate}")
            if value is not True:
                errors.append(f"persistent topology requires persistence_{gate}=true")
        for lifecycle in ("team_name", "controller", "write_scopes", "checkpoint", "completion", "retirement_trigger"):
            if not expect.get(f"lifecycle_{lifecycle}"):
                errors.append(f"persistent topology requires lifecycle_{lifecycle}")
    else:
        if expect.get("persistence_authority") is not None:
            errors.append("non-persistent topology must not declare persistence gates")

    # Rule: temporary topology never creates user-owned tasks.
    if topology == "temporary" and expect.get("creates_user_owned_tasks") is True:
        errors.append("temporary topology must not create user-owned tasks")

    # Rule: wakeup with heartbeat/cron needs a stop condition.
    if wakeup in {"heartbeat", "cron"} and not expect.get("wakeup_stop_condition"):
        errors.append(f"{wakeup} wakeup requires wakeup_stop_condition")

    # Rule: explicit persistence wording is required for persistent topology.
    if topology == "persistent" and authority not in {
        "explicit-invocation",
        "auto-lifetime",
    }:
        errors.append(
            "persistent topology requires explicit-invocation or auto-lifetime authority"
        )

    # Rule: human gates must be allowed values.
    human_gates = expect.get("human_gates", [])
    for gate in human_gates:
        if gate not in ALLOWED_HUMAN_GATES:
            errors.append(f"unknown human gate: {gate}")

    return errors


def validate_scenario(scenario: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("id", "request", "authority", "expect"):
        if key not in scenario:
            errors.append(f"scenario missing required field: {key}")
    if errors:
        return errors
    if not str(scenario["id"]).strip():
        errors.append("scenario id must be non-empty")
    if scenario["authority"] not in {
        "explicit-invocation",
        "implicit",
        "auto-lifetime",
        "plain-multi-agent",
    }:
        errors.append(f"unknown authority: {scenario['authority']}")
    errors.extend(validate_expect(scenario["expect"], scenario["authority"]))
    return errors
