# 🔐 DevSecOps Pipeline — NexusCore Technologies

| Branch | Pipeline Status |
|--------|-----------------|
| `main` (intentionally vulnerable) | ![main](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/actions/workflows/devsecops-pipeline.yml/badge.svg?branch=main) |
| `hardened` (fully remediated) | ![hardened](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/actions/workflows/devsecops-pipeline.yml/badge.svg?branch=hardened) |

![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat&logo=githubactions&logoColor=white)
![AWS](https://img.shields.io/badge/Cloud-AWS-FF9900?style=flat&logo=amazonaws&logoColor=white)
![CodeQL](https://img.shields.io/badge/SAST-CodeQL-6F42C1?style=flat)
![Trivy](https://img.shields.io/badge/SCA-Trivy-1904DA?style=flat&logo=aqua&logoColor=white)
![Gitleaks](https://img.shields.io/badge/Secrets-Gitleaks-red?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

> A production-grade DevSecOps pipeline embedding automated security scanning at every stage of the software development lifecycle — built for a fictional Series A fintech startup, NexusCore Technologies. Demonstrates shift-left security across SAST, SCA, secret detection, IaC scanning, and container security, with a full remediation branch showing how each vulnerability is fixed.

> ⚠️ **Educational repo:** NexusCore Technologies is a fictional client. All vulnerabilities are intentional and documented. All credentials are fake dummy values that exist solely to trigger and validate secret detection tooling. See [REMEDIATION.md](REMEDIATION.md) for the hardened versions of every file.

---

## 💼 Business Context

NexusCore Technologies is a fictional Series A fintech startup processing card payments for e-commerce merchants. After three security incidents in Q4 — a leaked API key, a dependency with a known CVE reaching production, and an S3 bucket misconfiguration — their investors demanded a demonstrable improvement in security posture before the Series B round.

The solution was a **shift-left security pipeline**: rather than running security scans manually before release, every commit now passes through five automated security gates before it can be merged. Developers see findings inline in pull requests. Nothing reaches production without passing all gates.

This repo demonstrates that pipeline end-to-end — including the intentionally vulnerable code that proves each gate catches what it is supposed to catch, and the hardened branch that shows how each finding would be remediated in practice.

---

## 📊 Pipeline Results

| Stage | Tool | Status | Findings |
|-------|------|--------|----------|
| SAST — Static Analysis | CodeQL | ✅ Passing | SQL Injection, Command Injection, SSTI detected & reported |
| SCA — Dependency Scanning | Trivy | 🔴 Intentionally fails | CVE-2020-14343 (Critical) in PyYAML 5.4.1; vulns in Flask 2.0.1 |
| IaC Security | Trivy IaC | 🔴 Intentionally fails | S3 bucket unencrypted; overly permissive security group |
| Secret Detection | Gitleaks | 🔴 Intentionally fails | `hashicorp-tf-password` + `generic-api-key` detected in source |
| Container Security | Trivy Image | 🔴 Intentionally fails | Root user, unpinned base image, unnecessary packages |
| Security Summary | GitHub Actions | ✅ Passing | All SARIF reports uploaded to GitHub Security tab |

> Pipeline failures are **by design** — the repo contains intentionally vulnerable code to demonstrate that each security gate correctly detects and blocks real-world vulnerability classes. The [hardened branch](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/tree/hardened) shows the remediated versions of every file.

---

## 🔒 Hardened Branch — Remediation Demo

The [`hardened` branch](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/tree/hardened) contains the security-engineered versions of every vulnerable file. All five security gates pass on that branch.

| File | What changed |
|------|--------------|
| [`Dockerfile.hardened`](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/blob/hardened/Dockerfile.hardened) | Pinned base image digest, non-root user, removed unnecessary packages, exec form CMD |
| [`src/remediated_app.py`](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/blob/hardened/src/remediated_app.py) | Parameterised queries, subprocess removed, `yaml.safe_load`, `debug=False`, path traversal fix, credentials from env vars |
| [`requirements-hardened.txt`](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/blob/hardened/requirements-hardened.txt) | PyYAML 6.0.2, Flask 3.0.3 — no known CVEs |
| [`terraform/main.tf`](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/blob/hardened/terraform/main.tf) | S3 public access blocks enabled, restricted security group, EBS encryption, Secrets Manager |

[**→ Read REMEDIATION.md for the full before/after technical breakdown**](REMEDIATION.md)

---

## 📸 Pipeline in Action

![Pipeline Screenshot](screenshots/pipeline-run.png)

*Live GitHub Actions run showing CodeQL passing, Gitleaks catching hardcoded secrets with commit SHA, file path and line number, and all SARIF results uploaded to the Security tab.*

---

## 📄 Security Analysis Documents

Beyond running scanners, this project includes three dedicated security analysis documents authored against the NexusCore threat landscape:

| Document | What it covers |
|----------|----------------|
| [STRIDE Threat Register](reports/analyses/stride-threats.md) | Full STRIDE analysis across all six categories — Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege — each threat tied to a specific file or component in the repo |
| [MITRE ATT&CK Mapping](reports/analyses/mitre-mapping.md) | Pipeline vulnerabilities mapped to MITRE ATT&CK Enterprise techniques — Initial Access, Execution, Persistence, Exfiltration |
| [Kill Chain Analysis](reports/analyses/kill-chain-analysis.md) | Three end-to-end attack chains showing how an attacker could chain the intentional vulnerabilities from initial access to full compromise |

---

## 🛠️ Security Tools

| Tool | Purpose | Stage |
|------|---------|-------|
| **CodeQL** | Static Application Security Testing (SAST) — analyses Python source for injection flaws, path traversal, and unsafe API usage | Build |
| **Trivy** | Software Composition Analysis (SCA) — scans `requirements.txt` for known CVEs | Build |
| **Gitleaks** | Secret Detection — scans entire git history and working tree for credentials, API keys, and tokens | Pre-commit / CI |
| **Trivy IaC** | Infrastructure as Code Security — scans Terraform for misconfigurations against CIS benchmarks | Build |
| **Trivy Container** | Container image scanning — checks the built Docker image for OS-level CVEs and misconfigurations | Post-build |
| **GitHub Security Tab** | Centralised SARIF vulnerability reporting — all tool findings are visible in one place at the PR level | Post-scan |

---

## 🏗️ Architecture

```mermaid
graph LR
    A[Developer Push] --> B[GitHub Actions]
    B --> C[SAST - CodeQL]
    B --> D[SCA - Trivy]
    B --> E[Secret Scan - Gitleaks]
    B --> F[IaC Scan - Trivy]
    C --> G[Docker Build]
    D --> G
    E --> G
    F --> G
    G --> H[Container Scan - Trivy]
    H --> I[AWS Deployment]
    C --> J[SARIF Upload]
    D --> J
    F --> J
    H --> J
    J --> K[GitHub Security Tab]
```

---

## 🔍 Intentional Vulnerabilities

Each vulnerability is chosen to exercise a specific security gate. The scanner finding it is the proof the gate works. See [REMEDIATION.md](REMEDIATION.md) for the technical fix and explanation for each one.

### SAST — CodeQL (`src/vulnerable_app.py`)
- **SQL Injection** — f-string concatenation in `get_user()`. An attacker controls the WHERE clause.
- **Command Injection** — `subprocess.check_output(..., shell=True)` in `/ping`. Shell metacharacters allow arbitrary OS command execution.
- **Server-Side Template Injection (SSTI)** — user input interpolated into a `render_template_string()` call. A Jinja2 expression in the URL achieves RCE.

### SCA — Trivy (`requirements.txt`)
- **CVE-2020-14343** in PyYAML 5.4.1 — **Critical (CVSSv3 9.8)** — arbitrary code execution via YAML deserialization.
- Multiple CVEs in Flask 2.0.1.

### IaC — Trivy (`terraform/main.tf`)
- S3 bucket with all public access block settings disabled.
- Security group with `0.0.0.0/0` on all ports and protocols (ingress and egress).
- EC2 root volume with `encrypted = false`.

### Secret Detection — Gitleaks
- Fake `hashicorp-tf-password` in `terraform/main.tf`.
- Fake `generic-api-key` in `src/vulnerable_app.py`.

### Container Security — Trivy (`Dockerfile`)
- No `USER` instruction — container runs as root.
- Unpinned base image (`FROM python:3.9`) — mutable tag enables supply chain attacks.
- Unnecessary packages installed: `curl`, `wget`, `vim`, `net-tools`.
- Shell form `CMD` — SIGTERM bypasses the Python process.

---

## 🏗️ Terraform Note

The `terraform/main.tf` in this repo is an **intentionally minimal demo** containing three deliberate misconfigurations, included solely to give the IaC scanning stage something to find. It is not a production Terraform module.

For a complete, production-grade AWS security architecture built with Terraform — including VPC design, IAM least-privilege, encrypted S3, CloudTrail, GuardDuty, and full Checkov/tfsec scanning — see the dedicated project:

**[→ Terraform AWS Security Audit (QuantumTrade)](https://github.com/AurelienKumarathas/terraform-aws-security-audit)**

---

## ⚡ Quick Start

```bash
git clone https://github.com/AurelienKumarathas/devsecops-pipeline-project-1.git
cd devsecops-pipeline-project-1

# Push any change to trigger the full security pipeline
git commit --allow-empty -m "trigger pipeline"
git push

# View scan results in:
#   Actions tab   → per-job logs
#   Security tab  → SARIF findings from all tools
```

To see the hardened versions of all files:

```bash
git checkout hardened
# Dockerfile.hardened and src/remediated_app.py are the remediated files
```

---

## 💼 Skills Demonstrated

| Skill | Tool / Technique | What it shows |
|-------|-----------------|---------------|
| CI/CD Pipeline Design | GitHub Actions | Multi-job pipeline with dependencies, conditional steps, and SARIF integration |
| SAST | CodeQL | Python static analysis catching injection flaws at the AST level |
| SCA | Trivy | CVE matching against known vulnerability databases for direct and transitive dependencies |
| Secret Detection | Gitleaks | Full git history scanning + working tree filesystem scan |
| IaC Security | Trivy IaC | CIS benchmark checks on Terraform before cloud resources are provisioned |
| Container Security | Docker + Trivy | Secure image best practices and OS-level CVE detection |
| Vulnerability Reporting | SARIF + GitHub Security tab | Centralised findings visible in PR reviews, not buried in CI logs |
| Security Engineering | REMEDIATION.md + hardened branch | Demonstrates ability to fix vulnerabilities, not just find them |
| Threat Modelling | STRIDE + MITRE ATT&CK + Kill Chain | Structured threat analysis beyond automated scanning |

---

## 📄 Licence

MIT — see [LICENSE](LICENSE) for details.
