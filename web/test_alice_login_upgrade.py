"""Supplemental isolated reenactment, not historical Alice migration evidence.

Temporarily represent Alice's original plaintext seed inside one uncommitted
transaction. Every change is rolled back, then a separate connection confirms
that Alice's original stored value remains intact. Passwords and hashes are
never printed.
"""
from contextlib import closing
from unittest.mock import patch

import app as module
from password_security import verify_password


def main():
    get_db = module.get_db
    conn = get_db()
    conn.autocommit = False
    original_password = None

    class BorrowedConnection:
        def cursor(self):
            return conn.cursor()

        def close(self):
            # The test owns the transaction and performs the final rollback.
            pass

    def stored_password():
        with conn.cursor() as cur:
            cur.execute("SELECT password FROM users WHERE username = %s", ("alice",))
            return cur.fetchone()["password"]

    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '5s'")
            cur.execute(
                "SELECT id, password FROM users WHERE username = %s FOR UPDATE",
                ("alice",),
            )
            alice = cur.fetchone()
            assert alice is not None, "The course Alice account must exist."
            original_password = alice["password"]
            cur.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                ("alicepw", alice["id"]),
            )

        with patch.object(module, "get_db", return_value=BorrowedConnection()), \
                patch.object(module, "log"):
            client = module.app.test_client()
            response = client.post(
                "/login", data={"username": "alice", "password": "wrong"}
            )
            assert response.status_code == 200
            assert b"Invalid credentials" in response.data
            assert stored_password() == "alicepw", "Wrong login modified storage."
            with client.session_transaction() as session:
                assert "user_id" not in session

            response = client.post(
                "/login", data={"username": "alice", "password": "alicepw"}
            )
            assert response.status_code == 302
            upgraded_password = stored_password()
            assert upgraded_password.startswith("$argon2id$")
            assert verify_password(upgraded_password, "alicepw")
            with client.session_transaction() as session:
                assert session["user_id"] == alice["id"]

            assert client.get("/logout").status_code == 302
            response = client.post(
                "/login", data={"username": "alice", "password": "alicepw"}
            )
            assert response.status_code == 302
            assert stored_password() == upgraded_password, "Second login changed the hash."
            with client.session_transaction() as session:
                assert session["user_id"] == alice["id"]
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()
        if original_password is not None:
            with closing(get_db()) as check_conn:
                with check_conn.cursor() as cur:
                    cur.execute(
                        "SELECT password FROM users WHERE username = %s", ("alice",)
                    )
                    current = cur.fetchone()
                    assert current is not None
                    assert current["password"] == original_password, \
                        "Alice's original stored value was not preserved."

    print(
        "PASS: supplemental isolated Alice reenactment (not historical migration evidence); "
        "wrong login leaves plaintext fixture unchanged; correct login upgrades to Argon2id; "
        "logout and second login succeed with the same hash; transaction rolled back; "
        "separate connection confirms Alice's original stored value is intact."
    )


if __name__ == "__main__":
    main()
