# Changelog — NexusCore DevSecOps Pipeline

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — hardened branch

### Added
- `Dockerfile.hardened` — remediated container with pinned base image digest, non-root user, minimal packages, exec form CMD
- `src/remediated_app.py` — hardened Flask app with parameterised queries, subprocess removed, yaml.safe_load, debug=False, path traversal fix, credentials from env vars
- `REMEDIATION.md` — full before/after technical explanation of every vulnerability and fix
- `SECURITY.md` — security policy, responsible disclosure instructions, scanning overview
- `CHANGELOG.md` — this file
- SARIF upload step added to container-scanning job so findings are visible in GitHub Security tab

---

## [1.0.0] — 2026-03-01 — Initial release

### Added
- Intentionally vulnerable `Dockerfile` demonstrating 5 container security misconfigurations
- `src/vulnerable_app.py` — Flask app with 7 OWASP Top 10 vulnerabilities for scanner validation
- `terraform/main.tf` — IaC with 3 intentional AWS misconfigurations
- GitHub Actions pipeline: CodeQL (SAST), Trivy (SCA + IaC + Container), Gitleaks (secrets), SARIF upload
- `README.md` with pipeline results table, architecture diagram, and business context
