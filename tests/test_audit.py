"""Persistent audit records, append-only privileges, and atomic protected writes."""
import json
from unittest.mock import patch

import psycopg2

from tests.test_security import DatabaseFixture


class PersistentAuditTests(DatabaseFixture):
    def events(self, role):
        return self.query(
            "SELECT actor_id,action,target,outcome,details FROM notesapp_audit.events "
            "WHERE actor_id=%s ORDER BY event_id", (self.ids[role],), many=True,
        )

    def failing_action(self, action):
        original = self.module.record_event

        def record(**kwargs):
            if kwargs["action"] == action:
                raise self.module.AuditFailure("isolated test: audit unavailable")
            return original(**kwargs)

        return patch.object(self.module, "record_event", side_effect=record)

    def test_sensitive_reads_and_grade_write_have_persistent_redacted_records(self):
        self.login("teacher1")
        self.assertEqual(self.client.get("/teacher", base_url="https://localhost").status_code, 200)
        self.assertEqual(self.api(self.notes[1], self.token("teacher1")).status_code, 200)
        comment = self.prefix + "_must_not_be_logged"
        response = self.post("/grades", self.grade_data(comment=comment), form="/teacher")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(f"/export.csv?class_id={self.classes[1]}",
                                         base_url="https://localhost").status_code, 200)
        events = self.events("teacher1")
        for action in ("teacher_read", "api_note_read", "grade_write", "csv_export"):
            matching = [event for event in events if event["action"] == action and event["outcome"] == "success"]
            self.assertTrue(matching, f"Missing persistent success audit for {action}")
        writes = [event for event in events if event["action"] == "grade_write"]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["target"]["note_id"], self.notes[1])
        self.assertEqual(str(writes[0]["details"]["grade_before"]), "12.3")
        self.assertEqual(str(writes[0]["details"]["grade_after"]), "14.5")
        self.assertTrue(writes[0]["details"]["comment_changed"])
        text = json.dumps(events, default=str)
        self.assertNotIn(comment, text)
        self.assertNotIn(self.password, text)
        self.assertNotIn(self.password_hash, text)
        self.assertNotIn(self.token("teacher1"), text)

        self.login("student1", client=self.module.app.test_client()).get("/dashboard", base_url="https://localhost")
        self.assertTrue(any(event["action"] == "dashboard_read" and event["outcome"] == "success"
                            for event in self.events("student1")))
        self.login("admin", client=self.module.app.test_client()).get("/admin", base_url="https://localhost")
        self.assertTrue(any(event["action"] == "admin_read" and event["outcome"] == "success"
                            for event in self.events("admin")))

    def test_application_database_role_cannot_modify_or_erase_audit_records(self):
        # Rollback even if a regression accidentally grants TRUNCATE. The stack
        # is disposable, but previous audit evidence must still be preserved.
        for statement in (
            "UPDATE notesapp_audit.events SET outcome=outcome WHERE false",
            "DELETE FROM notesapp_audit.events WHERE false",
            "TRUNCATE notesapp_audit.events",
        ):
            with self.subTest(statement=statement):
                conn = self.module.get_db()
                conn.autocommit = False
                try:
                    with conn.cursor() as cursor:
                        with self.assertRaises(psycopg2.errors.InsufficientPrivilege):
                            cursor.execute(statement)
                finally:
                    conn.rollback()
                    conn.close()

    def test_grade_change_rolls_back_when_its_audit_write_fails(self):
        self.login("teacher1")
        before = self.note()
        token = self.csrf(path="/teacher")
        with self.failing_action("grade_write") as audit:
            response = self.client.post("/grades", data={**self.grade_data(), "csrf_token": token},
                                        base_url="https://localhost")
        self.assertEqual(response.status_code, 503)
        self.assertTrue(any(call.kwargs.get("action") == "grade_write" for call in audit.call_args_list))
        self.assertEqual(self.note(), before, "Audit failure must roll back grade and encrypted comment")
        self.assertFalse(any(event["action"] == "grade_write" and event["outcome"] == "success"
                             for event in self.events("teacher1")))

    def test_user_creation_rolls_back_when_its_audit_write_fails(self):
        self.login("admin")
        name = self.prefix + "_audit_atomic"
        self.cleanup_usernames.append(name)
        token = self.csrf(path="/admin")
        with self.failing_action("user_create") as audit:
            response = self.client.post("/admin/users", data={
                "csrf_token": token, "action": "create", "username": name,
                "password": self.password, "role": "student",
            }, base_url="https://localhost")
        self.assertEqual(response.status_code, 503)
        self.assertTrue(any(call.kwargs.get("action") == "user_create" for call in audit.call_args_list))
        self.assertIsNone(self.query("SELECT id FROM users WHERE username=%s", (name,), one=True))
        self.assertFalse(any(event["action"] == "user_create" and event["outcome"] == "success"
                             for event in self.events("admin")))

    def test_logout_version_change_rolls_back_when_its_audit_write_fails(self):
        self.login()
        bearer = self.token()
        before = self.query("SELECT auth_version FROM users WHERE id=%s", (self.ids["student1"],), one=True)
        token = self.csrf(path="/dashboard")
        with self.failing_action("logout_all_sessions") as audit:
            response = self.client.post("/logout", data={"csrf_token": token}, base_url="https://localhost")
        self.assertEqual(response.status_code, 503)
        self.assertTrue(any(call.kwargs.get("action") == "logout_all_sessions" for call in audit.call_args_list))
        after = self.query("SELECT auth_version FROM users WHERE id=%s", (self.ids["student1"],), one=True)
        self.assertEqual(after, before)
        self.assertEqual(self.api(self.notes[1], bearer).status_code, 200)
        self.assertFalse(any(event["action"] == "logout_all_sessions" and event["outcome"] == "success"
                             for event in self.events("student1")))
