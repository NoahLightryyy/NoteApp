# Three minute presentation

Approximate duration: 3 minutes at 125–140 words per minute. Divide the sections among the speakers. The ratings below are assessment judgments under the network-accessible deployment assumption. This script is preparation material; it does not establish that the group presentation has taken place.

## Scope and architecture

Our project models the original course version of NotesApp, a grades application with student, teacher and administrator roles. Students should read their own grades, while teachers should manage their assigned classes. We traced browser requests into Flask, database queries into PostgreSQL, and the administrator ping function into a shell process.

Our diagrams also include the container’s access to host resources, the published database port and the interpretation of exported CSV files. These matter because threats do not stop at the browser-to-server boundary.

## Assessment method

We identified seventeen threats covering all six STRIDE categories. Each threat has a likelihood and impact score from one to five. We multiply them to prioritize risk. Our scenario assumes the unchanged application is reachable by untrusted network clients and its default source configuration is known. These scores are not measurements of attacks on our local machines.

## Highest priority risks

First, login SQL injection scores twenty-five. The application concatenates user input into SQL. An attacker may change the query logic and obtain another user’s identity. We propose parameterized queries, proper password verification and a restricted database account.

Second, the published session-signing secret also scores twenty-five. Someone who knows it may forge a privileged session. We propose a deployment-specific secret stored outside the repository, rotation of the exposed key, invalidation of old sessions, and server-side role checks.

Third, forged API tokens score twenty. The custom verifier accepts unsigned JWTs. We propose a maintained verification library, an explicit algorithm allowlist, protected keys and validation of token claims. We must also fix note ownership checks: a correctly authenticated student still must not read another student’s grade.

## Evidence and conclusion

Our evidence combines group-recorded page flows and code inspection. We distinguish these from untested outcomes, especially CSRF, spreadsheet formula execution and denial of service. An administrator compromise may chain into shell execution and Docker Engine access, so removing the shell interpretation and Docker socket is an additional containment priority.

The main lesson is that authentication, authorization and runtime isolation need separate controls. Our submission connects each threat to data flows, a justified score and a proposed mitigation. These are recommendations for that baseline; later labs implement selected fixes, not the entire remediation plan.
