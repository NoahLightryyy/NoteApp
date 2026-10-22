# NotesApp canonical flow register

F01–F44 preserve the group’s global numbering. The separate teacher and administrator figures use local numbering; see the mapping below. Return arrows represent logical responses, not separate trust domains.

| Flow | Direction and data |
|---|---|
| F01 | Browser → Flask: `POST /login (username, password)` |
| F02 | Flask → PostgreSQL: `Query (username, password)` |
| F03 | PostgreSQL → Flask: `Query result (id, username, role; empty result or query error)` |
| F04 | Flask → Browser: `HTTP 302 (Location=/, signed session cookie containing identity and JWT); on failure: HTTP 200 HTML (login form, error)` |
| F05 | Browser → Flask: `GET /login (optional session cookie)` |
| F06 | Flask → Browser: `HTTP 200 HTML (login form)` |
| F07 | Browser → Flask: `GET /logout (session cookie)` |
| F08 | Flask → Browser: `HTTP 302 (Location=/login, session-clearing Set-Cookie)` |
| F09 | Student → Flask: `GET /dashboard (session cookie)` |
| F10 | Flask → PostgreSQL: `Query (session user_id)` |
| F11 | PostgreSQL → Flask: `Query result (id, grade, comment, class_name)` |
| F12 | Flask → Student: `HTTP 200 HTML (grades, comments, class names, JWT)` |
| F13 | Student → Flask: `GET /api/notes/<id> (note_id, Bearer JWT or session cookie)` |
| F14 | Flask → PostgreSQL: `Query (note_id)` |
| F15 | PostgreSQL → Flask: `Query result (id, student_id, class_id, grade, comment, student, class_name; or empty result)` |
| F16 | Flask → Student: `HTTP 200 JSON (id, student_id, class_id, grade, comment, student, class_name); HTTP 404 JSON (error) if absent` |
| F17 | Teacher → Flask: `GET /teacher (session cookie)` |
| F18 | Flask → PostgreSQL: `Query (courses, grades, students)` |
| F19 | PostgreSQL → Flask: `Query results (courses; grades with student/course details; student IDs and usernames)` |
| F20 | Flask → Teacher: `HTTP 200 HTML (courses, grades, students, grade form, export links)` |
| F21 | Teacher → Flask: `POST /grades (session cookie, note_id, student_id, class_id, grade, comment)` |
| F22 | Flask → PostgreSQL: `Query (update grade: note_id, grade, comment; create grade: student_id, class_id, grade, comment)` |
| F23 | PostgreSQL → Flask: `Command result (write completion status)` |
| F24 | Flask → Teacher: `HTTP 302 (Location=/teacher)` |
| F25 | Teacher → Flask: `GET /export.csv (session cookie, optional class_id)` |
| F26 | Flask → PostgreSQL: `Query (optional class_id)` |
| F27 | PostgreSQL → Flask: `Query result (student, class, grade, comment)` |
| F28 | Flask → Teacher: `HTTP 200 CSV (student, class, grade, comment; filename=grades.csv)` |
| F29 | Admin → Flask: `GET /admin (session cookie, optional ping_result)` |
| F30 | Flask → PostgreSQL: `Query (users, classes)` |
| F31 | PostgreSQL → Flask: `Query results (users: id, username, role, teacher_id; classes: id, name, teacher_id)` |
| F32 | Flask → Admin: `HTTP 200 HTML (users, classes, user forms, ping form, optional ping_result)` |
| F33 | Admin → Flask: `POST /admin/users (session cookie; create: action, username, password, role; delete: action, user_id)` |
| F34 | Flask → PostgreSQL: `Query (create user: username, password, role; delete user: user_id)` |
| F35 | PostgreSQL → Flask: `Command result (write completion status)` |
| F36 | Flask → Admin: `HTTP 302 (Location=/admin)` |
| F37 | Admin → Flask: `POST /admin/ping (session cookie, host)` |
| F38 | Flask → Shell/ping process: `Execute command string ("ping -c 1 " + host, shell=True)` |
| F39 | Shell/ping process → Flask: `Process result (ping output or error)` |
| F40 | Flask → Admin: `HTTP 200 HTML (ping_result)` |
| F41 | Browser → Flask: `GET /static/<path:filename> (filename, optional cache-validation headers; e.g. style.css)` |
| F42 | Flask → Static files: `Read/stat file (/app/static/<filename>)` |
| F43 | Static files → Flask: `File result (content, modification time, size)` |
| F44 | Flask → Browser: `HTTP 200 file (content, cache headers) or HTTP 304 (cache headers, no body)` |

## Additional infrastructure and utility flows

| Flow | Direction and data | Boundary |
|---|---|---|
| F45 | Monitoring client → Flask: GET /healthz | TB1 |
| F46 | Flask → PostgreSQL: connection attempt and credentials | TB2 |
| F47 | PostgreSQL → Flask: connection success or error | TB2 |
| F48 | Flask → monitoring client: 200 ok or 500 database error text | TB1 |
| F49 | Browser → Flask: GET / following a redirect | TB1 |
| F50 | Flask → browser: 302 to the role landing page or /login | TB1 |
| F51 | Flask → log file: selected login, grade-write and ping events | Internal file interface |
| F52 | Log filesystem → Flask: append success or error, silently ignored on OSError | Internal file interface |
| F53 | Web-container process → Docker Engine through mounted socket: potential control API requests | TB4; capability exposed by configuration, not normal app traffic |
| F54 | Docker Engine → web-container process: potential API response | TB4; conditional capability |
| F55 | Web-container process → host project bind mount /host: potential file read or write | TB4; capability, not a normal route |
| F56 | Host bind mount → web-container process: file content or write result | TB4; conditional capability |
| F57 | External database client → published port 5432: PostgreSQL protocol | TB5; reachability depends on host firewall/network |
| F58 | PostgreSQL → external database client: authentication/query response | TB5; conditional capability |
| F59 | Flask → container environment/configuration: load database and signing configuration at startup | Internal configuration interface |
| F60 | Container environment/configuration → Flask: configuration values | Internal configuration interface |
| F61 | Ping process → destination: ICMP echo request; when a hostname is supplied, resolver query precedes it | TB7 for nonlocal network traffic; conditional on route, name resolution and egress policy |
| F62 | Destination/resolver → ping process: ICMP echo reply, resolver answer or network error; a timeout can occur without a reply | TB7; local-only targets need not cross an external network boundary |

F13 without an accepted identity returns 401 before database access. A missing note returns 404.
For F09, F17, F21, F25, F29, F33 and F37, a failed session/role check redirects to /login.
Login follows F04 → F49 → F50 → the role page; role diagrams abbreviate this chain.
F37 also invokes the user/class read helpers for rendering the response; these reads are grouped with F30–F31.
F35 can be an error instead of success when a foreign-key constraint prevents deletion.
The GET /admin route reads classes, but the supplied template does not render every queried value.
Static files, logs, packaged configuration and the baked backup are container resources. They are not publicly downloadable merely because they exist.

## Diagram numbering cross reference

| Figure | Local IDs | Canonical IDs |
|---|---|---|
| Teacher | 1, 2 | F01, F04 |
| Teacher | 3, 4 | F17, F20 |
| Teacher | 5, 6 | F25, F28 |
| Teacher | 7, 8 | F21, F24 |
| Teacher | 9, 10 | Grouped reads F02–F03, F18–F19, F26–F27 |
| Teacher | 11, 12 | F22, F23 |
| Admin | 1, 2 | F01, F04 |
| Admin | 3, 4 | F29, F32 |
| Admin | 5, 6 and 7, 8 | Create/delete variants of F33, F36 |
| Admin | 9, 10 | F37, F40 |
| Admin | 11, 12 | F07, F08 |
| Admin | 13, 14 | Grouped reads F02–F03 and F30–F31, including ping page rendering |
| Admin | 15, 16 | F34, F35 |
| Admin | 17, 18 | F38, F39 |

The handwritten figure follows global IDs but is a rough sketch: its static-file arrows should terminate at container static files, not PostgreSQL. The corrected system diagram and this register govern the submission.

F61–F62 expand the network activity behind F38–F39. They are code-supported capabilities of the ping command, not a claim that an external probe was performed.
