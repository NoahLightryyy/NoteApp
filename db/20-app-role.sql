-- Initialization runs as the database owner, never as the application role.
-- Read the dedicated app secret without putting it in command arguments or logs.
DO $$
BEGIN
    EXECUTE format('CREATE ROLE notesapp_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD %L',
                   btrim(pg_read_file('/run/secrets/db_password')));
END
$$;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO notesapp_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO notesapp_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO notesapp_app;
