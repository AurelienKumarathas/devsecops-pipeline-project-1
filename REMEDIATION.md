# Remediation Guide — NexusCore Technologies

**Scope:** Technical before/after remediation detail for all findings across `src/vulnerable_app.py`, `Dockerfile`, `terraform/main.tf`, `requirements.txt`, `.github/workflows/devsecops-pipeline.yml`, and `src/remediated_app.py`

> **Full before/after code diffs and the hardened versions of all files are on the [`hardened` branch](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/tree/hardened).**  
> This file provides a structured index of what was fixed and why.

---

## Summary Table

| # | File | Finding | Severity | Fix Applied (hardened branch) |
|---|------|---------|----------|------------------------------|
| 1 | `src/vulnerable_app.py` | SQL Injection — f-string in SQLite query | Critical | Parameterised queries with `?` placeholder |
| 2 | `src/vulnerable_app.py` | Command Injection — `subprocess.check_output(shell=True)` | Critical | Removed `shell=True`; `shlex.split()`; hostname allowlist |
| 3 | `src/vulnerable_app.py` | SSTI — user input in `render_template_string()` | Critical | Static template with context variable; input never passed to engine |
| 4 | `src/vulnerable_app.py` | Path Traversal — no validation on `/read_file` | High | `os.path.abspath()` check; explicit file allowlist |
| 5 | `src/vulnerable_app.py` | Hardcoded credentials (`DATABASE_PASSWORD`, `API_KEY`) | Critical | Replaced with `os.environ.get()`; secrets sourced from AWS Secrets Manager |
| 6 | `src/vulnerable_app.py` | Debug mode enabled (`debug=True`) | High | `debug=False`; served via gunicorn in production |
| 7 | `src/vulnerable_app.py` | Insecure YAML deserialisation (`yaml.load`) | High | Replaced with `yaml.safe_load()` |
| 8 | `requirements.txt` | CVE-2020-14343 — PyYAML 5.4.1 (CVSS 9.8) | Critical | Upgraded to PyYAML 6.0.1 |
| 9 | `requirements.txt` | CVEs in Flask 2.0.1 | High | Upgraded to Flask 3.0.x |
| 10 | `terraform/main.tf` | S3 public access blocks all disabled | Critical | All four `block_public_*` settings enabled |
| 11 | `terraform/main.tf` | Security group `0.0.0.0/0` all ports ingress + egress | Critical | Ingress restricted to port 443/5000 specific CIDRs; egress restricted |
| 12 | `terraform/main.tf` | EC2 root volume `encrypted = false` | High | `encrypted = true` with AWS KMS CMK |
| 13 | `terraform/main.tf` | `associate_public_ip_address = true` | High | Moved EC2 to private subnet behind ALB |
| 14 | `terraform/main.tf` | Hardcoded `DB_PASSWORD` in EC2 `user_data` | Critical | Replaced with `aws_secretsmanager_secret_version` data source |
| 15 | `Dockerfile` | No `USER` instruction — runs as root | Critical | `RUN useradd -m appuser && USER appuser` |
| 16 | `Dockerfile` | Unpinned base image (`python:3.9`) | High | Pinned to `python:3.9-slim@sha256:<verified digest>` — switches to slim base, eliminating ~3,900 transitive OS-level CVEs |
| 17 | `Dockerfile` | Unnecessary packages (curl, wget, vim, net-tools) | High | Removed all; `python:3.9-slim` base no longer ships them |
| 18 | `Dockerfile` | No `HEALTHCHECK` instruction | Medium | Added `HEALTHCHECK` with appropriate interval and threshold |
| 19 | `Dockerfile` | Shell-form `CMD` — SIGTERM not forwarded | Low | Exec-form `CMD ["gunicorn", ...]` |
| 20 | `.github/workflows/` | Actions pinned to floating tags — remediated in v1.2 | High → Residual: Low | All Actions pinned to immutable commit SHAs; quarterly SHA rotation recommended |

---

## CodeQL-Identified Findings in Remediated Code

During CI on the hardened branch, CodeQL identified 3 additional High severity findings inside `src/remediated_app.py` itself — the file written to fix the original vulnerabilities. These were caught, triaged, and fixed in v1.2. This is the pipeline working exactly as intended: catching residual issues even in security-engineered code.

| # | File | Finding | Severity | Root Cause | Fix Applied |
|---|------|---------|----------|------------|-------------|
| 21 | `src/remediated_app.py` | Reflected XSS — `/greet` endpoint | High | Fixing SSTI by removing `render_template_string()` introduced a new issue: user input was returned in an f-string with `Content-Type: text/plain`. CodeQL's taint analysis correctly flagged the unescaped user value in the response. | Added `import html` and wrapped the name with `html.escape()` before it appears in the response. Any HTML special characters (`<`, `>`, `"`, `&`) are now encoded as entities, neutralising both the original SSTI and the reflected XSS. |
| 22 | `src/remediated_app.py` | Reflected XSS — `/load_config` endpoint | High | `return str(config)` reflected the parsed user-supplied YAML back in the response body. Even though `yaml.safe_load()` prevents code execution, returning user-controlled data in the response is a reflected XSS vector. | Changed the response to a fixed status string: `"Config loaded successfully."` User input is now consumed (parsed and validated) but never echoed back. |
| 23 | `src/remediated_app.py` | Uncontrolled path expression — `/read_file` endpoint | High | The initial fix used `os.path.basename(filename)` to strip traversal sequences before constructing the path. CodeQL's inter-procedural data flow analysis traced the taint from `request.args` through `basename()` → `join()` → `realpath()` → `open()` and flagged it: user input still ultimately reached the filesystem call. | Replaced the sanitisation approach with an explicit `ALLOWED_FILES` dict mapping safe keys to hardcoded literal paths. User input is now used only as a dict lookup key — the value passed to `open()` is always a compile-time string constant. Taint chain fully severed. |

---

## Bandit — Accepted Risk and `nosec` Rationale

Bandit runs against `src/remediated_app.py` on the `hardened` branch and is expected to exit `0` (zero findings). All HIGH and MEDIUM severity findings from `src/vulnerable_app.py` are fully remediated in the hardened version. One LOW severity finding remains and is formally accepted.

### Findings in `src/vulnerable_app.py` (intentional — `main` branch)

| Rule | Finding | Severity | Confidence | Status |
|------|---------|----------|------------|--------|
| B201 | `app.run(debug=True)` — Flask debug mode exposes the Werkzeug interactive debugger | HIGH | HIGH | Remediated: `debug=False` in `remediated_app.py` |
| B506 | `yaml.load()` with `FullLoader` — arbitrary Python object deserialisation | MEDIUM | HIGH | Remediated: replaced with `yaml.safe_load()` |
| B602 | `subprocess.check_output(..., shell=True)` — shell metacharacter injection | HIGH | HIGH | Remediated: endpoint removed entirely |
| B106 | Hardcoded password string assigned to `DATABASE_PASSWORD` | LOW | MEDIUM | Remediated: replaced with `os.environ.get()` |
| B104 | `app.run(host='0.0.0.0')` — binding to all network interfaces | LOW | MEDIUM | Accepted with `# nosec B104` (see below) |

### Accepted Risk: B104 in `src/remediated_app.py`

```python
app.run(host='0.0.0.0', port=5000, debug=False)  # nosec B104
```

**Rule:** B104 — Possible binding to all interfaces  
**Severity:** LOW | **Confidence:** MEDIUM

**Why it is accepted and not suppressed silently:**

B104 flags any `host='0.0.0.0'` binding as a potential exposure because it makes the socket reachable on all network interfaces, not just localhost. In a VM or bare-metal environment this is a real concern — the process is reachable from any network the host is connected to.

In a containerised deployment, this finding does not represent a real risk for two reasons:

1. **`app.run()` is never the production entrypoint.** The container uses `CMD ["gunicorn", "--bind", "0.0.0.0:5000", "remediated_app:app"]`. The `if __name__ == '__main__':` block containing `app.run()` is only executed during local development, never inside the container.
2. **Container networking is the actual boundary.** Port exposure is controlled by `docker run -p` or the orchestrator (ECS task definition, Kubernetes Service). A container binding to all internal interfaces does not bypass this — it is a necessary condition for the port mapping to work at all.

**Why `# nosec` rather than removing the line:**

Removing `app.run()` entirely would prevent local development without Docker. The correct response to a known-acceptable finding is `# nosec <rule>` with a written justification — this is a first-class Bandit mechanism that makes the decision auditable. It appears in Bandit's suppression report and in code review, unlike `|| true` which discards the exit code silently with no traceability.

---

## Viewing the Hardened Code

To compare the vulnerable and hardened versions of any file:

```bash
# Clone the repo
git clone https://github.com/AurelienKumarathas/devsecops-pipeline-project-1.git
cd devsecops-pipeline-project-1

# Compare a specific file between branches
git diff main hardened -- src/vulnerable_app.py
git diff main hardened -- terraform/main.tf
git diff main hardened -- Dockerfile
```

Or view directly on GitHub:  
[github.com/AurelienKumarathas/devsecops-pipeline-project-1/compare/main...hardened](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/compare/main...hardened)

---

## Related Documents

| Document | Description |
|----------|-------------|
| [reports/threat-model-report.md](reports/threat-model-report.md) | Full threat model with executive summary and architecture |
| [reports/analyses/stride-threats.md](reports/analyses/stride-threats.md) | STRIDE threat register — all 21 threats |
| [reports/analyses/mitre-mapping.md](reports/analyses/mitre-mapping.md) | MITRE ATT&CK technique mapping |
| [reports/analyses/kill-chain-analysis.md](reports/analyses/kill-chain-analysis.md) | End-to-end attack chain analysis |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
