# REMEDIATION.md — NexusCore DevSecOps Pipeline

This document explains every vulnerability in the intentionally insecure files, what was fixed in the hardened versions, and why the fix works at a technical level. It mirrors the before/after structure used in the companion [Terraform Security project](https://github.com/AurelienKumarathas/terraform-aws-security-audit).

---

## Overview

| File | Vulnerable Version | Hardened Version |
|------|--------------------|------------------|
| Dockerfile | `Dockerfile` | `Dockerfile.hardened` |
| Flask application | `src/vulnerable_app.py` | `src/remediated_app.py` |

---

## Dockerfile Remediations

### 1. Unpinned Base Image (`FROM python:3.9`)

**Vulnerability**: Using a mutable tag like `:3.9` or `:latest` means the base image can change between builds without any change to your source code. A compromised upstream image silently becomes part of your supply chain.

**Fix**: Pin to a specific image digest:
```dockerfile
# BEFORE
FROM python:3.9

# AFTER
FROM python:3.9-slim@sha256:<digest>
```

**Why it works**: A digest is a cryptographic hash of the exact image manifest. If the upstream image is tampered with, the digest will not match and the build will fail rather than silently pulling a malicious image.

**MITRE ATT&CK**: T1195.002 — Compromise Software Supply Chain

---

### 2. Running as Root (no `USER` instruction)

**Vulnerability**: Docker containers run as root by default. If an attacker achieves Remote Code Execution inside the container (e.g., via the command injection in vulnerable_app.py), they immediately have root privileges — making container escape and host pivot significantly easier.

**Fix**: Create a dedicated low-privilege user and switch to it before the `CMD`:
```dockerfile
# BEFORE
# (no USER instruction — runs as root)

# AFTER
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/sh --no-create-home appuser
USER appuser
```

**Why it works**: The principle of least privilege. The application process has only the permissions it needs. Even if code execution is achieved, the attacker operates as a restricted user rather than root.

**CIS Docker Benchmark**: 4.1 — Ensure a user for the container has been created

---

### 3. Unnecessary Packages (vim, wget, net-tools, curl)

**Vulnerability**: Every binary installed in a container is a potential tool for an attacker who has achieved initial access. `wget` and `curl` enable downloading additional payloads; `net-tools` provides network reconnaissance capability; `vim` can be used to edit files or as a GTFObin for privilege escalation.

**Fix**: Remove all packages not required at runtime:
```dockerfile
# BEFORE
RUN apt-get update && apt-get install -y \
    curl wget vim net-tools

# AFTER
# (removed entirely — slim base provides no unnecessary tools)
```

**Why it works**: Attack surface reduction. An attacker who achieves code execution in a stripped container has far fewer local tools available. This does not prevent exploitation but significantly increases post-exploitation cost.

---

### 4. Shell Form CMD

**Vulnerability**: `CMD python src/app.py` uses shell form, which spawns `/bin/sh -c python src/app.py`. The SIGTERM signal from `docker stop` hits the shell wrapper, not the Python process. The Python app never receives a graceful shutdown signal and is killed after the stop timeout.

**Fix**: Use exec form:
```dockerfile
# BEFORE
CMD python src/vulnerable_app.py

# AFTER
CMD ["python", "src/remediated_app.py"]
```

**Why it works**: Exec form runs the process directly as PID 1. SIGTERM is delivered directly to Python, allowing graceful shutdown (closing DB connections, finishing in-flight requests). This also eliminates the shell as an intermediary process.

---

## Flask Application Remediations

### 1. Hardcoded Credentials

**Vulnerability**: `DATABASE_PASSWORD = "super_secret_password_123"` and `API_KEY = "sk-1234567890abcdef"` committed to source control. Once a secret is in git history it is compromised permanently — even if deleted in a later commit, it remains in the git log and in any forks or clones taken before deletion.

**Fix**: Load from environment variables:
```python
# BEFORE
DATABASE_PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"

# AFTER
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
API_KEY = os.environ.get("API_KEY", "")
```

**In production**: Environment variables are injected at runtime via AWS Secrets Manager, HashiCorp Vault, or Kubernetes Secrets (encrypted at rest). The application never holds the secret in source code.

**OWASP**: A02:2021 — Cryptographic Failures

---

### 2. SQL Injection

**Vulnerability**:
```python
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)
```
An attacker who controls `username` can inject arbitrary SQL. Input of `' OR '1'='1` returns every row. Input of `'; DROP TABLE users; --` destroys the table.

**Fix**: Parameterised queries:
```python
# BEFORE
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)

# AFTER
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

**Why it works**: The DB driver sends the query text and parameters separately to the database engine. The engine never concatenates them — user input is always treated as a literal value, never as SQL syntax.

**OWASP**: A03:2021 — Injection | **CVSSv3**: 9.8 Critical

---

### 3. Command Injection (`subprocess` with `shell=True`)

**Vulnerability**:
```python
result = subprocess.check_output(f"ping -c 1 {host}", shell=True)
```
`shell=True` passes the full string to `/bin/sh`. Input of `8.8.8.8; cat /etc/passwd` executes as two shell commands.

**Fix**: Endpoint removed entirely. There is no safe way to pass arbitrary user-controlled strings to a shell command. If ping functionality is genuinely required, it must be implemented without `shell=True` and with strict input validation against an allowlist of IP addresses using `ipaddress.ip_address()`.

**OWASP**: A03:2021 — Injection | **CVSSv3**: 9.8 Critical

---

### 4. Server-Side Template Injection (SSTI)

**Vulnerability**:
```python
template = f"<h1>Hello {name}!</h1>"
return render_template_string(template)
```
User input interpolated into a Jinja2 template string allows template expression injection. Input of `{{7*7}}` returns `49`. Input of `{{config}}` leaks the Flask config. A polyglot payload achieves full RCE.

**Fix**: Return a plain text response without template rendering:
```python
# BEFORE
return render_template_string(f"<h1>Hello {name}!</h1>")

# AFTER
return f"Hello {name}!", 200, {'Content-Type': 'text/plain; charset=utf-8'}
```

**OWASP**: A03:2021 — Injection | **CVSSv3**: 9.8 Critical

---

### 5. Insecure YAML Deserialization

**Vulnerability**:
```python
config = yaml.load(config_data, Loader=yaml.FullLoader)
```
Even with `FullLoader`, `yaml.load` can deserialise Python objects via YAML tags. A payload of `!!python/object/apply:os.system ["id"]` executes arbitrary OS commands.

**Fix**:
```python
# BEFORE
config = yaml.load(config_data, Loader=yaml.FullLoader)

# AFTER
config = yaml.safe_load(config_data)
```

**Why it works**: `yaml.safe_load` only deserialises standard YAML scalars, sequences, and mappings. It raises a `YAMLError` on any `!!python/` tag, preventing object instantiation entirely.

**CVE**: CVE-2020-14343 (PyYAML) | **CVSSv3**: 9.8 Critical

---

### 6. Path Traversal

**Vulnerability**:
```python
with open(f"/app/files/{filename}", 'r') as f:
    return f.read()
```
Input of `../../etc/passwd` resolves to `/etc/passwd`. No validation is performed before the file is opened.

**Fix**: Resolve the absolute path and assert it is within the allowed directory:
```python
# BEFORE
with open(f"/app/files/{filename}", 'r') as f:

# AFTER
BASE_FILES_DIR = os.path.abspath("/app/files")
requested_path = os.path.realpath(os.path.join(BASE_FILES_DIR, filename))
if not requested_path.startswith(BASE_FILES_DIR + os.sep):
    abort(400)
```

**Why it works**: `os.path.realpath` resolves all symlinks and `..` components before the check. If the resolved path does not start with the allowed base directory, the request is rejected before the file is opened.

**OWASP**: A01:2021 — Broken Access Control | **CVSSv3**: 7.5 High

---

### 7. Debug Mode Enabled in Production

**Vulnerability**:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```
`debug=True` enables the Werkzeug interactive debugger, which presents a full Python REPL on every unhandled exception page. An attacker who can trigger an exception has immediate code execution in the application context. It also enables the reloader, which watches for file changes and restarts the server — useful in development, dangerous in production.

**Fix**:
```python
# BEFORE
app.run(host='0.0.0.0', port=5000, debug=True)

# AFTER
app.run(host='0.0.0.0', port=5000, debug=False)
```

**In production**: Flask should be run behind a production WSGI server (gunicorn, uWSGI) rather than the built-in development server, which is single-threaded and not designed for production traffic.

---

## Security Scanning Results

The pipeline on the `main` branch intentionally fails on the vulnerable files — this validates that each security gate correctly detects the vulnerability class it is designed to catch. The hardened branch passes all gates.

| Tool | Vulnerable Branch Finding | Hardened Branch Status |
|------|--------------------------|------------------------|
| CodeQL | SQL Injection, Command Injection, SSTI | ✅ Clean |
| Trivy SCA | CVE-2020-14343 (Critical) in PyYAML | ✅ No Critical/High |
| Gitleaks | `generic-api-key`, `hashicorp-tf-password` | ✅ No secrets in code |
| Trivy Container | Root user, unpinned base image | ✅ Clean |

---

*For questions about methodology, see the [README](README.md) or the companion [Terraform Security project](https://github.com/AurelienKumarathas/terraform-aws-security-audit).*
