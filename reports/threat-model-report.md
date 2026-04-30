# Threat Model Report — NexusCore Technologies

**Version:** 1.1  
**Classification:** Internal / Confidential  
**Scope:** DevSecOps pipeline, AWS infrastructure, containerised Flask application, Terraform IaC  
**Methodology:** STRIDE + MITRE ATT&CK + Kill-Chain Analysis

---

## Executive Summary

NexusCore Technologies is a fictional Series A fintech startup processing card payments for e-commerce merchants. This threat model covers the attack surface of the DevSecOps pipeline as implemented in this repository — from developer workstation through GitHub Actions CI/CD to the AWS-provisioned infrastructure defined in Terraform.

**Scope of this model:**
- Flask application (`src/vulnerable_app.py`) — 7 intentional vulnerabilities
- GitHub Actions pipeline (`.github/workflows/devsecops-pipeline.yml`) — 5 security gates; 1 deliberate misconfiguration (floating Action tags)
- Terraform IaC (`terraform/main.tf`) — EC2, S3, Security Group with 3 deliberate misconfigurations
- Docker container (`Dockerfile`) — 5 intentional container security weaknesses
- Python dependencies (`requirements.txt`) — known CVEs in PyYAML 5.4.1 and Flask 2.0.1

**MITRE ATT&CK techniques mapped:** See [analyses/mitre-mapping.md](analyses/mitre-mapping.md)  
**Attack chains modelled:** 3 (credential theft, supply chain compromise, container escape → data destruction)

---

## Architecture Under Review

The following represents the actual infrastructure and application stack defined in this repository:

```
Developer Push
     │
     ▼
GitHub Actions CI/CD Pipeline
     │  ├── CodeQL (SAST)
     │  ├── Trivy (SCA — dependencies)
     │  ├── Gitleaks (secret detection)
     │  ├── Trivy IaC (Terraform scan)
     │  └── Trivy Container (image scan)
     │
     ▼
Docker Build → Container Image
     │  └── Flask app (Python 3.9, runs as root)
     │
     ▼
AWS Infrastructure (terraform/main.tf)
     ├── EC2 Instance (t2.micro, public IP, unencrypted root disk)
     ├── S3 Bucket (public access blocks disabled)
     └── Security Group (0.0.0.0/0 all ports ingress + egress)
```

**Application:** Flask API (`src/vulnerable_app.py`) with SQLite database backend (`sqlite3`)

**Note:** This repository does not provision ECS, RDS, or a VPC. Threats scoped to those services are out of scope for this model.

---

## Vulnerability Inventory (Source of Truth)

All threats in this model are grounded in the following confirmed vulnerabilities:

| # | File | Vulnerability | Tool That Detects It |
|---|------|--------------|---------------------|
| 1 | `src/vulnerable_app.py` | SQL Injection — f-string in SQLite query | CodeQL |
| 2 | `src/vulnerable_app.py` | Command Injection — `subprocess.check_output(shell=True)` | CodeQL |
| 3 | `src/vulnerable_app.py` | SSTI — user input in `render_template_string()` | CodeQL |
| 4 | `src/vulnerable_app.py` | Path Traversal — no path validation on `/read_file` | CodeQL |
| 5 | `src/vulnerable_app.py` | Hardcoded credentials (`DATABASE_PASSWORD`, `API_KEY`) | Gitleaks |
| 6 | `src/vulnerable_app.py` | Debug mode enabled (`debug=True`) | CodeQL / Trivy |
| 7 | `src/vulnerable_app.py` | Insecure YAML deserialisation (`yaml.load` with FullLoader) | CodeQL / Trivy |
| 8 | `requirements.txt` | CVE-2020-14343 in PyYAML 5.4.1 (CVSS 9.8 Critical) | Trivy SCA |
| 9 | `requirements.txt` | Multiple CVEs in Flask 2.0.1 | Trivy SCA |
| 10 | `terraform/main.tf` | S3 public access blocks all disabled | Trivy IaC |
| 11 | `terraform/main.tf` | Security group: `0.0.0.0/0` all ports ingress + egress | Trivy IaC |
| 12 | `terraform/main.tf` | EC2 root volume `encrypted = false` | Trivy IaC |
| 13 | `terraform/main.tf` | EC2 `associate_public_ip_address = true` | Trivy IaC |
| 14 | `terraform/main.tf` | Hardcoded `DB_PASSWORD` in EC2 `user_data` | Gitleaks |
| 15 | `Dockerfile` | No `USER` instruction — container runs as root | Trivy Container |
| 16 | `Dockerfile` | Unpinned base image (`python:3.9`) — mutable tag | Trivy Container |
| 17 | `Dockerfile` | Unnecessary packages installed (curl, wget, vim, net-tools) | Trivy Container |
| 18 | `Dockerfile` | No `HEALTHCHECK` instruction | Trivy Container |
| 19 | `Dockerfile` | Shell form `CMD` — SIGTERM not forwarded to Python | Trivy Container |
| 20 | `.github/workflows/` | Actions pinned to floating tags, not commit SHAs | Manual review |

---

## Remediation Roadmap

| Priority | Finding | Sprint |
|----------|---------|--------|
| 🔴 Critical | Rotate all leaked credentials | Sprint 1 |
| 🔴 Critical | Fix SQL injection — parameterised queries | Sprint 1 |
| 🔴 Critical | Fix command injection — remove `shell=True` | Sprint 1 |
| 🔴 Critical | Pin Docker base image to SHA digest | Sprint 1 |
| 🔴 Critical | Add non-root `USER` to Dockerfile | Sprint 1 |
| 🟠 High | Upgrade PyYAML — CVE-2020-14343 | Sprint 2 |
| 🟠 High | Restrict S3 bucket public access | Sprint 2 |
| 🟠 High | Enable EC2 root volume encryption | Sprint 2 |
| 🟠 High | Tighten security group egress rules | Sprint 2 |
| 🟠 High | Pin GitHub Actions to commit SHAs | Sprint 2 |
| 🟡 Medium | Implement application-level audit logging | Sprint 3 |
| 🟡 Medium | Enable MFA on all AWS IAM accounts | Sprint 3 |
| 🟡 Medium | Move secrets to AWS Secrets Manager | Sprint 3 |
| 🟡 Medium | Add `HEALTHCHECK` to Dockerfile | Sprint 3 |

---

## MITRE ATT&CK Coverage

See [analyses/mitre-mapping.md](analyses/mitre-mapping.md) for the full technique-to-threat mapping.

---

## STRIDE Threat Register

See [analyses/stride-threats.md](analyses/stride-threats.md) for the complete per-threat register.

---

## Related Documents

| Document | Description |
|----------|-------------|
| [analyses/mitre-mapping.md](analyses/mitre-mapping.md) | MITRE ATT&CK technique mapping |
| [analyses/stride-threats.md](analyses/stride-threats.md) | STRIDE threat register |
| [analyses/kill-chain-analysis.md](analyses/kill-chain-analysis.md) | End-to-end attack chain analysis |
| [CHANGELOG.md](../../CHANGELOG.md) | Version history |
| [REMEDIATION.md](../../REMEDIATION.md) | Full findings index with hardened branch cross-reference |
