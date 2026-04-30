# Security Policy — NexusCore Technologies

## Scope

This is an **educational repository** containing intentionally vulnerable code built to demonstrate a DevSecOps pipeline. All credentials, secrets, and API keys present in the `main` branch are **fake dummy values** that exist solely to trigger and validate secret detection tooling (Gitleaks). They have never been used in any real system.

## Reporting a Vulnerability

If you discover a genuine security issue with the pipeline configuration, GitHub Actions workflows, or any other non-intentional vulnerability in this repository, please:

1. **Do not open a public GitHub issue.**
2. Email the maintainer at the address listed on the GitHub profile.
3. Include a description of the finding, the affected file(s), and steps to reproduce.

Expect a response within 48 hours.

## Intentional Vulnerabilities

The following are **by design** and do not require reporting:

- All vulnerabilities documented in [`REMEDIATION.md`](REMEDIATION.md)
- All STRIDE threats listed in [`reports/analyses/stride-threats.md`](reports/analyses/stride-threats.md)
- All pipeline failures on the `main` branch (Gitleaks, Trivy SCA, Trivy IaC, Trivy Container)
- Hardcoded fake credentials in `src/vulnerable_app.py` and `terraform/main.tf`

The [`hardened` branch](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/tree/hardened) contains the remediated versions of all intentionally vulnerable files.
