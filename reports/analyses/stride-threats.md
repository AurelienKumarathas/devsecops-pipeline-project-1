# STRIDE Threat Register — NexusCore Technologies

**Version:** 1.1  
**Total Threats:** 31  
**Methodology:** STRIDE per component

---

## A — Spoofing (5 threats)

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| S1 | Flask API | Attacker replays stolen session token to impersonate authenticated merchant | High | Implement JWT expiry + rotation; bind tokens to IP/user-agent |
| S2 | GitHub Actions | Attacker spoofs a trusted GitHub Actions workflow by forking and crafting a malicious PR | High | Require branch protection; pin Actions to commit SHA |
| S3 | AWS IAM | Attacker uses stolen `AWS_ACCESS_KEY_ID` (hardcoded in source) to impersonate CI/CD service role | Critical | Rotate all credentials immediately; use OIDC for GitHub Actions → AWS auth |
| S4 | Docker Registry | Attacker publishes a malicious image with the same tag as the production image (`python:3.9`) | Critical | Pin all base images to immutable digest (`@sha256:...`) |
| S5 | RDS | Attacker connects to PostgreSQL using hardcoded `DB_PASSWORD` found in source | Medium | Remove hardcoded credentials; use AWS Secrets Manager |

---

## B — Tampering (6 threats)

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| T1 | CI/CD Pipeline | Attacker with write access modifies `.github/workflows/devsecops-pipeline.yml` to disable security gates | Critical | Require PR reviews for workflow changes; use CODEOWNERS |
| T2 | Source Code | Attacker injects malicious commit to `vulnerable_app.py` via compromised developer account | Critical | Enforce signed commits (GPG); require 2 reviewers |
| T3 | Terraform IaC | Attacker modifies `terraform/main.tf` to open additional ports or disable encryption before `terraform apply` | Critical | IaC changes require security review; use Sentinel policy-as-code |
| T4 | S3 Bucket | Attacker overwrites card payment exports in S3 after gaining access via misconfigured bucket policy | High | Enable S3 Object Lock; enable versioning |
| T5 | Docker Image | Unpinned `python:3.9` base image silently updated by upstream to include a malicious layer | High | Pin base image; verify digest in CI |
| T6 | Dependencies | CVE-2020-14343 — PyYAML 5.4.1 arbitrary code execution via YAML deserialization | Medium | Upgrade to PyYAML ≥ 6.0; add Trivy to block on Critical CVEs |

---

## C — Repudiation (4 threats)

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| R1 | AWS CloudTrail | Attacker disables CloudTrail logging to remove evidence of credential abuse | Critical | Enable CloudTrail with S3 log integrity validation; alert on disable events |
| R2 | Flask API | No request logging — attacker can exfiltrate data via SQL injection with no audit trail | High | Implement structured logging (request ID, user ID, endpoint, status) |
| R3 | GitHub Actions | Pipeline runs with no tamper-evident log export — attacker can delete run logs | High | Export SARIF and job logs to immutable S3 archive |
| R4 | RDS | No query logging enabled — SQL injection activity leaves no database audit trail | Medium | Enable RDS PostgreSQL `log_statement = all`; ship to CloudWatch |

---

## D — Information Disclosure (7 threats)

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| I1 | Source Code | `AWS_SECRET_ACCESS_KEY`, `DB_PASSWORD`, `API_KEY` hardcoded in `vulnerable_app.py` and `terraform/main.tf` | Critical | Use AWS Secrets Manager / environment variables; Gitleaks blocks this in CI |
| I2 | Flask API | SQL injection on `/user?name=` endpoint dumps full `users` table including password hashes | Critical | Parameterise all queries; principle of least privilege on DB user |
| I3 | Flask API | SSTI via `render_template_string()` — attacker can read environment variables including secrets | Critical | Never pass user input to template engine; use static templates |
| I4 | S3 Bucket | Public access blocks disabled — unauthenticated HTTP GET downloads card payment exports | Critical | Enable all four S3 `block_public_*` settings; bucket policy denies non-VPC access |
| I5 | Flask API | Debug mode enabled (`debug=True`) — stack traces with file paths and env vars exposed to users | High | Set `debug=False` in production; use a WSGI server (gunicorn) |
| I6 | Docker Container | Container runs as root — any RCE exposes entire filesystem including mounted secrets | High | Add `USER appuser` to Dockerfile; use read-only filesystem |
| I7 | GitHub Repo | Public repository exposes intentional vulnerabilities — ensure fake credentials are clearly marked | Medium | README warning added; all credentials are dummy values validated by Gitleaks |

---

## E — Denial of Service (5 threats)

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| D1 | Flask API | `/ping` endpoint with `shell=True` — attacker passes `;:(){ :|:& };:` fork bomb payload | Critical | Remove `shell=True`; use `shlex.split()` + allowlist of permitted commands |
| D2 | RDS | SQL injection used to execute long-running queries (`SLEEP`, `pg_sleep`) causing connection exhaustion | High | Parameterise queries; set query timeout on DB connection pool |
| D3 | ECS | Container with no resource limits — runaway process consumes all CPU/memory on Fargate task | High | Set `cpu` and `memory` limits in ECS task definition |
| D4 | S3 | Attacker repeatedly requests large S3 objects — cost-based DoS via egress billing | Medium | Enable S3 request metrics; set billing alerts; consider CloudFront CDN |
| D5 | GitHub Actions | Pipeline with no timeout — malicious workflow step hangs indefinitely consuming Actions minutes | Medium | Set `timeout-minutes` on all jobs and steps |

---

## E — Elevation of Privilege (4 threats)

| ID | Component | Threat | Severity | Mitigation |
|----|-----------|--------|----------|------------|
| E1 | Docker Container | Container runs as root (`no USER` instruction) — container escape grants host-level privileges | Critical | `USER appuser` in Dockerfile; `--read-only` filesystem; drop all capabilities |
| E2 | AWS IAM | CI/CD role has overly broad IAM permissions — compromised pipeline can escalate to `AdministratorAccess` | Critical | Apply least-privilege IAM; use permission boundaries; audit with IAM Access Analyzer |
| E3 | Terraform | Security group allows all inbound/outbound on `0.0.0.0/0` — attacker can reach any internal service | High | Restrict to known CIDR ranges; separate security groups per service tier |
| E4 | EC2 Root Volume | `encrypted = false` on root EBS volume — physical access or snapshot leak exposes full OS disk | Medium | Set `encrypted = true`; use AWS KMS CMK |

### E5 — Insider Threat: Bulk Export (UBA Detection Triggers)

Scenario: A malicious or compromised internal user with legitimate access to the NexusCore merchant data API performs a bulk exfiltration of cardholder records.

**User Behaviour Analytics (UBA) detection triggers — alert on any of the following:**

| # | Trigger | Threshold | Severity |
|---|---------|-----------|----------|
| 1 | Bulk record export in a single session | > 500 records in one session | Critical |
| 2 | Off-hours access | Any access outside 07:00–21:00 local time | High |
| 3 | Access from new or unrecognised geolocation | First access from a new country/city | High |
| 4 | Patient/merchant records accessed outside assigned list | > 3 records outside authorised scope | High |
| 5 | API calls at machine speed | > 20 requests/second sustained for ≥ 10 seconds | Critical |

**Recommended controls:**
- Integrate with AWS CloudTrail + Athena for API call volume analysis
- SIEM rule: alert when any single IAM principal triggers ≥ 2 of the above in a 30-minute window
- Apply field-level encryption on sensitive columns (PAN, CVV) so even authorised access returns masked data by default
- Require step-up MFA for exports > 100 records

---

## Threat Count Verification

| Category | Count |
|----------|-------|
| Spoofing | 5 |
| Tampering | 6 |
| Repudiation | 4 |
| Information Disclosure | 7 |
| Denial of Service | 5 |
| Elevation of Privilege | 4 (+ E5 insider scenario) |
| **Total** | **31** |
