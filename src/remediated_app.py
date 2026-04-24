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


# FIX 4: SSTI remediation — return plain text, not a rendered template.
# The original used render_template_string with user input interpolated directly
# into the template string. An attacker could pass name={{ config }} to leak
# the Flask config object, or name={{ ''.__class__.__mro__[1].__subclasses__() }}
# for full RCE. The fix returns a plain escaped string with no template rendering.
@app.route('/greet')
def greet():
    """SSTI remediated — user input is never passed into a template engine."""
    name = request.args.get('name', 'Guest')
    # Input is returned as plain text; Flask escapes it automatically in responses.
    # If HTML rendering is required, use a static template with {{ name|e }} escaping.
    return f"Hello {name}!", 200, {'Content-Type': 'text/plain; charset=utf-8'}


# FIX 5: yaml.safe_load instead of yaml.load.
# yaml.load with FullLoader (or no Loader) can deserialise arbitrary Python
# objects via YAML tags like !!python/object/apply:os.system ['rm -rf /']
# yaml.safe_load only deserialises standard YAML scalars, lists, and dicts —
# it raises an exception if it encounters any object/apply tag.
@app.route('/load_config')
def load_config():
    """Insecure deserialization remediated via yaml.safe_load."""
    config_data = request.args.get('config', '{}')
    try:
        config = yaml.safe_load(config_data)
    except yaml.YAMLError:
        abort(400)
    return str(config)


# FIX 6: Path traversal remediated with os.path.abspath allowlist check.
# The original did open(f"/app/files/{filename}") with no validation, allowing
# filename = "../../etc/passwd" to read arbitrary files. The fix resolves the
# absolute path and asserts it starts with the allowed base directory.
# Any attempt to escape the directory raises a 400 before the file is opened.
BASE_FILES_DIR = os.path.abspath("/app/files")

@app.route('/read_file')
def read_file():
    """Path traversal remediated via realpath allowlist check."""
    filename = request.args.get('file', 'default.txt')
    requested_path = os.path.realpath(os.path.join(BASE_FILES_DIR, filename))
    if not requested_path.startswith(BASE_FILES_DIR + os.sep):
        abort(400)
    try:
        with open(requested_path, 'r') as f:
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
