# STRIDE Threat Register — NexusCore Technologies

**Version:** 1.2  
**Scope:** Flask app (`src/vulnerable_app.py`), Dockerfile, `terraform/main.tf`, GitHub Actions pipeline  
**Methodology:** STRIDE per component  
**All threats grounded in confirmed vulnerabilities in this repository.**

---

## S — Spoofing

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| S1 | GitHub Actions | Attacker with a leaked `GITHUB_TOKEN` (e.g. from a public Actions log) impersonates the CI/CD service to trigger pipeline runs or read repository secrets | High | Restrict `GITHUB_TOKEN` permissions to minimum required per job; rotate on exposure |
| S2 | GitHub Actions | Attacker spoofs a trusted workflow by targeting an unpinned action — **previously `aquasecurity/trivy-action@master`; remediated in v1.2 by pinning all Actions to immutable commit SHAs. Residual risk: pinned SHAs become stale as upstream releases security patches.** | Low (Residual) | Maintain SHA pinning; use Dependabot for automated SHA update PRs; review quarterly |
| S3 | AWS IAM | Attacker uses hardcoded `DB_PASSWORD` from `terraform/main.tf` user_data to impersonate the EC2 application service | Critical | Remove all hardcoded credentials; use AWS Secrets Manager or IAM instance profiles |
| S4 | Docker Registry | Attacker publishes a malicious image update under the mutable `python:3.9` tag, silently replacing the base image on the next build | Critical | Pin base image to an immutable SHA digest (`FROM python:3.9@sha256:...`) |
| S5 | Flask API | Attacker provides a crafted `API_KEY` matching the hardcoded value in `vulnerable_app.py` to impersonate a trusted internal client | Medium | Remove hardcoded credentials; issue scoped API keys via a secrets manager |

---

## T — Tampering

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| T1 | CI/CD Pipeline | Attacker with write access modifies `.github/workflows/devsecops-pipeline.yml` to disable security gates or inject a malicious step. **Actions were previously pinned to floating tags (`@master`, `@v2`, `@v3`), making this trivially exploitable via an upstream compromise — remediated in v1.2 by pinning all Actions to immutable commit SHAs. Residual risk: SHAs must be reviewed and rotated periodically as upstream actions release security patches.** | High (Residual) | Require PR reviews for workflow changes; use CODEOWNERS; rotate pinned SHAs quarterly via Dependabot |
| T2 | Source Code | Attacker injects a malicious commit to `vulnerable_app.py` via a compromised developer account | Critical | Enforce signed commits (GPG); require 2 reviewers on all PRs; enable branch protection |
| T3 | Terraform IaC | Attacker modifies `terraform/main.tf` to open additional ports or remove the `encrypted = false` marker before `terraform apply` | Critical | IaC changes require a security review gate; use Sentinel/OPA policy-as-code |
| T4 | S3 Bucket | Attacker overwrites objects in the S3 bucket (public access blocks all disabled in `terraform/main.tf`) after gaining access via the open security group | High | Enable all four `block_public_*` settings; enable S3 Object Lock and versioning |
| T5 | Docker Image | Unpinned `python:3.9` base image (`Dockerfile` line 12) silently updated by upstream to include a malicious layer | High | Pin base image to SHA digest; verify digest in CI |
| T6 | Dependencies | CVE-2020-14343 in PyYAML 5.4.1 (`requirements.txt`) — CVSS 9.8 Critical — arbitrary code execution via YAML deserialisation in `load_config` endpoint | Critical | Upgrade PyYAML to ≥ 6.0; configure Trivy to block on Critical severity |

---

## R — Repudiation

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| R1 | AWS CloudTrail | Attacker with IAM access disables CloudTrail (enabled by default but not enforced via SCP/policy) to remove evidence of credential abuse via hardcoded EC2 user_data credentials | Critical | Enable CloudTrail with S3 log integrity validation; alert on disable events via CloudWatch |
| R2 | Flask API | No request logging in `vulnerable_app.py` — SQL injection and path traversal exploitation leave no audit trail | High | Implement structured request logging (request ID, endpoint, source IP, status code) |
| R3 | GitHub Actions | Pipeline run logs can be deleted by a repo admin — no tamper-evident log export | High | Export SARIF reports and job logs to an immutable S3 archive on every run |
| R4 | Flask API | No SQL query logging — SQL injection activity via the `/user` endpoint leaves no database audit trail (SQLite, no query log facility) | Medium | Add application-level query logging wrapping all `cursor.execute()` calls; ship to a log aggregator |

---

## I — Information Disclosure

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| I1 | Source Code | `DATABASE_PASSWORD` and `API_KEY` hardcoded in `vulnerable_app.py`; `DB_PASSWORD` hardcoded in `terraform/main.tf` user_data — all detected by Gitleaks | Critical | Use AWS Secrets Manager or environment variables; Gitleaks gate blocks this in CI |
| I2 | Flask API | SQL injection on `/user?username=` endpoint — f-string concatenation allows full SQLite database dump | Critical | Parameterise all queries: `cursor.execute("SELECT * FROM users WHERE username = ?", (username,))` |
| I3 | Flask API | SSTI via `render_template_string()` in `/greet` — Jinja2 expression in URL parameter achieves RCE and environment variable disclosure | Critical | Never pass user input to a template engine; use a static template with `{{ name }}` passed as a context variable |
| I4 | S3 Bucket | All four public access blocks disabled in `terraform/main.tf` — unauthenticated HTTP GET can download any object | Critical | Enable `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets` |
| I5 | Flask API | `debug=True` in `app.run()` — stack traces including file paths, local variables, and environment variables exposed to all users | High | Set `debug=False`; serve via a production WSGI server (gunicorn) |
| I6 | Docker Container | No `USER` instruction in `Dockerfile` — container runs as root; any RCE immediately exposes entire filesystem including any mounted secrets | High | Add `RUN useradd -m appuser` and `USER appuser` before `CMD` |
| I7 | Flask API | Path traversal in `/read_file` — no validation on `filename` parameter allows reading any file accessible to the container process | High | Validate and sanitise the filename; restrict to an explicit allowlist of permitted files |

---

## D — Denial of Service

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| D1 | Flask API | `/ping` endpoint with `shell=True` — attacker passes a fork bomb payload (`;:(){ :\|:& };:`) causing process exhaustion and container crash | Critical | Remove `shell=True`; use `shlex.split()` and an allowlist of permitted hostnames |
| D2 | Flask API | Long-running SQLite queries injected via `/user` (e.g. recursive CTEs) cause connection blocking and application hang | High | Parameterise queries; set a connection timeout on the SQLite connection |
| D3 | EC2 Instance | No CloudWatch CPU/memory alarms on the EC2 instance — a fork bomb or resource exhaustion attack consumes host resources with no auto-recovery or alerting | High | Configure CloudWatch alarms for CPU > 80% sustained; use Auto Scaling or a watchdog process |
| D4 | S3 Bucket | Attacker repeatedly requests large objects from the publicly accessible S3 bucket — cost-based denial of service via AWS egress billing | Medium | Enable S3 request metrics; set billing alerts; restrict public access (see I4) |
| D5 | GitHub Actions | No `timeout-minutes` on any job in `devsecops-pipeline.yml` — **remediated in v1.3 by adding `timeout-minutes` to all jobs on both branches.** Residual risk: individual steps within jobs still lack per-step timeouts. | Low (Residual) | Add per-step `timeout-minutes` to long-running scan steps; monitor Actions usage minutes |

---

## E — Elevation of Privilege

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| E1 | Docker Container | No `USER` instruction — container runs as root (UID 0); container escape via kernel exploit or `--privileged` grants host-level privileges | Critical | `RUN useradd -m appuser && USER appuser`; add `--read-only` filesystem; drop all capabilities |
| E2 | AWS IAM | If the CI/CD pipeline's IAM role has overly broad permissions (common in demo setups), a compromised pipeline step can call `sts:AssumeRole` to escalate to higher-privilege roles | Critical | Apply least-privilege IAM; use permission boundaries; audit with IAM Access Analyzer |
| E3 | Terraform | Security group in `terraform/main.tf` allows all inbound and outbound on `0.0.0.0/0` — attacker reaching any open port can access all internal services on the EC2 instance | High | Restrict ingress to known CIDR ranges and specific ports (443, 5000); separate security groups per service tier |
| E4 | EC2 Root Volume | `encrypted = false` on root EBS volume (`terraform/main.tf`) — an EBS snapshot or physical access exposes the full OS disk including any in-memory secrets written to disk | Medium | Set `encrypted = true`; use an AWS KMS Customer Managed Key |

### E5 — Insider Threat: Bulk Cardholder Data Export

**Scenario:** A malicious or compromised internal user with legitimate access to the NexusCore payments API performs a bulk exfiltration of merchant or cardholder records via the `/user` endpoint or direct S3 access (the bucket is publicly accessible with no access controls).

**User Behaviour Analytics (UBA) detection triggers — alert on any of the following:**

| # | Trigger | Threshold | Severity |
|---|---------|-----------|----------|
| 1 | Bulk record export in a single session | > 500 merchant/cardholder records in one session | Critical |
| 2 | Off-hours access | Any access outside 07:00–21:00 local time | High |
| 3 | Access from new or unrecognised geolocation | First-ever access from a new country or city | High |
| 4 | Cardholder records accessed outside authorised scope | > 3 records outside the user's assigned merchant portfolio | High |
| 5 | API calls at machine speed | > 20 requests/second sustained for ≥ 10 seconds | Critical |

**Recommended controls:**
- AWS CloudTrail + Athena: query API call volume per IAM principal
- SIEM rule: alert when any single principal triggers ≥ 2 of the above triggers in a 30-minute window
- Require step-up MFA for bulk exports > 100 records
- Field-level masking on PAN/CVV so even authorised access returns masked data by default

**Why this threat is in scope here:** The S3 bucket in `terraform/main.tf` has all public access blocks disabled. An insider (or anyone with the bucket name) can exfiltrate all stored data with a single unauthenticated `aws s3 cp` command.
