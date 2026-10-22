1.Teacher browser -> Flask:

    POST /login (username, password)

2.Flask -> Teacher browser:

    302 redirect (Location: /)

    Data: session cookie

3.Teacher browser -> Flask:

    GET /teacher

4.Flask -> Teacher browser:

    200 HTML

    Data: classes, notes, students

5.Teacher browser -> Flask:

    GET /export.csv?class_id={id}

    Data: class_id

6.Flask -> Teacher browser:

    200 OK

    Data: CSV file containing class grades

7.Teacher browser -> Flask:

    POST /grades

    Data: note_id, student_id, class_id, grade, comment

    Purpose: Add / update a grade

8.Flask -> Teacher browser:

    302 redirect (Location: /teacher)

9.Flask -> PostgreSQL:

    SELECT queries

    Data: users, classes, notes

10.PostgreSQL -> Flask:

    Query results

    Data: user identity, classes, students, grades

11.Flask -> PostgreSQL:

    INSERT / UPDATE notes

    Data (add): student_id, class_id, grade, comment

    Data (update): note_id, grade, comment

12.PostgreSQL -> Flask:

    Write acknowledgement
