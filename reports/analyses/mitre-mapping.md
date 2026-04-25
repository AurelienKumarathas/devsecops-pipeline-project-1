# MITRE ATT&CK Mapping — NexusCore Technologies

**Version:** 1.1  
**Scope:** Grounded in confirmed vulnerabilities in `src/vulnerable_app.py`, `Dockerfile`, `terraform/main.tf`, `requirements.txt`, and `.github/workflows/devsecops-pipeline.yml`

---

## Technique Mapping

| # | Tactic | Technique ID | Technique Name | Threat Scenario (repo-grounded) | Source File |
|---|--------|--------------|----------------|--------------------------------|-------------|
| 1 | Initial Access | T1190 | Exploit Public-Facing Application | SQL injection via `/user?username=` (f-string concatenation); SSTI via `/greet?name=` (render_template_string); path traversal via `/read_file?file=` | `src/vulnerable_app.py` |
| 2 | Initial Access | T1195 | Supply Chain Compromise | CVE-2020-14343 in PyYAML 5.4.1 — malicious YAML payload triggers code execution in `/load_config` endpoint; unpinned `python:3.9` base image silently updated by upstream | `requirements.txt`, `Dockerfile` |
| 3 | Execution | T1059 | Command and Script Interpreter | Command injection via `/ping?host=` — `subprocess.check_output(shell=True)` executes arbitrary OS commands passed via HTTP parameter | `src/vulnerable_app.py` |
| 4 | Execution | T1203 | Exploitation for Client Execution | SSTI via `render_template_string()` — Jinja2 expression `{{7*7}}` in URL achieves remote code execution inside the container | `src/vulnerable_app.py` |
| 5 | Persistence | T1525 | Implant Internal Image | Attacker who compromises the CI/CD pipeline (floating Action tags: `trivy-action@master`) injects a backdoor step into the workflow, persisting a malicious layer in built container images | `.github/workflows/devsecops-pipeline.yml` |
| 6 | Persistence | T1078 | Valid Accounts | Hardcoded `DATABASE_PASSWORD` and `API_KEY` in `vulnerable_app.py`; hardcoded `DB_PASSWORD` in Terraform `user_data` — attacker authenticates as a legitimate service account indefinitely | `src/vulnerable_app.py`, `terraform/main.tf` |
| 7 | Privilege Escalation | T1611 | Escape to Host | Container has no `USER` instruction — runs as root (UID 0); kernel exploit or misconfigured volume mount grants host-level access on the EC2 instance | `Dockerfile` |
| 8 | Privilege Escalation | T1078 | Valid Accounts | Stolen IAM credentials (from hardcoded secrets or EC2 instance metadata exposure via SSRF) used to assume a higher-privilege IAM role | `terraform/main.tf` |
| 9 | Defence Evasion | T1562 | Impair Defenses | Attacker with IAM access disables CloudTrail or modifies the S3 bucket policy to suppress the audit trail before exfiltration | `terraform/main.tf` |
| 10 | Defence Evasion | T1036 | Masquerading | Malicious dependency published under a typosquatted package name bypasses Trivy SCA if the exact CVE database entry has not been populated | `requirements.txt` |
| 11 | Credential Access | T1552 | Unsecured Credentials | `DATABASE_PASSWORD = "super_secret_password_123"` and `API_KEY = "sk-1234567890abcdef"` hardcoded in source; `DB_PASSWORD` hardcoded in Terraform user_data — detected by Gitleaks | `src/vulnerable_app.py`, `terraform/main.tf` |
| 12 | Credential Access | T1212 | Exploitation for Credential Access | SQL injection on `/user?username=` dumps the full SQLite `users` table including any stored credentials | `src/vulnerable_app.py` |
| 13 | Discovery | T1083 | File and Directory Discovery | Path traversal on `/read_file?file=../../etc/passwd` — no path validation allows container filesystem enumeration | `src/vulnerable_app.py` |
| 14 | Discovery | T1526 | Cloud Service Discovery | EC2 instance with public IP and open security group (`0.0.0.0/0`) allows network-level enumeration of all listening ports; S3 bucket name is guessable from Terraform config | `terraform/main.tf` |
| 15 | Lateral Movement | T1021 | Remote Services | Attacker with access to the EC2 instance (via container escape + root on host) uses the hardcoded `DB_PASSWORD` from user_data to authenticate to any database or internal service reachable via the open security group | `terraform/main.tf`, `Dockerfile` |
| 16 | Collection | T1530 | Data from Cloud Storage Object | S3 bucket has all public access blocks disabled — unauthenticated `aws s3 cp` or HTTP GET collects all stored objects | `terraform/main.tf` |
| 17 | Collection | T1213 | Data from Information Repositories | SQL injection exfiltrates the full SQLite database; path traversal reads arbitrary files from the container filesystem | `src/vulnerable_app.py` |
| 18 | Exfiltration | T1537 | Transfer Data to Cloud Account | Attacker uses stolen IAM credentials to copy exfiltrated data to an attacker-controlled S3 bucket via AWS CLI | `terraform/main.tf` |
| 19 | Command and Control | T1071 | Application Layer Protocol | Malware installed post-container-escape communicates with C2 infrastructure over HTTPS (port 443) — the security group allows all outbound traffic, and unnecessary tools (curl, wget) are available in the container for payload delivery | `Dockerfile`, `terraform/main.tf` |
| 20 | Impact | T1485 | Data Destruction | Attacker with S3 access deletes all objects in the publicly accessible bucket — no versioning or Object Lock configured | `terraform/main.tf` |
| 21 | Impact | T1499 | Endpoint Denial of Service | Fork bomb via `/ping?host=;:(){ :|:& };:` — `shell=True` executes the payload, exhausting processes and crashing the container | `src/vulnerable_app.py` |

---

## Tactic Coverage

| Tactic | Techniques Mapped | Grounded In |
|--------|-------------------|-------------|
| Initial Access | T1190, T1195 | `vulnerable_app.py`, `requirements.txt`, `Dockerfile` |
| Execution | T1059, T1203 | `vulnerable_app.py` |
| Persistence | T1525, T1078 | `devsecops-pipeline.yml`, `vulnerable_app.py`, `main.tf` |
| Privilege Escalation | T1611, T1078 | `Dockerfile`, `main.tf` |
| Defence Evasion | T1562, T1036 | `main.tf`, `requirements.txt` |
| Credential Access | T1552, T1212 | `vulnerable_app.py`, `main.tf` |
| Discovery | T1083, T1526 | `vulnerable_app.py`, `main.tf` |
| Lateral Movement | T1021 | `main.tf`, `Dockerfile` |
| Collection | T1530, T1213 | `main.tf`, `vulnerable_app.py` |
| Exfiltration | T1537 | `main.tf` |
| Command and Control | T1071 | `Dockerfile`, `main.tf` |
| Impact | T1485, T1499 | `main.tf`, `vulnerable_app.py` |

---

## Attack Chains

### Chain 1 — Credential Theft & Data Exfiltration
```
T1190 (SQL injection via /user)
  → T1212 (dump SQLite users table)
  → T1552 (hardcoded API_KEY used to authenticate)
  → T1530 (exfiltrate S3 objects — public bucket)
```
*All steps grounded in `vulnerable_app.py` and `terraform/main.tf`.*

### Chain 2 — Supply Chain Compromise via CI/CD
```
T1195 (malicious PyYAML or python:3.9 base image)
  → T1525 (inject malicious step via floating trivy-action@master)
  → T1036 (typosquatted package name bypasses SCA)
```
*Grounded in `requirements.txt`, `Dockerfile`, `.github/workflows/devsecops-pipeline.yml`.*

### Chain 3 — Container Escape → EC2 Host → Data Destruction
```
T1190 (command injection via /ping shell=True)
  → T1611 (container escape — root user, open security group)
  → T1021 (lateral movement using hardcoded DB_PASSWORD from EC2 user_data)
  → T1071 (C2 over HTTPS — curl/wget available, all outbound allowed)
  → T1485 (destroy S3 objects — no versioning or Object Lock)
```
*Grounded in `vulnerable_app.py`, `Dockerfile`, `terraform/main.tf`.*
