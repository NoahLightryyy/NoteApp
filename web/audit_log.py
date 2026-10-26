"""Protected database audit events; never include credentials or comment text."""
import sys

from psycopg2.extras import Json

from database import get_db


class AuditFailure(RuntimeError):
    """An operation must not claim success without its audit record."""


def record_event(*, actor, action, target=None, outcome="success", details=None, connection=None):
    """Append using the caller's transaction, or an independent autocommit connection."""
    owned = connection is None
    conn = connection
    try:
        if owned:
            conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT notesapp_audit.record_event(%s, %s, %s, %s, %s)",
                        (actor, action, Json(target or {}), outcome, Json(details or {})))
            return cur.fetchone()["record_event"]
    except Exception as error:
        # No exception text: a driver message could contain submitted values.
        print("AUDIT_WRITE_FAILED: protected audit storage is unavailable.", file=sys.stderr, flush=True)
        raise AuditFailure("Protected audit storage is unavailable") from error
    finally:
        if owned and conn is not None:
            conn.close()
