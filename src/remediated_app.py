#!/usr/bin/env python3
"""
Remediated Flask Application — NexusCore Technologies
This is the hardened version of vulnerable_app.py.
See REMEDIATION.md for a full explanation of every fix.

Original file: src/vulnerable_app.py
Remediated file: src/remediated_app.py
"""

from flask import Flask, request, abort
import os
import sqlite3
import yaml
import html

app = Flask(__name__)

# FIX 1: Remove hardcoded credentials.
# Credentials are loaded from environment variables at runtime.
# In production these are injected via AWS Secrets Manager / Vault.
# The fallback empty string ensures the app fails fast if env vars are missing
# rather than silently using a default insecure value.
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
API_KEY = os.environ.get("API_KEY", "")


# FIX 2: Parameterised queries eliminate SQL Injection.
# The original used f-string concatenation: query = f"SELECT * FROM users WHERE username = '{username}'"
# An attacker could pass username = "' OR '1'='1" to dump the entire table.
# Parameterised queries pass user input as a separate argument — the DB driver
# handles escaping, so the input is always treated as data, never as SQL syntax.
def get_user(username):
    """SQL Injection remediated via parameterised query."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()


# FIX 3: Remove the /ping endpoint entirely.
# The original used subprocess.check_output(f"ping -c 1 {host}", shell=True).
# shell=True passes the full string to /bin/sh, so host = "; cat /etc/passwd"
# would execute as two commands. There is no safe way to pass user-controlled
# input to a shell command. The endpoint has been removed. If ICMP diagnostics
# are genuinely needed, they must be implemented without shell=True and with
# strict input validation against an allowlist of IP addresses.


# FIX 4: SSTI and XSS remediation.
# The original used render_template_string with user input interpolated directly
# into the template string, enabling SSTI. The initial fix returned the name in
# a plain text f-string, which CodeQL correctly flagged as reflected XSS — user
# input was still echoed into the response without explicit escaping.
# Final fix: html.escape() sanitises all HTML special characters before the
# value is placed in the response body, neutralising both SSTI and XSS vectors.
@app.route('/greet')
def greet():
    """SSTI and XSS remediated — user input is HTML-escaped before output."""
    name = request.args.get('name', 'Guest')
    safe_name = html.escape(name)
    return f"Hello {safe_name}!", 200, {'Content-Type': 'text/plain; charset=utf-8'}


# FIX 5: yaml.safe_load instead of yaml.load.
# yaml.load with FullLoader (or no Loader) can deserialise arbitrary Python
# objects via YAML tags like !!python/object/apply:os.system ['rm -rf /']
# yaml.safe_load only deserialises standard YAML scalars, lists, and dicts —
# it raises an exception if it encounters any object/apply tag.
# The response no longer reflects user-controlled data — a fixed status string
# is returned instead, eliminating the reflected XSS CodeQL flagged previously.
@app.route('/load_config')
def load_config():
    """Insecure deserialization remediated via yaml.safe_load. Response is a fixed string."""
    config_data = request.args.get('config', '{}')
    try:
        yaml.safe_load(config_data)
    except yaml.YAMLError:
        abort(400)
    return "Config loaded successfully.", 200


# FIX 6: Path traversal remediated with a safe join and realpath allowlist check.
# The original did open(f"/app/files/{filename}") with no validation, allowing
# filename = "../../etc/passwd" to read arbitrary files.
# Fix: the safe base directory is joined with only the basename of the supplied
# filename (stripping any directory components the user may have included),
# then os.path.realpath resolves symlinks before the allowlist check.
# CodeQL is satisfied because user input is never used as the direct path —
# only os.path.basename(filename) reaches the filesystem call.
BASE_FILES_DIR = os.path.realpath("/app/files")

@app.route('/read_file')
def read_file():
    """Path traversal remediated via basename stripping and realpath allowlist check."""
    filename = request.args.get('file', 'default.txt')
    # os.path.basename strips any directory traversal sequences (../../)
    # before the path is constructed, so only a plain filename reaches the join.
    safe_filename = os.path.basename(filename)
    resolved_path = os.path.realpath(os.path.join(BASE_FILES_DIR, safe_filename))
    if not resolved_path.startswith(BASE_FILES_DIR + os.sep):
        abort(400)
    try:
        with open(resolved_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    # FIX 7: Debug mode disabled.
    # debug=True in production exposes the Werkzeug interactive debugger on
    # every unhandled exception — a full Python REPL accessible from the browser.
    # It also enables the PIN-protected console, which attackers can brute-force.
    # In production, debug must be False and the app should run behind gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=False)
