-- The application can append through this fixed function and read history,
-- but cannot alter or remove audit rows. Database administrators remain trusted.
CREATE SCHEMA notesapp_audit;
REVOKE ALL ON SCHEMA notesapp_audit FROM PUBLIC;

CREATE TABLE notesapp_audit.events (
    event_id BIGSERIAL PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    actor_id INTEGER,
    action TEXT NOT NULL CHECK (length(action) BETWEEN 1 AND 64),
    target JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(target) = 'object'),
    outcome TEXT NOT NULL CHECK (length(outcome) BETWEEN 1 AND 32),
    details JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(details) = 'object')
);

CREATE FUNCTION notesapp_audit.record_event(
    p_actor_id INTEGER, p_action TEXT, p_target JSONB,
    p_outcome TEXT, p_details JSONB
) RETURNS BIGINT
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, notesapp_audit, pg_temp
AS $$
DECLARE inserted_id BIGINT;
BEGIN
    INSERT INTO notesapp_audit.events(actor_id, action, target, outcome, details)
    VALUES (p_actor_id, p_action, p_target, p_outcome, p_details)
    RETURNING event_id INTO inserted_id;
    RETURN inserted_id;
END;
$$;

REVOKE ALL ON notesapp_audit.events FROM PUBLIC, notesapp_app;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA notesapp_audit FROM PUBLIC, notesapp_app;
REVOKE ALL ON FUNCTION notesapp_audit.record_event(INTEGER, TEXT, JSONB, TEXT, JSONB) FROM PUBLIC;
GRANT USAGE ON SCHEMA notesapp_audit TO notesapp_app;
GRANT SELECT ON notesapp_audit.events TO notesapp_app;
GRANT EXECUTE ON FUNCTION notesapp_audit.record_event(INTEGER, TEXT, JSONB, TEXT, JSONB) TO notesapp_app;
