"""Route regressions against an explicitly marked disposable PostgreSQL database.

Use scripts/verify.py. These tests refuse the existing coursework database. Each
test owns UUID-named fixtures; there are no assumptions about seed users or IDs.
"""
import csv
from html.parser import HTMLParser
import importlib
import io
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))

import jwt
from argon2 import PasswordHasher
from comment_crypto import PREFIX, decrypt_comment, encrypt_comment
from csv_hmac import verify_csv
from password_security import hash_password, verify_password
from security import JWT_AUDIENCE, JWT_ISSUER, LoginLimiter


class CsrfInputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tokens = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "input" and values.get("name") == "csrf_token":
            self.tokens.append(values.get("value", ""))


class DatabaseFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (os.environ.get("NOTESAPP_TEST_DATABASE") != "1"
                or os.environ.get("DB_NAME") != "notesapp_test"):
            raise RuntimeError(
                "Database tests require NOTESAPP_TEST_DATABASE=1 and DB_NAME=notesapp_test. "
                "Run python3 scripts/verify.py to create the isolated test stack."
            )
        cls.module = importlib.import_module("app")
        cls.module.app.config["TESTING"] = True
        cls.password = "Fixture-only-secret-42!"
        cls.password_hash = hash_password(cls.password)

    def query(self, sql, params=(), *, one=False, many=False):
        conn = self.module.get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                result = cur.fetchone() if one else cur.fetchall() if many else None
            conn.commit()
            return result
        finally:
            conn.close()

    def setUp(self):
        self.prefix = "fixture_" + uuid4().hex
        self.ids, self.names, self.classes, self.notes = {}, {}, {}, {}
        self.cleanup_usernames = []
        self.addCleanup(self.cleanup)
        self.module.login_limiter.reset()
        for role_key in ("student1", "student2", "unenrolled", "teacher1", "teacher2", "admin"):
            role = "student" if role_key in ("student1", "student2", "unenrolled") else role_key.rstrip("12")
            name = self.prefix + "_" + role_key
            self.names[role_key] = name
            self.cleanup_usernames.append(name)
            self.ids[role_key] = self.query(
                "INSERT INTO users(username,password,role) VALUES(%s,%s,%s) RETURNING id",
                (name, self.password_hash, role), one=True,
            )["id"]
        for number in (1, 2):
            self.classes[number] = self.query(
                "INSERT INTO classes(name,teacher_id) VALUES(%s,%s) RETURNING id",
                (self.prefix + "_class" + str(number), self.ids["teacher" + str(number)]), one=True,
            )["id"]
            self.query("INSERT INTO enrollments(student_id,class_id) VALUES(%s,%s)",
                       (self.ids["student" + str(number)], self.classes[number]))
            note_id = self.query(
                "INSERT INTO notes(student_id,class_id,grade,comment) VALUES(%s,%s,%s,NULL) RETURNING id",
                (self.ids["student" + str(number)], self.classes[number], "12.3"), one=True,
            )["id"]
            self.notes[number] = note_id
            self.set_comment(number, self.prefix + "_private" + str(number))
        self.client = self.module.app.test_client()

    def cleanup(self):
        class_ids = list(self.classes.values())
        if class_ids:
            self.query("DELETE FROM notes WHERE class_id = ANY(%s)", (class_ids,))
            self.query("DELETE FROM enrollments WHERE class_id = ANY(%s)", (class_ids,))
            self.query("DELETE FROM classes WHERE id = ANY(%s)", (class_ids,))
        if self.cleanup_usernames:
            self.query("DELETE FROM users WHERE username = ANY(%s)", (self.cleanup_usernames,))

    def csrf(self, client=None, path="/login"):
        client = client or self.client
        response = client.get(path, base_url="https://localhost")
        self.assertEqual(response.status_code, 200, "CSRF form must be accessible")
        parser = CsrfInputParser()
        parser.feed(response.get_data(as_text=True))
        self.assertTrue(parser.tokens and parser.tokens[0], "Form must carry a CSRF token")
        return parser.tokens[0]

    def post(self, path, data=None, *, client=None, form="/login"):
        client = client or self.client
        payload = dict(data or {})
        payload["csrf_token"] = self.csrf(client, form)
        return client.post(path, data=payload, base_url="https://localhost")

    def login(self, role="student1", *, client=None, password=None):
        client = client or self.client
        response = self.post("/login", {
            "username": self.names[role], "password": self.password if password is None else password,
        }, client=client)
        self.assertEqual(response.status_code, 302, "Fixture login must succeed")
        return client

    def stored_password(self, role="student1"):
        return self.query("SELECT password FROM users WHERE id=%s", (self.ids[role],), one=True)["password"]

    def note(self, number=1):
        return self.query("SELECT * FROM notes WHERE id=%s", (self.notes[number],), one=True)

    def set_comment(self, number, text):
        note_id = self.notes[number]
        self.query("UPDATE notes SET comment=%s WHERE id=%s", (
            encrypt_comment(text, note_id, self.module.COMMENT_KEY), note_id,
        ))

    def grade_data(self, number=1, **updates):
        data = {"note_id": str(self.notes[number]),
                "student_id": str(self.ids["student" + str(number)]),
                "class_id": str(self.classes[number]), "grade": "14.5", "comment": "Updated fixture"}
        data.update(updates)
        return data

    def token(self, role="student1"):
        return self.module.make_jwt({"user_id": self.ids[role]})

    def api(self, note_id, token, *, client=None):
        return (client or self.client).get(
            f"/api/notes/{note_id}", headers={"Authorization": "Bearer " + token},
            base_url="https://localhost",
        )


class LoginUpgradeTests(DatabaseFixture):
    def test_legacy_wrong_password_does_not_migrate_success_does(self):
        self.query("UPDATE users SET password=%s WHERE id=%s", (self.password, self.ids["student1"]))
        wrong = self.post("/login", {"username": self.names["student1"], "password": "wrong"})
        self.assertIn(wrong.status_code, (200, 401))
        self.assertEqual(self.stored_password(), self.password)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)
        self.login()
        encoded = self.stored_password()
        self.assertTrue(encoded.startswith("$argon2id$"))
        self.assertTrue(verify_password(encoded, self.password))
        self.assertEqual(self.post("/logout", form="/dashboard").status_code, 302)
        self.login()
        self.assertEqual(self.stored_password(), encoded, "A current hash must not be regenerated each login")

    def test_wrong_unknown_injection_and_malformed_hash_do_not_authenticate(self):
        before = self.stored_password()
        for username, password in (
            (self.names["student1"], "wrong"), (self.prefix + "_missing", self.password),
            ("' OR 1=1 --", self.password),
        ):
            with self.subTest(username=username):
                response = self.post("/login", {"username": username, "password": password})
                self.assertIn(response.status_code, (200, 400, 401))
                with self.client.session_transaction() as session:
                    self.assertNotIn("user_id", session)
        self.assertEqual(self.stored_password(), before)
        self.query("UPDATE users SET password=%s WHERE id=%s", ("$argon2id$broken", self.ids["student1"]))
        response = self.post("/login", {"username": self.names["student1"], "password": self.password})
        self.assertIn(response.status_code, (200, 401))
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)

    def test_outdated_argon_parameters_rehash_after_correct_login(self):
        old = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(self.password)
        self.query("UPDATE users SET password=%s WHERE id=%s", (old, self.ids["student1"]))
        self.login()
        refreshed = self.stored_password()
        self.assertNotEqual(refreshed, old)
        self.assertTrue(verify_password(refreshed, self.password))

    def test_login_endpoint_enforces_attempt_budget(self):
        limiter = LoginLimiter(per_ip=2, per_username=2)
        with patch.object(self.module, "login_limiter", limiter):
            for _ in range(2):
                response = self.post("/login", {"username": self.names["student1"], "password": "wrong"})
                self.assertIn(response.status_code, (200, 401))
            response = self.post("/login", {"username": self.names["student1"], "password": self.password})
            self.assertEqual(response.status_code, 429)
            with self.client.session_transaction() as session:
                self.assertNotIn("user_id", session)


class TokenAndSessionTests(DatabaseFixture):
    def test_invalid_tokens_never_fall_back_to_authenticated_session(self):
        self.login()
        now = int(time.time())
        claims = {"sub": str(self.ids["student1"]), "iat": now, "exp": now + 60,
                  "iss": JWT_ISSUER, "aud": JWT_AUDIENCE, "ver": 0}
        bad_tokens = {
            "unsigned": jwt.encode(claims, "", algorithm="none"),
            "wrong_key": jwt.encode(claims, os.urandom(32), algorithm="HS256"),
            "wrong_algorithm": jwt.encode(claims, self.module.JWT_SECRET, algorithm="HS384"),
            "expired": jwt.encode({**claims, "iat": now - 120, "exp": now - 60}, self.module.JWT_SECRET, algorithm="HS256"),
            "issuer": jwt.encode({**claims, "iss": "other"}, self.module.JWT_SECRET, algorithm="HS256"),
            "audience": jwt.encode({**claims, "aud": "other"}, self.module.JWT_SECRET, algorithm="HS256"),
            "subject": jwt.encode({**claims, "sub": "0"}, self.module.JWT_SECRET, algorithm="HS256"),
            "missing_exp": jwt.encode({k: v for k, v in claims.items() if k != "exp"}, self.module.JWT_SECRET, algorithm="HS256"),
            "missing_version": jwt.encode({k: v for k, v in claims.items() if k != "ver"}, self.module.JWT_SECRET, algorithm="HS256"),
            "negative_version": jwt.encode({**claims, "ver": -1}, self.module.JWT_SECRET, algorithm="HS256"),
            "boolean_version": jwt.encode({**claims, "ver": False}, self.module.JWT_SECRET, algorithm="HS256"),
            "string_version": jwt.encode({**claims, "ver": "0"}, self.module.JWT_SECRET, algorithm="HS256"),
            "unknown_version": jwt.encode({**claims, "ver": 1}, self.module.JWT_SECRET, algorithm="HS256"),
            "malformed": "not.a.valid.token",
        }
        for kind, token in bad_tokens.items():
            with self.subTest(kind=kind):
                self.assertEqual(self.api(self.notes[1], token).status_code, 401)

    def test_valid_token_enforces_ownership_and_database_role(self):
        token = self.token()
        own = self.api(self.notes[1], token)
        self.assertEqual(own.status_code, 200)
        self.assertIn(self.prefix + "_private1", own.get_data(as_text=True))
        self.assertIn(self.api(self.notes[2], token).status_code, (403, 404))
        claims = jwt.decode(token, options={"verify_signature": False})
        claims["role"] = "admin"
        claims["username"] = self.names["admin"]
        forged_role = jwt.encode(claims, self.module.JWT_SECRET, algorithm="HS256")
        self.assertIn(self.api(self.notes[2], forged_role).status_code, (403, 404))

    def test_deleted_user_token_and_admin_session_are_revoked(self):
        self.login("admin")
        token = self.token("admin")
        self.query("DELETE FROM users WHERE id=%s", (self.ids["admin"],))
        self.assertEqual(self.api(self.notes[1], token).status_code, 401)
        self.assertIn(self.client.get("/admin", base_url="https://localhost").status_code, (302, 401, 403))

    def test_demoted_admin_session_loses_privileges(self):
        self.login("admin")
        self.query("UPDATE users SET role=%s WHERE id=%s", ("student", self.ids["admin"]))
        self.assertIn(self.client.get("/admin", base_url="https://localhost").status_code, (302, 401, 403))

    def test_logout_revokes_copied_cookie_and_bearer_token(self):
        self.login()
        token = self.token()
        cookie_name = self.module.app.config["SESSION_COOKIE_NAME"]
        cookie = self.client.get_cookie(cookie_name).value
        copied = self.module.app.test_client()
        copied.set_cookie(cookie_name, cookie, domain="localhost")
        path = f"/api/notes/{self.notes[1]}"
        self.assertEqual(copied.get(path, base_url="https://localhost").status_code, 200)
        self.assertEqual(self.api(self.notes[1], token).status_code, 200)

        self.assertEqual(self.post("/logout", form="/dashboard").status_code, 302)
        self.assertEqual(copied.get(path, base_url="https://localhost").status_code, 401)
        self.assertEqual(self.api(self.notes[1], token).status_code, 401)
        self.assertEqual(self.client.get("/dashboard", base_url="https://localhost").status_code, 401)

    def test_new_login_after_logout_issues_working_new_credentials(self):
        self.login()
        previous_token = self.token()
        previous_claims = jwt.decode(previous_token, options={"verify_signature": False})
        self.assertEqual(self.post("/logout", form="/dashboard").status_code, 302)
        self.login()
        current_token = self.token()
        current_claims = jwt.decode(current_token, options={"verify_signature": False})
        self.assertEqual(current_claims["ver"], previous_claims["ver"] + 1)
        self.assertEqual(self.client.get("/dashboard", base_url="https://localhost").status_code, 200)
        self.assertEqual(self.api(self.notes[1], current_token).status_code, 200)
        self.assertEqual(self.api(self.notes[1], previous_token).status_code, 401,
                         "A new cookie must not make a revoked explicit bearer token valid")

    def test_dashboard_uses_cookie_when_previous_page_token_has_expired(self):
        self.login()
        claims = jwt.decode(self.token(), options={"verify_signature": False})
        now = int(time.time())
        expired = jwt.encode({**claims, "iat": now - 120, "exp": now - 60},
                             self.module.JWT_SECRET, algorithm="HS256")
        # A browser may keep a page open longer than a bearer token's lifetime;
        # retaining that old token must not break an otherwise valid session.
        with self.client.session_transaction() as session:
            session["token"] = expired
        response = self.client.get("/dashboard", base_url="https://localhost")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn(expired, body)
        self.assertNotIn("Bearer ", body)
        self.assertNotIn("Authorization", body)
        self.assertIn("credentials: 'same-origin'", body)
        detail = self.client.get(f"/api/notes/{self.notes[1]}", base_url="https://localhost")
        self.assertEqual(detail.status_code, 200)
        self.assertIn(self.prefix + "_private1", detail.get_data(as_text=True))
        self.assertEqual(self.api(self.notes[1], expired).status_code, 401)


class AuthorizationTests(DatabaseFixture):
    def test_teacher_lists_and_exports_only_owned_classes(self):
        self.login("teacher1")
        response = self.client.get("/teacher", base_url="https://localhost")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn(self.prefix + "_private1", body)
        self.assertNotIn(self.prefix + "_private2", body)
        self.assertNotIn(self.prefix + "_class2", body)
        export = self.client.get("/export.csv", base_url="https://localhost")
        self.assertEqual(export.status_code, 200)
        self.assertIn(self.names["student1"].encode(), export.data)
        self.assertNotIn(self.names["student2"].encode(), export.data)
        self.assertTrue(verify_csv(export.data, export.headers["X-CSV-HMAC-SHA256"],
                                   self.module.CSV_HMAC_KEY))
        forbidden = self.client.get(f"/export.csv?class_id={self.classes[2]}", base_url="https://localhost")
        self.assertIn(forbidden.status_code, (403, 404))
        self.assertIn(self.api(self.notes[2], self.token("teacher1")).status_code, (403, 404))

    def test_cross_teacher_update_and_insert_are_rejected(self):
        self.login("teacher1")
        before = self.note(2)
        for data in (self.grade_data(2), self.grade_data(2, note_id="")):
            response = self.post("/grades", data, form="/teacher")
            self.assertIn(response.status_code, (403, 404))
        self.assertEqual(self.note(2), before)

    def test_student_cannot_use_teacher_or_admin_routes(self):
        self.login()
        for path in ("/teacher", "/admin", "/export.csv"):
            with self.subTest(path=path):
                self.assertIn(self.client.get(path, base_url="https://localhost").status_code, (302, 403))
        response = self.post("/grades", self.grade_data(), form="/dashboard")
        self.assertIn(response.status_code, (302, 403))
        self.assertEqual(str(self.note()["grade"]), "12.3")


class CsrfTests(DatabaseFixture):
    def test_login_requires_correct_session_bound_csrf(self):
        token = self.csrf()
        for data in ({}, {"csrf_token": "invalid"}):
            response = self.client.post("/login", data={
                "username": self.names["student1"], "password": self.password, **data,
            }, base_url="https://localhost")
            self.assertIn(response.status_code, (400, 403))
        another = self.module.app.test_client()
        response = another.post("/login", data={
            "username": self.names["student1"], "password": self.password, "csrf_token": token,
        }, base_url="https://localhost")
        self.assertIn(response.status_code, (400, 403))
        self.login()

    def test_grade_write_requires_csrf_and_get_logout_cannot_change_state(self):
        self.login("teacher1")
        before = self.note()
        for csrf in (None, "invalid"):
            data = self.grade_data()
            if csrf is not None:
                data["csrf_token"] = csrf
            response = self.client.post("/grades", data=data, base_url="https://localhost")
            self.assertIn(response.status_code, (400, 403))
        self.assertEqual(self.note(), before)
        self.assertEqual(self.client.get("/logout", base_url="https://localhost").status_code, 405)
        self.assertEqual(self.client.get("/teacher", base_url="https://localhost").status_code, 200)
        self.assertEqual(self.post("/logout", form="/teacher").status_code, 302)
        self.assertIn(self.client.get("/teacher", base_url="https://localhost").status_code, (302, 401))

    def test_admin_post_routes_require_csrf(self):
        self.login("admin")
        for path, data in (("/admin/ping", {"host": "127.0.0.1"}),
                           ("/admin/users", {"action": "delete", "user_id": self.ids["unenrolled"]})):
            with self.subTest(path=path):
                response = self.client.post(path, data=data, base_url="https://localhost")
                self.assertIn(response.status_code, (400, 403))
        self.assertIsNotNone(self.query("SELECT id FROM users WHERE id=%s", (self.ids["unenrolled"],), one=True))


class EncryptedRouteTests(DatabaseFixture):
    def test_teacher_write_encrypts_and_authenticated_read_decrypts(self):
        self.login("teacher1")
        plaintext = self.prefix + "_updated_private_comment"
        for _ in range(2):
            previous = self.note()["comment"]
            response = self.post("/grades", self.grade_data(comment=plaintext), form="/teacher")
            self.assertEqual(response.status_code, 302)
            stored = self.note()["comment"]
            self.assertTrue(stored.startswith(PREFIX))
            self.assertNotIn(plaintext, stored)
            self.assertNotEqual(stored, previous)
            self.assertEqual(decrypt_comment(stored, self.notes[1], self.module.COMMENT_KEY), plaintext)
        response = self.api(self.notes[1], self.token())
        self.assertEqual(response.status_code, 200)
        self.assertIn(plaintext, response.get_data(as_text=True))

    def test_copied_ciphertext_never_returns_plaintext(self):
        ciphertext = self.note(1)["comment"]
        self.query("UPDATE notes SET comment=%s WHERE id=%s", (ciphertext, self.notes[2]))
        response = self.api(self.notes[2], self.token("student2"))
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(self.prefix + "_private1", response.get_data(as_text=True))
        self.assertNotIn(ciphertext, response.get_data(as_text=True))

    def test_stored_xss_escaped_on_student_and_teacher_pages(self):
        payload = '<script>alert("stored-xss")</script>'
        self.set_comment(1, payload)
        for role, path in (("student1", "/dashboard"), ("teacher1", "/teacher")):
            client = self.module.app.test_client()
            self.login(role, client=client)
            response = client.get(path, base_url="https://localhost")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(payload, response.get_data(as_text=True))
            self.assertIn("&lt;script&gt;", response.get_data(as_text=True))

    def test_real_export_zip_hmac_and_formula_neutralization(self):
        self.login("teacher1")
        for formula in ("=1+1", "+SUM(1,2)", "-1+2", "@SUM(1,2)", " \t=1+1", "\n=1+1"):
            with self.subTest(formula=formula):
                self.set_comment(1, formula)
                response = self.client.get(
                    f"/export.csv?class_id={self.classes[1]}&signed=1", base_url="https://localhost"
                )
                self.assertEqual(response.status_code, 200)
                with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
                    payload = archive.read("grades.csv")
                    signature = archive.read("grades.csv.hmac").decode("ascii").strip()
                self.assertTrue(verify_csv(payload, signature, self.module.CSV_HMAC_KEY))
                self.assertFalse(verify_csv(payload + b"changed", signature, self.module.CSV_HMAC_KEY))
                rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["comment"], "'" + formula)
                self.assertNotIn(self.names["student2"].encode(), payload)


class ValidationAndAdminTests(DatabaseFixture):
    def test_invalid_grades_and_oversized_comments_leave_storage_unchanged(self):
        self.login("teacher1")
        before = self.note()
        for grade in ("-0.1", "20.1", "NaN", "Infinity", "1.23", "not-a-number"):
            with self.subTest(grade=grade):
                response = self.post("/grades", self.grade_data(grade=grade), form="/teacher")
                self.assertIn(response.status_code, (400, 422))
                self.assertEqual(self.note(), before)
        response = self.post("/grades", self.grade_data(comment="x" * 4001), form="/teacher")
        self.assertIn(response.status_code, (400, 413, 422))
        self.assertEqual(self.note(), before)

    def test_new_grade_requires_enrolled_student_and_accepts_valid_insert(self):
        self.login("teacher1")
        for user in ("unenrolled", "teacher1"):
            response = self.post("/grades", self.grade_data(note_id="", student_id=str(self.ids[user])), form="/teacher")
            self.assertIn(response.status_code, (400, 403, 404, 422))
        self.query("INSERT INTO enrollments(student_id,class_id) VALUES(%s,%s)",
                   (self.ids["unenrolled"], self.classes[1]))
        response = self.post("/grades", self.grade_data(note_id="", student_id=str(self.ids["unenrolled"])), form="/teacher")
        self.assertEqual(response.status_code, 302)
        row = self.query("SELECT id,comment FROM notes WHERE student_id=%s AND class_id=%s",
                         (self.ids["unenrolled"], self.classes[1]), one=True)
        self.assertTrue(row["comment"].startswith(PREFIX))
        self.assertEqual(decrypt_comment(row["comment"], row["id"], self.module.COMMENT_KEY), "Updated fixture")

    def test_user_creation_validates_roles_names_passwords_and_hashes(self):
        self.login("admin")
        name = self.prefix + "_created"
        self.cleanup_usernames.append(name)
        base = {"action": "create", "username": name, "password": self.password, "role": "student"}
        for changed in ({"role": "superuser"}, {"username": "<script>bad</script>"}, {"password": "short"}):
            response = self.post("/admin/users", {**base, **changed}, form="/admin")
            self.assertIn(response.status_code, (400, 422))
        response = self.post("/admin/users", base, form="/admin")
        self.assertEqual(response.status_code, 302)
        user = self.query("SELECT password,role FROM users WHERE username=%s", (name,), one=True)
        self.assertEqual(user["role"], "student")
        self.assertTrue(verify_password(user["password"], self.password))
        self.assertNotEqual(user["password"], self.password)
        duplicate = self.post("/admin/users", base, form="/admin")
        self.assertIn(duplicate.status_code, (400, 409))

    def test_admin_deletion_invalidates_victims_session(self):
        victim = self.module.app.test_client()
        self.login("unenrolled", client=victim)
        self.login("admin")
        response = self.post("/admin/users", {
            "action": "delete", "user_id": str(self.ids["unenrolled"]),
        }, form="/admin")
        self.assertEqual(response.status_code, 302)
        response = victim.get("/dashboard", base_url="https://localhost")
        self.assertIn(response.status_code, (302, 401, 403))


class PingTests(DatabaseFixture):
    def test_shell_syntax_and_non_loopback_targets_never_spawn(self):
        self.login("admin")
        with patch.object(self.module.subprocess, "run") as run:
            for host in ("127.0.0.1; echo injected", "$(id)", "--help", "8.8.8.8", "192.168.1.1", "example.com"):
                with self.subTest(host=host):
                    response = self.post("/admin/ping", {"host": host}, form="/admin")
                    self.assertIn(response.status_code, (400, 403, 422))
            run.assert_not_called()

    def test_loopback_ping_uses_argument_vector_without_shell(self):
        self.login("admin")
        with patch.object(self.module.subprocess, "run", return_value=SimpleNamespace(
            stdout="fictional loopback success", stderr="", returncode=0,
        )) as run:
            response = self.post("/admin/ping", {"host": "127.0.0.1"}, form="/admin")
            self.assertIn(response.status_code, (200, 302))
            run.assert_called_once()
            args, kwargs = run.call_args
            self.assertIsInstance(args[0], (list, tuple))
            self.assertIn("127.0.0.1", args[0])
            self.assertFalse(kwargs.get("shell", False))
            self.assertGreater(kwargs.get("timeout", 0), 0)
            self.assertLessEqual(kwargs["timeout"], 10)
