# Security Policy

## Report a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not open a
public issue containing exploit details, credentials, tokens, private paths, or
other sensitive data.

Include the affected file or workflow, expected security boundary, reproduction
steps, and the smallest safe proof of impact. Never include real secrets.

## Security scope

The highest-risk surfaces are:

- evidence-loop command and path isolation;
- state, contract, and frozen-asset integrity;
- output redaction and process termination;
- synchronization destination checks and backup behavior;
- authority boundaries for persistent tasks and consequential actions.

The evidence-loop helper is a convergence guardrail for trusted repository
code. It is not an operating-system sandbox for unknown or malicious code.
