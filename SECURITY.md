# Security Policy — NexusCore DevSecOps Pipeline

## ⚠️ Important Notice

This repository contains **intentionally vulnerable code** for educational and portfolio demonstration purposes. The vulnerable files are:

- `src/vulnerable_app.py` — Flask app with SQL injection, command injection, SSTI, path traversal, insecure deserialization, hardcoded credentials, and debug mode enabled
- `Dockerfile` — container with root user, unpinned base image, unnecessary packages, and shell form CMD
- `terraform/main.tf` — IaC with public S3 bucket, open security groups, and unencrypted EBS

**Do not deploy these files to any environment.** The hardened equivalents are `Dockerfile.hardened` and `src/remediated_app.py`.

---

## Reporting a Vulnerability

If you discover a security vulnerability in this repository that is **not one of the intentional vulnerabilities documented in [REMEDIATION.md](REMEDIATION.md)**, please report it responsibly.

**Please do not open a public GitHub issue for security vulnerabilities.**

Contact: Open a [GitHub Security Advisory](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/security/advisories/new) to report privately.

Expected response time: 5 business days.

---

## Security Scanning

This repository runs automated security scans on every push via GitHub Actions:

| Tool | Coverage |
|------|----------|
| **CodeQL** | SAST — Python static analysis |
| **Trivy** | SCA — dependency CVEs; container image scanning |
| **Gitleaks** | Secret detection across all commits |
| **Trivy IaC** | Terraform misconfiguration scanning |

All findings are uploaded to the [GitHub Security tab](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/security/code-scanning) as SARIF reports.

---

## Supported Versions

This is a portfolio/educational project. Only the `main` branch is maintained.
