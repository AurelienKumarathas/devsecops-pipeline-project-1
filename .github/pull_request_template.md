## Summary

<!-- What does this PR do? One paragraph max. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Security remediation
- [ ] IaC / infrastructure change
- [ ] CI/CD pipeline change
- [ ] Documentation update

---

## Security Checklist

> Complete this for every PR that touches source code, dependencies, Dockerfiles, Terraform, or pipeline config.

### SAST
- [ ] CodeQL analysis passes — 0 unresolved findings
- [ ] Bandit passes on any modified Python files — 0 findings

### SCA
- [ ] No new CRITICAL or HIGH CVEs introduced in `requirements*.txt`
- [ ] If a dependency was added or upgraded, reason documented below

### Secrets
- [ ] No credentials, API keys, tokens, or passwords in source code
- [ ] Gitleaks filesystem scan passes on this branch

### Container (if Dockerfile modified)
- [ ] Base image pinned to SHA digest
- [ ] Container runs as non-root user
- [ ] No unnecessary packages installed
- [ ] HEALTHCHECK instruction present
- [ ] Exec form CMD used
- [ ] Trivy image scan passes — 0 fixable CRITICAL/HIGH CVEs

### IaC (if Terraform modified)
- [ ] Trivy IaC scan passes after `.trivyignore` suppressions
- [ ] Any new suppressions are documented with rationale in `.trivyignore`
- [ ] No public S3 buckets, open security groups, or unencrypted storage

---

## Dependency changes

<!-- List any added, removed, or upgraded dependencies and why. -->

| Package | Old version | New version | Reason |
|---------|-------------|-------------|--------|
| | | | |

---

## Testing

- [ ] Pipeline triggered and all jobs green (link to run below)
- [ ] Relevant screenshots or SARIF output attached if applicable

**Pipeline run:** <!-- paste URL -->

---

## References

<!-- Link to relevant issues, CVEs, or documentation -->
