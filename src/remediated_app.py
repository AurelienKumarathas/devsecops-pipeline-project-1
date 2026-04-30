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
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
API_KEY = os.environ.get("API_KEY", "")


# FIX 2: Parameterised queries eliminate SQL Injection.
# The original used f-string concatenation allowing ' OR '1'='1 style attacks.
# Parameterised queries pass user input as a separate argument to the DB driver
# so it is always treated as data, never as executable SQL syntax.
def get_user(username):
    """SQL Injection remediated via parameterised query."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()


# FIX 3: Remove the /ping endpoint entirely.
# The original used subprocess.check_output(f"ping -c 1 {host}", shell=True).
# There is no safe way to pass user-controlled input to a shell command.
# The endpoint has been removed. ICMP diagnostics must be implemented
# without shell=True and with an IP allowlist if genuinely required.


# FIX 4: SSTI and XSS remediation.
# The original used render_template_string with user input directly in the
# template string, enabling SSTI. The fix applies html.escape() to sanitise
# all HTML special characters before the value appears in the response body,
# neutralising both SSTI and reflected XSS vectors.
@app.route('/greet')
def greet():
    """SSTI and XSS remediated — user input is HTML-escaped before output."""
    name = request.args.get('name', 'Guest')
    safe_name = html.escape(name)
    return f"Hello {safe_name}!", 200, {'Content-Type': 'text/plain; charset=utf-8'}


# FIX 5: yaml.safe_load instead of yaml.load.
# yaml.load can deserialise arbitrary Python objects via YAML tags such as
# !!python/object/apply:os.system ['rm -rf /'], enabling RCE.
# yaml.safe_load only deserialises standard scalars, lists, and dicts.
# The response no longer reflects user input — a fixed status string is
# returned, eliminating the reflected XSS CodeQL previously flagged.
@app.route('/load_config')
def load_config():
    """Insecure deserialization remediated via yaml.safe_load."""
    config_data = request.args.get('config', '{}')
    try:
        yaml.safe_load(config_data)
    except yaml.YAMLError:
        abort(400)
    return "Config loaded successfully.", 200


# FIX 6: Path traversal remediated via explicit allowlist.
# The original did open(f"/app/files/{filename}") with no validation.
# The basename() approach in the previous iteration still allowed CodeQL's
# taint analysis to trace user input all the way to the open() call.
# Final fix: user input is used only as a lookup key in a hardcoded dict.
# The value passed to open() is always a literal string from ALLOWED_FILES —
# user input never touches the filesystem path. Taint chain fully severed.
ALLOWED_FILES = {
    "readme": "/app/files/readme.txt",
    "config": "/app/files/config.txt",
    "info":   "/app/files/info.txt",
}

@app.route('/read_file')
def read_file():
    """Path traversal remediated via explicit file allowlist."""
    file_key = request.args.get('file', '')
    filepath = ALLOWED_FILES.get(file_key)
    if filepath is None:
        abort(400)
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    # FIX 7: Debug mode disabled.
    # debug=True exposes the Werkzeug interactive debugger — a full Python REPL
    # accessible from the browser on every unhandled exception.
    # In production, debug must be False and the app should run behind gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=False)
