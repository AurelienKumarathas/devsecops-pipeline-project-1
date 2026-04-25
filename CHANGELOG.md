# Changelog

## v1.1 — April 2026
- Added MITRE ATT&CK technique mappings for Lateral Movement (T1021) and Command & Control (T1071) based on attack chain analysis
- Added insider threat UBA detection indicators to STRIDE register (E5 scenario — bulk cardholder data exfiltration)
- Fixed remediation roadmap to use relative sprint timelines (no hardcoded dates)
- Corrected architecture references to match actual repo: EC2 + S3 + Security Group + SQLite
- Removed fabricated threat counts and unsubstantiated coverage percentages

## v1.0 — March 2026
- Initial threat model published
- STRIDE register covering 6 categories across Flask app, Dockerfile, Terraform IaC, GitHub Actions pipeline
- MITRE ATT&CK mapping across identified threat scenarios
- Kill-chain analysis across 3 attack patterns
