# Admin Flow

1. Admin browser → Flask:

   POST /login

   Data:

   - username
   - password

2. Flask → Admin browser:

   302 FOUND

   Data:

   - Location: / (redirect to the home route)
   - Set-Cookie: session (login session cookie; HttpOnly; Path=/)

3. Admin browser → Flask:

   GET /admin

   Data:

   - Session cookie

4. Flask → Admin browser:

   200 OK

   Data:

   - HTML administration page (Content-Type: text/html; charset=utf-8)
   - Current username and admin role badge
   - User table containing user IDs, usernames and roles
   - User deletion form targeting POST /admin/users, with hidden action and user_id fields
   - Logout link

5. Admin browser → Flask:

   POST /admin/users

   Data:

   - action: create
   - username: test_admin_flow
   - password (new user's password)
   - role: student
   - Session cookie

6. Flask → Admin browser:

   302 FOUND

   Data:

   - Location: /admin (redirect to the administration page)

7. Admin browser → Flask:

   POST /admin/users

   Data:

   - action: delete
   - user_id: 36
   - Session cookie

8. Flask → Admin browser:

   302 FOUND

   Data:

   - Location: /admin (redirect to the administration page)

9. Admin browser → Flask:

   POST /admin/ping

   Data:

   - host: 127.0.0.1
   - Session cookie

10. Flask → Admin browser:

    200 OK

    Data:

    - HTML administration page (Content-Type: text/html; charset=utf-8)
    - Ping output for 127.0.0.1
    - 1 packet transmitted, 1 received, 0% packet loss
    - Round-trip time: 0.179 ms

11. Admin browser → Flask:

    GET /logout

    Data:

    - Session cookie

12. Flask → Admin browser:

    302 FOUND

    Data:

    - Location: /login (redirect to the login page)
    - Set-Cookie: session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; HttpOnly; Path=/
    - The response instructs the browser to delete the session cookie.

All twelve flows cross TB1, the trust boundary between the browser and Flask.

These entries describe the login, administration-page, user-creation, user-deletion, server-connectivity-test and logout exchanges shown in the supplied screenshots. Intermediate login redirects and repeated page loads after redirects are not detailed here. Creation and deletion responses redirect to /admin; changes to the user list should be checked to confirm the results. Flask–PostgreSQL flows across TB2 and the server-side execution of ping are not visible in the browser Network screenshots.
