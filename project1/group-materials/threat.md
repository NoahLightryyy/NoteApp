S = Spoofing, T = Tampering, R = Repudiation, I = Information disclosure, D = Denial of service, E = Elevation of privilege.

| ID | Flows / scope | Type | Issue |
|---|---|---|---|
| TH01 | 1-4 | S, T, E | The login query puts the username and password directly into SQL. Someone could change the query and get logged in as another user, possibly an admin. |
| TH02 | 4, 9, 13, 17, 21, 25, 29, 33, 37 | S, E | Flow 4 sets a session cookie signed with the key in the Compose file. Someone who knows the key could forge a Teacher or Admin session for later requests. |
| TH03 | 13-16 | S, I | The API accepts JWTs with `alg: none` and uses a hard-coded signing key. A forged Bearer token could pass authentication and read notes. Teacher/Admin pages use the Flask session. |
| TH04 | 13-16 | I | The notes API checks the note ID but not who owns it. A logged-in user could read another student's grade and comment. |
| TH05 | 17-20, 25-28 | I, E | A Teacher can see and export other teachers' classes. The queries don't restrict the results to their own classes. |
| TH06 | 21-24 | T, E | Updating a grade only checks the note ID. It doesn't check whether the class belongs to that teacher, so grades in another class could be changed. Creating a grade has the same missing class check. |
| TH07 | 11-12, 19-22 | T, I | Comments are displayed without HTML escaping. Someone who can write a comment could put a script there, which could run when a Student or Teacher opens the page. |
| TH08 | 7-8, 21-24, 33-40 | T, E | The forms have no CSRF tokens, and logout uses GET. SameSite is not explicitly set ([Flask defaults](https://github.com/pallets/flask/blob/3.0.3/src/flask/app.py)). An attack depends on the browser sending the session cookie; with an Admin victim, a forged ping request could trigger TH13. |
| TH09 | TB1; HTTP deployment | S, T, I | The Compose setup serves HTTP and the session cookie has no Secure flag. Someone intercepting traffic could steal passwords or cookies, reuse a session, or change requests and pages. |
| TH10 | PostgreSQL / backups | I | Passwords and comments are stored in clear text. Reading the database would expose them, and the image also contains a password backup. |
| TH11 | 1-4, 7-28, 33-40 | R | Logins are recorded, but logout and reads lack user-level audit records. Grade logs miss old/new values and affected rows; user changes and exports aren't logged. Ping records the host without the actor. |
| TH12 | 1-44 | D | There is no app rate limit or pagination. Repeated HTTP requests, large writes/exports and growing logs could exhaust resources. This still needs a load test. |
| TH13 | 37-40 | T, D, E | The Admin ping tool puts the host straight into a command with `shell=True`. Someone with an Admin session could run other commands to alter files or disrupt the service. |
| TH14 | 38; Docker setup | E | The container runs as root and has the Docker socket mounted. If someone gets code execution and can use that socket, the damage could extend to the Docker host. |
| TH15 | 21-22, 25-28 | T, I | CSV exports include raw comments. A crafted comment may run as a formula when a Teacher opens the CSV in a spreadsheet, altering results or exposing data depending on its settings. ([OWASP](https://community.owasp.org/attacks/CSV_Injection)) |
| TH16 | 21-24 | T | Grades have no business range check, and creating a note doesn't check that the user is a Student enrolled in that class. A Teacher could submit false grade records. Non-null user/class IDs must still exist. |
| TH17 | 4, 7-8, 12-16 | S, I | Issued JWTs have no expiry, and logout only clears the session cookie. Someone with a copied token could keep using the notes API as a Bearer client after the user logs out. |
