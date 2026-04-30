# Changelog — NexusCore Technologies DevSecOps Pipeline

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.2] — 2026-04-30

### Fixed
- **CodeQL findings in `src/remediated_app.py` (hardened branch)** — CodeQL's data flow analysis identified 3 residual High severity findings in the remediated file itself after the initial hardening pass:
  - Finding #21: Reflected XSS in `/greet` — initial fix for SSTI returned user input in an f-string without explicit escaping. Resolved by wrapping with `html.escape()` before the value appears in the response body.
  - Finding #22: Reflected XSS in `/load_config` — `str(config)` was reflecting user-controlled YAML input. Resolved by returning a fixed status string; user input no longer appears in the response.
  - Finding #23: Uncontrolled path expression in `/read_file` — CodeQL's taint analysis traced user input through `os.path.basename()` and `os.path.realpath()` all the way to the `open()` call. Resolved by replacing the sanitisation approach with an explicit `ALLOWED_FILES` dict; user input now only selects a key and never touches the filesystem path.
- Updated `REMEDIATION.md` to document findings #21–23 with full technical explanation
- Pinned Python base image in `Dockerfile.hardened` to verified SHA digest (replacing placeholder)
- Corrected finding #20 severity in `REMEDIATION.md` to `High → Residual: Low` post-remediation

---

## [1.1] — 2026-04-30

### Changed
- Pinned all GitHub Actions to immutable commit SHAs on both main and hardened branches
- Added `.gitleaks.toml` allowlist on hardened branch to correctly scope secret scanning to current code, not shared git history
- Added `timeout-minutes` to all pipeline jobs
- Updated STRIDE register to reflect remediation status of T1 (floating tags), S2 (trivy-action), and D5 (timeouts)
- Updated kill-chain Chain 2 to frame the floating-tags finding as a pre-remediation historical condition
- Restored Mermaid Gantt chart in threat model report
- Corrected architecture references throughout threat model — EC2 + S3 + SQLite (not ECS/RDS)
- Corrected domain scope — fintech/merchant records (not healthcare)
- Threat count corrected to 21
- Wired `/user` route in `vulnerable_app.py` so the SQL injection endpoint is reachable
- Improved vulnerability annotations in `vulnerable_app.py` to match Dockerfile standard
- Added `reports/README.md` document map

---

## [1.0] — 2026-04-20

### Added
- Flask vulnerable application with 7 intentional vulnerabilities across SQL injection, command injection, SSTI, path traversal, insecure deserialisation, hardcoded credentials, and debug mode
- Dockerfile with 5 intentional container security weaknesses
- Terraform IaC with 3 deliberate misconfigurations across S3, EC2, and Security Group
- GitHub Actions pipeline with five security gates: CodeQL, Trivy SCA, Trivy IaC, Gitleaks, Trivy Container
- STRIDE threat register covering 21 threats across six categories
- MITRE ATT&CK mapping across 12 tactics
- Three end-to-end kill-chain analyses grounded in specific repository files
- Hardened branch with remediated versions of all vulnerable files
- `REMEDIATION.md` full findings index with before/after technical detail for all 20 findings
