# Changelog

## v1.1 — April 2026

### Added
- `reports/analyses/kill-chain-analysis.md` — three end-to-end attack chains (credential theft & exfiltration, supply chain compromise via CI/CD, container escape through to data destruction); each step grounded in a specific file and vulnerability in this repository
- `REMEDIATION.md` — structured remediation index on main branch; cross-references hardened branch for full before/after code diffs
- MITRE ATT&CK technique mappings for Lateral Movement (T1021) and Command & Control (T1071) based on attack chain analysis
- Insider threat UBA detection indicators in STRIDE register (E5 scenario — bulk cardholder data exfiltration)

### Changed
- Aligned all architecture references to the actual repository stack: EC2, S3, Security Group, SQLite
- Scoped all threat scenarios to confirmed findings in `vulnerable_app.py`, `Dockerfile`, `main.tf`, `requirements.txt`, and `devsecops-pipeline.yml`
- Remediation roadmap updated to use relative sprint timelines rather than fixed calendar dates
- STRIDE register and MITRE mapping updated to v1.1 with tightened per-finding source file references

## v1.0 — March 2026
- Initial threat model published
- STRIDE register covering 6 categories across Flask app, Dockerfile, Terraform IaC, and GitHub Actions pipeline
- MITRE ATT&CK mapping across identified threat scenarios
- Kill-chain analysis across 3 attack patterns
