"""NotesApp coursework implementation: scoped access, AES-GCM, HMAC and Argon2.

This local teaching deployment still needs deployment-specific operations and
security review before handling real student records.
"""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import csv
import hmac
import io
import json
import os
import secrets
import subprocess
import sys

import psycopg2
from flask import (
    Flask, request, session, redirect, url_for, render_template,
    Response, jsonify, abort, g,
)
from werkzeug.exceptions import HTTPException

from database import get_db
from audit_log import AuditFailure, record_event
from comment_crypto import load_key, encrypt_comment, decrypt_comment
from csv_hmac import load_hmac_key, sign_csv, signed_archive
from password_security import hash_password, verify_password, hasher
from security import (
    ROLES, MAX_PASSWORD_LENGTH, MAX_COMMENT_LENGTH, LoginLimiter,
    load_secret, issue_token, decode_token, auth_version_value, positive_id, bounded_text,
    username_value, role_value, grade_value, csv_cell, loopback_host,
)

app = Flask(__name__)
app.secret_key = load_secret("SESSION_SECRET_FILE", "/run/secrets/session_key")
JWT_SECRET = load_secret("JWT_SECRET_FILE", "/run/secrets/jwt_key")
COMMENT_KEY = load_key()
CSV_HMAC_KEY = load_hmac_key()
_secure_cookie = os.environ.get("SESSION_COOKIE_SECURE", "true").lower()
if _secure_cookie not in {"true", "false"}:
    raise ValueError("SESSION_COOKIE_SECURE must be true or false")
app.config.update(
    SESSION_COOKIE_SECURE=_secure_cookie == "true",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    MAX_CONTENT_LENGTH=32 * 1024,
    MAX_FORM_PARTS=32,
)
login_limiter = LoginLimiter()
PAGE_SIZE = 100
MAX_SELECTOR_ROWS = 1000
MAX_EXPORT_ROWS = 1000
# Unknown users and legacy comparisons also perform an Argon2 verification.
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def log(event, *, actor=None, target=None, result="success", details=None, connection=None):
    """Persist the audit event before reporting success; stdout is a secondary copy."""
    try:
        record_event(actor=actor, action=event, target=target, outcome=result,
                     details=details, connection=connection)
    except AuditFailure:
        g.audit_failed = True
        print("AUDIT_WRITE_FAILED: operation refused.", file=sys.stderr, flush=True)
        raise
    g.audit_recorded = True
    print(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                      "event": event, "actor": actor, "target": target,
                      "result": result}, ensure_ascii=True), flush=True)


def audit(event, result="success", target=None, details=None, connection=None):
    identity = getattr(g, "identity", None)
    log(event, actor=identity["user_id"] if identity else None,
        target=target, result=result, details=details, connection=connection)


def make_jwt(payload):
    """Issue a short-lived token bound to the user's current revocation version."""
    user_id = positive_id(payload["user_id"])
    with closing(get_db()) as conn, conn.cursor() as cur:
        cur.execute("SELECT auth_version FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    if not row:
        raise ValueError("Unknown user")
    return issue_token(user_id, JWT_SECRET, row["auth_version"])


def verify_jwt(token):
    return decode_token(token, JWT_SECRET)


def current_identity():
    """An explicit invalid Authorization header can never fall back to cookies."""
    if "identity" in g:
        return g.identity
    auth = request.headers.get("Authorization")
    user_id = None
    auth_version = None
    if auth is not None:
        parts = auth.split()
        claims = verify_jwt(parts[1]) if len(parts) == 2 and parts[0].lower() == "bearer" else None
        if not claims:
            abort(401)
        user_id = claims["user_id"]
        auth_version = claims["ver"]
    elif session.get("user_id") is not None:
        try:
            user_id = positive_id(session["user_id"])
            auth_version = auth_version_value(session.get("auth_version"))
        except ValueError:
            session.clear()
            user_id = None
    if user_id is None:
        g.identity = None
        return None
    with closing(get_db()) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, username, role, auth_version FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    if not row or row["role"] not in ROLES or row["auth_version"] != auth_version:
        if auth is not None:
            abort(401)
        session.clear()
        g.identity = None
        return None
    g.identity = {"user_id": row["id"], "username": row["username"],
                  "role": row["role"], "auth_version": row["auth_version"]}
    if auth is None:
        session["username"] = row["username"]
        session["role"] = row["role"]
    return g.identity


def require_identity(*roles):
    identity = current_identity()
    if not identity:
        abort(401)
    if roles and identity["role"] not in roles:
        abort(403)
    return identity


def login_required(role=None):
    """Compatibility helper; authorization uses the freshly loaded DB role."""
    identity = current_identity()
    return bool(identity and (role is None or identity["role"] == role))


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@app.context_processor
def template_security():
    return {"csrf_token": csrf_token}


@app.before_request
def protect_request():
    g.csp_nonce = secrets.token_urlsafe(18)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        expected = session.get("csrf_token", "")
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        if (not isinstance(expected, str) or not isinstance(supplied, str)
                or not expected or len(supplied) > 128
                or not hmac.compare_digest(expected.encode(), supplied.encode())):
            audit("csrf", "denied")
            abort(400)
    if request.endpoint not in {"static", "healthz"}:
        current_identity()


@app.after_request
def response_security(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'nonce-" + getattr(g, "csp_nonce", "")
        + "'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    )
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"
    if (not getattr(g, "audit_failed", False) and not getattr(g, "audit_recorded", False)
            and (request.method not in {"GET", "HEAD", "OPTIONS"} or response.status_code >= 400)):
        audit(request.endpoint or "unknown_route", str(response.status_code), getattr(g, "audit_target", None))
    return response


@app.errorhandler(HTTPException)
def http_error(error):
    # Use fixed messages; never reflect SQL, exception text or submitted values.
    messages = {400: "Invalid request.", 401: "Authentication required.",
                403: "Access denied.", 404: "Not found.", 405: "Method not allowed.",
                409: "The requested change conflicts with existing records.",
                413: "Request too large.", 429: "Please try again later."}
    return jsonify({"error": messages.get(error.code, "Request failed.")}), error.code


@app.errorhandler(Exception)
def internal_error(error):
    if isinstance(error, AuditFailure):
        return jsonify({"error": "Audit storage unavailable; the operation was not completed."}), 503
    try:
        audit("internal_error", "failed")
    except AuditFailure:
        return jsonify({"error": "Audit storage unavailable; the operation was not completed."}), 503
    return jsonify({"error": "The request could not be completed."}), 500


def note_scope(identity):
    """SQL fragment for queries using the fixed aliases n (notes), c (classes)."""
    if identity["role"] == "admin":
        return "TRUE", ()
    if identity["role"] == "teacher":
        return "c.teacher_id = %s", (identity["user_id"],)
    return "n.student_id = %s", (identity["user_id"],)


def class_scope(identity):
    if identity["role"] == "admin":
        return "TRUE", ()
    return "c.teacher_id = %s", (identity["user_id"],)


def decrypt_notes(rows):
    for row in rows:
        row["comment"] = decrypt_comment(row["comment"], row["id"], COMMENT_KEY)
    return rows


def checked(parser, value):
    try:
        return parser(value)
    except ValueError:
        abort(400)


def page_cursor(name="after"):
    value = request.args.get(name, "0")
    return 0 if value == "0" else checked(positive_id, value)


def page_rows(rows):
    page = rows[:PAGE_SIZE]
    next_cursor = page[-1]["id"] if len(rows) > PAGE_SIZE else None
    return page, next_cursor


def selector_rows(cur):
    rows = cur.fetchall()
    if len(rows) > MAX_SELECTOR_ROWS:
        abort(413)
    return rows


@app.route("/")
def index():
    identity = current_identity()
    if not identity:
        return redirect(url_for("login"))
    return redirect(url_for({"student": "dashboard", "teacher": "teacher", "admin": "admin"}[identity["role"]]))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            username_value(username)
            bounded_text(password, MAX_PASSWORD_LENGTH, required=True)
        except ValueError:
            return render_template("login.html", error="Invalid credentials."), 401
        # Do not trust caller-supplied X-Forwarded-For headers.
        if not login_limiter.allow(request.remote_addr or "unknown", username):
            audit("login", "rate_limited")
            response = app.make_response((render_template("login.html", error="Invalid credentials."), 429))
            response.headers["Retry-After"] = str(login_limiter.window)
            return response
        with closing(get_db()) as conn:
            conn.autocommit = False
            with conn, conn.cursor() as cur:
                cur.execute("SELECT id, username, role, password, auth_version FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                authenticated = False
                needs_upgrade = False
                if row and row["role"] in ROLES:
                    stored = row["password"]
                    if stored.startswith("$argon2"):
                        authenticated = verify_password(stored, password)
                        needs_upgrade = authenticated and hasher.check_needs_rehash(stored)
                    else:
                        verify_password(_DUMMY_PASSWORD_HASH, password)
                        authenticated = hmac.compare_digest(stored.encode(), password.encode())
                        needs_upgrade = authenticated
                    if authenticated and needs_upgrade:
                        cur.execute("UPDATE users SET password = %s WHERE id = %s AND password = %s",
                                    (hash_password(password), row["id"], stored))
                        authenticated = cur.rowcount == 1
                        if authenticated:
                            log("password_upgrade", actor=row["id"], target={"user_id": row["id"]},
                                details={"fields": ["password_hash"]}, connection=conn)
                else:
                    verify_password(_DUMMY_PASSWORD_HASH, password)
                if authenticated:
                    log("login", actor=row["id"], target={"user_id": row["id"]}, connection=conn)
                else:
                    log("login", result="denied", connection=conn)
        if authenticated:
            session.clear()  # Rotate CSRF/session state after authentication.
            session.permanent = True
            session.update(user_id=row["id"], username=row["username"], role=row["role"],
                           auth_version=row["auth_version"],
                           token=issue_token(row["id"], JWT_SECRET, row["auth_version"]))
            csrf_token()
            g.identity = {"user_id": row["id"], "username": row["username"],
                          "role": row["role"], "auth_version": row["auth_version"]}
            return redirect(url_for("index"))
        error = "Invalid credentials."
        return render_template("login.html", error=error), 401
    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
def logout():
    identity = require_identity()
    with closing(get_db()) as conn:
        conn.autocommit = False
        with conn, conn.cursor() as cur:
            # A concurrent logout may already have revoked this exact version.
            cur.execute("UPDATE users SET auth_version = auth_version + 1 "
                        "WHERE id = %s AND auth_version = %s",
                        (identity["user_id"], identity["auth_version"]))
            audit("logout_all_sessions", target={"user_id": identity["user_id"]},
                  details={"fields": ["auth_version"]}, connection=conn)
    session.clear()
    g.identity = None
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    identity = require_identity("student")
    after = page_cursor()
    with closing(get_db()) as conn, conn.cursor() as cur:
        cur.execute("SELECT n.id, n.grade, n.comment, c.name AS class_name "
                    "FROM notes n JOIN classes c ON c.id = n.class_id "
                    "WHERE n.student_id = %s AND n.id > %s ORDER BY n.id LIMIT %s",
                    (identity["user_id"], after, PAGE_SIZE + 1))
        notes, next_cursor = page_rows(cur.fetchall())
        decrypt_notes(notes)
        audit("dashboard_read", target={"note_ids": [row["id"] for row in notes]}, connection=conn)
    return render_template("dashboard.html", notes=notes, after=after, next_cursor=next_cursor)


@app.route("/api/notes/<int:note_id>")
def api_notes(note_id):
    identity = require_identity()
    checked(positive_id, note_id)
    scope, params = note_scope(identity)
    with closing(get_db()) as conn, conn.cursor() as cur:
        cur.execute("SELECT n.id, n.student_id, n.class_id, n.grade, n.comment, "
                    "u.username AS student, c.name AS class_name "
                    "FROM notes n JOIN users u ON u.id = n.student_id "
                    "JOIN classes c ON c.id = n.class_id WHERE n.id = %s AND " + scope,
                    (note_id,) + params)
        note = cur.fetchone()
    if not note:
        abort(404)
    decrypt_notes([note])
    note["grade"] = float(note["grade"]) if note["grade"] is not None else None
    audit("api_note_read", target={"note_id": note_id})
    return jsonify(note)


@app.route("/teacher")
def teacher():
    identity = require_identity("teacher", "admin")
    after = page_cursor()
    scope, params = class_scope(identity)
    with closing(get_db()) as conn, conn.cursor() as cur:
        cur.execute("SELECT c.id, c.name, c.teacher_id FROM classes c WHERE " + scope
                    + " ORDER BY c.id LIMIT %s", params + (MAX_SELECTOR_ROWS + 1,))
        classes = selector_rows(cur)
        cur.execute("SELECT n.id, n.grade, n.comment, n.student_id, n.class_id, "
                    "u.username AS student, c.name AS class_name "
                    "FROM notes n JOIN users u ON u.id = n.student_id "
                    "JOIN classes c ON c.id = n.class_id WHERE " + scope
                    + " AND n.id > %s ORDER BY n.id LIMIT %s", params + (after, PAGE_SIZE + 1))
        notes, next_cursor = page_rows(cur.fetchall())
        decrypt_notes(notes)
        cur.execute("SELECT DISTINCT u.id, u.username FROM users u "
                    "JOIN enrollments e ON e.student_id = u.id JOIN classes c ON c.id = e.class_id "
                    "WHERE u.role = 'student' AND " + scope + " ORDER BY u.id LIMIT %s",
                    params + (MAX_SELECTOR_ROWS + 1,))
        students = selector_rows(cur)
        audit("teacher_read", target={"note_ids": [row["id"] for row in notes],
                                      "class_ids": [row["id"] for row in classes],
                                      "user_ids": [row["id"] for row in students]}, connection=conn)
    return render_template("teacher.html", classes=classes, notes=notes, students=students,
                           after=after, next_cursor=next_cursor)


@app.route("/grades", methods=["POST"])
def grades():
    identity = require_identity("teacher", "admin")
    note_id_text = request.form.get("note_id", "").strip()
    note_id = checked(positive_id, note_id_text) if note_id_text else None
    grade = checked(grade_value, request.form.get("grade", ""))
    comment = checked(lambda value: bounded_text(value, MAX_COMMENT_LENGTH), request.form.get("comment", ""))
    scope, params = class_scope(identity)
    with closing(get_db()) as conn:
        conn.autocommit = False
        with conn, conn.cursor() as cur:
            if note_id:
                # Lock and check the existing target. Submitted student/class fields
                # cannot reassign a note to a different enrollment.
                cur.execute("SELECT n.id, n.grade, n.comment FROM notes n JOIN classes c ON c.id = n.class_id "
                            "JOIN users u ON u.id = n.student_id WHERE n.id = %s AND " + scope
                            + " AND u.role = 'student' AND EXISTS (SELECT 1 FROM enrollments e "
                            "WHERE e.student_id = n.student_id AND e.class_id = n.class_id) FOR UPDATE OF n",
                            (note_id,) + params)
                existing = cur.fetchone()
                if not existing:
                    abort(404)
                previous_grade = str(existing["grade"]) if existing["grade"] is not None else None
                comment_changed = decrypt_comment(existing["comment"], note_id, COMMENT_KEY) != comment
                cur.execute("UPDATE notes SET grade = %s, comment = %s WHERE id = %s",
                            (grade, encrypt_comment(comment, note_id, COMMENT_KEY), note_id))
            else:
                student_id = checked(positive_id, request.form.get("student_id"))
                class_id = checked(positive_id, request.form.get("class_id"))
                cur.execute("INSERT INTO notes (student_id, class_id, grade, comment) "
                            "SELECT u.id, c.id, %s, NULL FROM users u JOIN classes c ON c.id = %s "
                            "WHERE u.id = %s AND u.role = 'student' AND " + scope
                            + " AND EXISTS (SELECT 1 FROM enrollments e WHERE e.student_id = u.id "
                            "AND e.class_id = c.id) RETURNING id", (grade, class_id, student_id) + params)
                inserted = cur.fetchone()
                if not inserted:
                    abort(404)
                note_id = inserted["id"]
                previous_grade = None
                comment_changed = True
                cur.execute("UPDATE notes SET comment = %s WHERE id = %s",
                            (encrypt_comment(comment, note_id, COMMENT_KEY), note_id))
            audit("grade_write", target={"note_id": note_id},
                  details={"fields": ["grade", "comment"], "grade_before": previous_grade,
                           "grade_after": str(grade), "comment_changed": comment_changed}, connection=conn)
    return redirect(url_for("teacher"))


@app.route("/export.csv")
def export_csv():
    identity = require_identity("teacher", "admin")
    scope, params = class_scope(identity)
    class_id = request.args.get("class_id")
    if class_id is not None:
        class_id = checked(positive_id, class_id)
    signed = request.args.get("signed", "0")
    if signed not in {"0", "1"}:
        abort(400)
    with closing(get_db()) as conn, conn.cursor() as cur:
        if class_id is not None:
            cur.execute("SELECT c.id FROM classes c WHERE c.id = %s AND " + scope, (class_id,) + params)
            if not cur.fetchone():
                abort(404)
            scope += " AND c.id = %s"
            params += (class_id,)
        cur.execute("SELECT n.id, u.username AS student, c.name AS class, n.grade, n.comment "
                    "FROM notes n JOIN users u ON u.id = n.student_id "
                    "JOIN classes c ON c.id = n.class_id WHERE " + scope
                    + " ORDER BY c.name, u.username, n.id LIMIT %s", params + (MAX_EXPORT_ROWS + 1,))
        rows = cur.fetchall()
        if len(rows) > MAX_EXPORT_ROWS:
            abort(413)
        decrypt_notes(rows)
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["student", "class", "grade", "comment"])
    for row in rows:
        writer.writerow([csv_cell(row[key]) for key in ("student", "class", "grade", "comment")])
    payload = buf.getvalue().encode("utf-8")
    audit("csv_export", target={"class_id": class_id, "note_ids": [row["id"] for row in rows]})
    if signed == "1":
        return Response(signed_archive(payload, CSV_HMAC_KEY), mimetype="application/zip",
                        headers={"Content-Disposition": "attachment; filename=grades-signed.zip"})
    return Response(payload, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=grades.csv",
                             "X-CSV-HMAC-SHA256": sign_csv(payload, CSV_HMAC_KEY)})


def admin_data():
    users_after = page_cursor("users_after")
    classes_after = page_cursor("classes_after")
    with closing(get_db()) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, username, role, teacher_id FROM users WHERE id > %s ORDER BY id LIMIT %s",
                    (users_after, PAGE_SIZE + 1))
        users, users_next = page_rows(cur.fetchall())
        cur.execute("SELECT id, name, teacher_id FROM classes WHERE id > %s ORDER BY id LIMIT %s",
                    (classes_after, PAGE_SIZE + 1))
        classes, classes_next = page_rows(cur.fetchall())
        audit("admin_read", target={"user_ids": [row["id"] for row in users],
                                    "class_ids": [row["id"] for row in classes]}, connection=conn)
    return {"users": users, "classes": classes, "users_after": users_after,
            "classes_after": classes_after, "users_next": users_next, "classes_next": classes_next}


@app.route("/admin")
def admin():
    require_identity("admin")
    return render_template("admin.html", **admin_data())


@app.route("/admin/ping", methods=["POST"])
def admin_ping():
    require_identity("admin")
    host = checked(loopback_host, request.form.get("host", ""))
    try:
        completed = subprocess.run(["ping", "-c", "1", host], shell=False,
                                   capture_output=True, text=True, timeout=3, check=False)
        output = "Local loopback check succeeded." if completed.returncode == 0 else "Local loopback check failed."
    except (OSError, subprocess.TimeoutExpired):
        output = "Local loopback check unavailable."
    audit("loopback_check", target={"loopback": host},
          result="success" if "succeeded" in output else "failed")
    return render_template("admin.html", ping_result=output, **admin_data())


@app.route("/admin/users", methods=["POST"])
def admin_users():
    identity = require_identity("admin")
    action = request.form.get("action")
    if action not in {"create", "delete"}:
        abort(400)
    try:
        with closing(get_db()) as conn:
            conn.autocommit = False
            with conn, conn.cursor() as cur:
                if action == "create":
                    username = checked(username_value, request.form.get("username", ""))
                    role = checked(role_value, request.form.get("role", ""))
                    password = checked(lambda value: bounded_text(value, MAX_PASSWORD_LENGTH, required=True),
                                       request.form.get("password", ""))
                    if len(password) < 12:
                        abort(400)
                    cur.execute("INSERT INTO users (username, password, role, teacher_id) "
                                "VALUES (%s, %s, %s, NULL) RETURNING id", (username, hash_password(password), role))
                    user_id = cur.fetchone()["id"]
                else:
                    user_id = checked(positive_id, request.form.get("user_id"))
                    if user_id == identity["user_id"]:
                        abort(409)
                    cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
                    if not cur.fetchone():
                        abort(404)
                audit("user_" + action, target={"user_id": user_id},
                      details={"fields": ["username", "role", "teacher_id", "password_hash"]}, connection=conn)
    except psycopg2.IntegrityError:
        abort(409)
    return redirect(url_for("admin"))


@app.route("/healthz")
def healthz():
    try:
        with closing(get_db()) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return "ok", 200
    except psycopg2.Error:
        audit("health", "unavailable")
        return "unavailable", 503


if __name__ == "__main__":
    # TLS terminates at nginx; the deployment does not publish this internal port.
    app.run(host="0.0.0.0", port=5000, debug=False)
