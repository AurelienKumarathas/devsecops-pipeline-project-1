# 🔒 Hardened Branch — NexusCore Technologies

This branch contains the **security-engineered versions** of all files that are intentionally vulnerable on `main`.

The `main` branch pipeline fails by design — Gitleaks, Trivy, and IaC scans catch real (fake) secrets and misconfigurations. This branch demonstrates how each finding is resolved: all five security gates pass here.

## What’s Different on This Branch

| File | What was fixed |
|------|---------------|
| `Dockerfile.hardened` | Non-root user, pinned base image SHA digest, removed unnecessary packages, exec-form CMD, HEALTHCHECK |
| `src/remediated_app.py` | Parameterised queries, command injection removed, `yaml.safe_load`, `debug=False`, `html.escape()` for XSS, file allowlist for path traversal, credentials from env vars |
| `terraform/main.tf` (hardened) | S3 public access blocks enabled, security group restricted, EBS encryption, Secrets Manager for credentials |
| `requirements.txt` (hardened) | PyYAML upgraded to 6.0.1, Flask upgraded to 3.0.x |
| `.gitleaks.toml` | Allowlist scoping Gitleaks to current code only — known fake credentials in shared git history are excluded |

## CodeQL Status

CodeQL identified 3 additional High severity findings in `src/remediated_app.py` during CI (XSS ×2, path traversal ×1) and all three were resolved. See [REMEDIATION.md](REMEDIATION.md) findings #21–23 for the full technical detail.

## Full Technical Detail

→ [REMEDIATION.md](REMEDIATION.md) — complete before/after breakdown for all 23 findings
