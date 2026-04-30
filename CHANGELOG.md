# Changelog — NexusCore Technologies DevSecOps Pipeline

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.3] — 2026-04-30

### Fixed
- **Hardened branch pipeline** — pinned all GitHub Actions to immutable commit SHAs
  (was still using floating tags `@v4`, `@master`, `@v2`, `@v3` after v1.2)
- **Hardened branch Gitleaks failures** — added `.gitleaks.toml` with regex allowlist
  for the three synthetic credentials in the main-branch git history; without this,
  Gitleaks scans the full shared history (`fetch-depth: 0`) and exits non-zero on every
  hardened branch run, incorrectly implying the hardened code is insecure
- **Pipeline timeouts** — added `timeout-minutes` to all jobs on both branches to
  prevent runaway workflow execution consuming Actions minutes

---

## [1.2] — 2026-04-30

### Fixed
- **Pipeline supply-chain risk (Critical)** — pinned all GitHub Actions on main branch to
  immutable commit SHAs, eliminating the floating-tag risk documented in STRIDE T1/T2
  and kill-chain Chain 2. SHAs fetched live from the GitHub API:
  - `actions/checkout` → `34e114876b0b11c390a56381ad16ebd13914f8d5` (v4)
  - `aquasecurity/trivy-action` → `ed142fd0673e97e23eac54620cfb913e5ce36c25` (v0.36.0)
  - `gitleaks/gitleaks-action` → `ff98106e4c7b2bc287b24eaf42907196329070c7` (v2)
  - `github/codeql-action/*` → `ce64ddcb0d8d890d2df4a9d1c04ff297367dea2a` (v3)
- **`vulnerable_app.py` annotation quality** — rewrote all seven vulnerability comment
  blocks to match Dockerfile annotation standard: attacker capability with real payloads,
  named real-world incident with financial impact, detection mechanism, exact parameterised fix
- **`/user` route** — wired the SQL injection endpoint so it is reachable via HTTP GET;
  previously `get_user()` existed but had no route binding
- **Gantt chart rendering** — replaced broken `dateFormat X` Mermaid block in
  `reports/threat-model-report.md` with a plain markdown remediation roadmap table;
  `dateFormat X` is unsupported in GitHub's Mermaid renderer
- **Threat model scope statement** — updated to accurately reflect 5 container
  weaknesses plus 1 CI/CD pipeline misconfiguration (floating Action tags)
- **`terraform/main.tf` AMI** — replaced us-east-1 AMI placeholder with eu-west-2
  placeholder consistent with the configured provider region
- **`reports/README.md`** — created document map index explaining the purpose of
  every report and the main/hardened branch relationship

---

## [1.1] — 2026-04-25

### Fixed
- Removed fabricated "31 threats" claim from executive summary and all headers
- Replaced "patient records" (healthcare) with "merchant/cardholder records" (fintech)
  throughout all documents — NexusCore is a payments company, not a healthcare provider
- Replaced fictional ECS Fargate + RDS PostgreSQL architecture with the actual stack:
  EC2 + S3 + Security Group + SQLite, as defined in `terraform/main.tf`
- Removed "12 of 12 MITRE tactics (100%)" fabricated coverage metric
- Replaced JWT/session token spoofing threat (S1) with actual risk: `GITHUB_TOKEN`
  leak and floating Actions tags — both grounded in the pipeline YAML
- Replaced all RDS PostgreSQL references with SQLite or EC2/S3 as appropriate
- Replaced ECS Fargate D3 DoS threat with EC2 CloudWatch alarm gap (what exists)
- Replaced RDS query logging gap (R4) with SQLite application-level logging gap
- Documented `trivy-action@master` floating tag explicitly in STRIDE T1 and T2
- Fixed `REMEDIATION.md` link to point to the hardened branch (not a non-existent path)
- Added MITRE ATT&CK technique mappings based on attack chain analysis

---

## [1.0] — 2026-04-20

### Added
- Initial repository structure: Flask vulnerable application, Dockerfile,
  Terraform IaC, GitHub Actions pipeline with five security gates
- STRIDE threat register covering 21 threats across six categories
- MITRE ATT&CK mapping across 12 tactics and 21 techniques
- Three end-to-end kill-chain analyses grounded in specific repo files
- Hardened branch with remediated versions of all vulnerable files
- `REMEDIATION.md` full findings index with before/after technical detail
