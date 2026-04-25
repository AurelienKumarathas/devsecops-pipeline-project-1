# MITRE ATT&CK Mapping — NexusCore Technologies

**Version:** 1.1  
**Coverage:** 12 of 12 tactics (100%)

---

## Full Tactic Mapping

| # | Tactic | Technique ID | Technique Name | Threat Scenario | Attack Chain |
|---|--------|--------------|----------------|-----------------|---------------|
| 1 | Initial Access | T1190 | Exploit Public-Facing Application | SQL injection / SSTI via Flask API — attacker crafts malicious HTTP request to `/user` or `/render` endpoint | Chain 1, 2, 3 |
| 2 | Initial Access | T1195 | Supply Chain Compromise | CVE-2020-14343 in PyYAML 5.4.1 — malicious YAML payload triggers arbitrary code execution during dependency load | Chain 2 |
| 3 | Execution | T1059 | Command and Script Interpreter | Command injection via `subprocess.check_output(shell=True)` in `/ping` endpoint — attacker executes OS commands | Chain 1, 3 |
| 4 | Execution | T1203 | Exploitation for Client Execution | SSTI via `render_template_string()` — Jinja2 expression in URL achieves RCE inside container | Chain 1 |
| 5 | Persistence | T1525 | Implant Internal Image | Attacker with write access to GitHub Actions injects malicious step into CI/CD pipeline, persisting backdoor in container images | Chain 2 |
| 6 | Persistence | T1078 | Valid Accounts | Hardcoded credentials (`hashicorp-tf-password`, `generic-api-key`) allow attacker to authenticate as legitimate service | Chain 1, 3 |
| 7 | Privilege Escalation | T1611 | Escape to Host | Container runs as root (no `USER` instruction) — container escape via kernel exploit grants host-level privileges | Chain 3 |
| 8 | Privilege Escalation | T1078 | Valid Accounts | Stolen IAM credentials used to assume higher-privilege role via AWS STS | Chain 1 |
| 9 | Defence Evasion | T1562 | Impair Defenses | Attacker disables CloudTrail logging or modifies S3 bucket policy to suppress audit trail | Chain 3 |
| 10 | Defence Evasion | T1036 | Masquerading | Malicious dependency published under a typosquatted package name to evade SCA scanning | Chain 2 |
| 11 | Credential Access | T1552 | Unsecured Credentials | Hardcoded `AWS_SECRET_ACCESS_KEY` and `DB_PASSWORD` in source code — exposed via GitHub public repo | Chain 1, 3 |
| 12 | Credential Access | T1212 | Exploitation for Credential Access | SQL injection dumps `users` table including password hashes from RDS PostgreSQL | Chain 1 |
| 13 | Discovery | T1083 | File and Directory Discovery | Path traversal vulnerability allows attacker to enumerate container filesystem | Chain 1 |
| 14 | Discovery | T1526 | Cloud Service Discovery | Overly permissive IAM policy allows attacker to enumerate all S3 buckets and EC2 instances | Chain 3 |
| 15 | **Lateral Movement** | **T1021** | **Remote Services** | **Attacker pivots from compromised ECS container to RDS PostgreSQL using stolen DB credentials — direct TCP connection to database port enables ransomware encryption of patient/merchant data** | **Chain 3** |
| 16 | Collection | T1530 | Data from Cloud Storage Object | Misconfigured S3 bucket (public access blocks disabled) allows unauthenticated bulk download of card payment exports | Chain 1, 3 |
| 17 | Collection | T1213 | Data from Information Repositories | SQL injection used to exfiltrate full merchant and cardholder records from RDS | Chain 1 |
| 18 | Exfiltration | T1537 | Transfer Data to Cloud Account | Attacker copies exfiltrated RDS data to attacker-controlled S3 bucket via AWS CLI using stolen credentials | Chain 3 |
| 19 | **Command and Control** | **T1071** | **Application Layer Protocol** | **HTTPS-based C2 traffic blends with normal application traffic — malware installed via container escape communicates with attacker infrastructure over port 443, evading network-layer controls** | **Chain 3** |
| 20 | Impact | T1486 | Data Encrypted for Impact | Ransomware encrypts RDS PostgreSQL data after lateral movement via T1021 — NexusCore loses access to all merchant transaction records | Chain 3 |
| 21 | Impact | T1485 | Data Destruction | Attacker deletes S3 bucket versioning then overwrites objects — card payment exports permanently destroyed | Chain 3 |
| 22 | Impact | T1499 | Endpoint Denial of Service | Unrestricted `/ping` endpoint with `shell=True` used to fork-bomb container, causing ECS task failure and service outage | Chain 1 |

---

## Tactic Coverage Summary

| Tactic | Techniques Mapped | Status |
|--------|-------------------|--------|
| Initial Access | T1190, T1195 | ✅ Covered |
| Execution | T1059, T1203 | ✅ Covered |
| Persistence | T1525, T1078 | ✅ Covered |
| Privilege Escalation | T1611, T1078 | ✅ Covered |
| Defence Evasion | T1562, T1036 | ✅ Covered |
| Credential Access | T1552, T1212 | ✅ Covered |
| Discovery | T1083, T1526 | ✅ Covered |
| Lateral Movement | T1021 | ✅ Covered (added v1.1) |
| Collection | T1530, T1213 | ✅ Covered |
| Exfiltration | T1537 | ✅ Covered |
| Command and Control | T1071 | ✅ Covered (added v1.1) |
| Impact | T1486, T1485, T1499 | ✅ Covered |
| **Total** | **22 techniques** | **12 of 12 (100%)** |

> **v1.0 coverage was 10 of 12 (83%).** T1021 (Lateral Movement) and T1071 (Command & Control) were identified as gaps and closed in v1.1.

---

## Attack Chain Summary

### Chain 1 — Credential Theft & Data Exfiltration
`T1190 (SQLi) → T1552 (Hardcoded Creds) → T1212 (SQLi Credential Dump) → T1530 (S3 Exfil)`

### Chain 2 — Supply Chain Compromise
`T1195 (Malicious Dependency) → T1525 (CI/CD Implant) → T1036 (Masquerading)`

### Chain 3 — Ransomware via Container Escape
`T1190 (Initial Access) → T1611 (Container Escape) → T1021 (RDS Lateral Movement) → T1071 (HTTPS C2) → T1486 (Ransomware Encryption)`
