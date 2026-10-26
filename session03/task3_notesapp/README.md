# Unified coursework application

C3, C4, HTTPS and Argon2 now use the root [application and instructions](../../README.md).
This folder keeps setup/Compose compatibility entry points, not a second application.
The earlier implementation is retained in Git history at `b138325`.
Existing `notesapp-session03` containers, encryption keys and database volumes are not
merged or deleted by this change. Preserve them together if you need the old records.
