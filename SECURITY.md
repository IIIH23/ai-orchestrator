# Security Policy

## Reporting a vulnerability

Do not open a public issue for a security problem. Use GitHub's private
reporting: **Security → Report a vulnerability** on this repository.

Include what you observed, how to reproduce it, and the commit you tested.
You can expect a first response within seven days.

## Scope

This repository is public and holds the AI Orchestrator control plane.
It must not contain secrets, real host addresses, or deployment-specific
reports; `tests/test_verify_staging.py` enforces the host rules in CI.

## Handling of secrets

- Secrets are provided through the environment or GitHub Environments and
  are never committed.
- Worker processes receive a sanitized environment
  (`tools/claude_code_adapter.py::sanitized_environment`).
- Secret scanning and push protection are enabled for this repository.
