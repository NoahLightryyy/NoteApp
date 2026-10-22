-- NotesApp schema + seed. Loaded automatically by postgres on first start
-- (docker-entrypoint-initdb.d). Runs only when the data volume is empty.

DROP TABLE IF EXISTS notes, enrollments, classes, users CASCADE;

CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,          -- Argon2id encoded hash (includes parameters and random salt)
    role       TEXT NOT NULL,          -- 'student' | 'teacher' | 'admin'
    teacher_id INTEGER REFERENCES users(id)
);

CREATE TABLE classes (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    teacher_id INTEGER REFERENCES users(id)
);

CREATE TABLE enrollments (
    id         SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id),
    class_id   INTEGER REFERENCES classes(id)
);

CREATE TABLE notes (
    id         SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id),
    class_id   INTEGER REFERENCES classes(id),
    grade      NUMERIC(4,1),
    comment    TEXT                    -- rendered as rich text / unescaped (planted flaw #10)
);

-- admin (id 1)
INSERT INTO users (username,password,role,teacher_id) VALUES ('admin','$argon2id$v=19$m=65536,t=3,p=4$mESkTs5hkn3L4JOyFrnxqA$h7IRENCVvmBnPE8wYZKlDavnqDU05hP0mCoM2WKEJmw','admin',NULL);

-- teachers (ids 2..5)
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.turing','$argon2id$v=19$m=65536,t=3,p=4$hTA72fDeGbtN5xugyGV2KA$9XMlBh0mRzmD4w/axg1W1PTEphvsWB91XhjSeP83u7Q','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.lovelace','$argon2id$v=19$m=65536,t=3,p=4$yu8rqB1yhLAyHRUkj7TKcQ$/ELl6uf9J+Yv5RqCiHYWohqRm+8/6+v2iLm6nCBWJlk','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.hopper','$argon2id$v=19$m=65536,t=3,p=4$xRtnVAY3lTL59ITdFZxcyg$XnGunmwibWVmOFj8VN3X8WHxItM07ZGegHvuc28UNak','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.knuth','$argon2id$v=19$m=65536,t=3,p=4$UM7IpU2LaS6X0PLf1pLBKQ$nNwpoS1cU9OvA4VjO9mN6OKO/NqHazNGzErZRxelzJI','teacher',NULL);

-- students (ids 6..35)
INSERT INTO users (username,password,role,teacher_id) VALUES ('alice','$argon2id$v=19$m=65536,t=3,p=4$Xn/7FjvRF25Z4I3kGMY2kg$JTK89QxYhmiljJ7oRo4YC/ZzArDswBXX70pb0yJxvsI','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('bob','$argon2id$v=19$m=65536,t=3,p=4$5xEbUFbkQQa+QL5EbrbF0g$YRu5EhtnVEuXL/WH4efUQywIdB+JmDJ3UyD07LEcl9c','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('carol','$argon2id$v=19$m=65536,t=3,p=4$SmRPxs46BixdVYtu3/9CrA$0EE+yY/+yYcHW9BFWkIbEjf9/brvaNAqZPbtwaI0tOI','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('dave','$argon2id$v=19$m=65536,t=3,p=4$onAl6BcFkMQcIvf0wFwFTw$5BFaTzpMuLiRN2GIW+lMI4ICa6nGI94bFbhQnAfdQys','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('eve','$argon2id$v=19$m=65536,t=3,p=4$Nd90ahOL1ESPJZxP17lr6A$Aec97i+OlQzaIOkw4A4VO5Nn3eL5hlmSr/drHesnxzE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('frank','$argon2id$v=19$m=65536,t=3,p=4$1+iCd+3FJXv3MG2fY6+DAA$KZYf4ll/kuanIyz5CJ087RQFWbEe9g+8lghJTj8nzw4','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('grace','$argon2id$v=19$m=65536,t=3,p=4$+xPjDCn4Vqt45br07F5HXg$yAePSB8oIaHclB8QDFS9sn1ys85Zb+3WJOCQI2uHrg0','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('heidi','$argon2id$v=19$m=65536,t=3,p=4$RaFaoSU7o2Jo1ARJGymJLg$mTOGOfGEyNJU0sow4SJG37uhslIiTXAj+j7UbLB96zE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('ivan','$argon2id$v=19$m=65536,t=3,p=4$vxc67UYDiFQ1q2bI9wXc6A$eYYP6OXxsbxOtXCUp0FPsTxcQV4Q/E6PQVbBGZnhWCY','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('judy','$argon2id$v=19$m=65536,t=3,p=4$LDvXZwekBni6LIhItO3mbQ$DulW0c5Z5bCPf9OViiaH7SSvvE9nvphjfdLDLKPQZr0','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('mallory','$argon2id$v=19$m=65536,t=3,p=4$g0UdoxVwy4lL3YCH/wlwgg$DYCLS4nyHdJm+kJfmAg5od9miqN6cKqYHRiOcbi60pM','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('niaj','$argon2id$v=19$m=65536,t=3,p=4$J4vNbyh+Qadt9+HhERX0cg$TQs7v8Ekl3pb8VmrQiqh73GE4bdrwCYA+Q9r7gg8T/k','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('olivia','$argon2id$v=19$m=65536,t=3,p=4$Y4k/VvdQue6mGLqhV0+xSA$P81CDvo7zfbnfdu4bR54ggw6syaM229aamT0StE3yME','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('peggy','$argon2id$v=19$m=65536,t=3,p=4$631JNPyLG63Ry1qCOcbykw$HuwiZcL80vxkOox+u1txv43QxX625awlrHd61Gn8jQE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('quentin','$argon2id$v=19$m=65536,t=3,p=4$AoEBcqeSDm8KWoM7GtwmkQ$lYEzuPtyPp8kirn1CXxqEw8QyHn+emZAXJ6eENXszzk','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('rupert','$argon2id$v=19$m=65536,t=3,p=4$yFCy6KmdT+2gisphpU/Vtg$0uao8gRW06x1uxtP8j9elIW1HJiu3Nxgg2EMPlGopss','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('sybil','$argon2id$v=19$m=65536,t=3,p=4$Xc/4TeT6u9Zc6MICEulNJw$xwedfr/7z8SZazhM1hzFlGAt0OSnwdCmP9+sdhQ1e4I','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('trent','$argon2id$v=19$m=65536,t=3,p=4$Lt0TvghK3G/P5SqmRaI47Q$EcD80zukOR+0/tE0wd3dH2TSI8VoW8RF1NikHwSu3AE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('ursula','$argon2id$v=19$m=65536,t=3,p=4$E6aJHIRKwK8rHPTdM5OUaA$oc3NR4itxR2Hx0dzb6Fm87xQhVChxHV4+zLdvd/lrks','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('victor','$argon2id$v=19$m=65536,t=3,p=4$n5iNo9rV/0gDYM2naqk/FQ$4NIpkJMFkSBCBSpfMgBCMqB67kCcmFCVXtn7ABeOmHY','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('wendy','$argon2id$v=19$m=65536,t=3,p=4$+SR2BGRUbeI/S42711MyYg$fkb1V/bbXEtIujNmg0wVi9bO3pSZjHQr2rpJkg/neT4','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('xavier','$argon2id$v=19$m=65536,t=3,p=4$U5phbiHc5aWncvIWXUP+PQ$TTePfrh421gQM6xn2w+TJSfgwFPO3ZHhC5nxFuYedNQ','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('yvonne','$argon2id$v=19$m=65536,t=3,p=4$UJI8fGMoxS3dPD0vexF3yg$YiD27tQJ2LwrDe+z1M2Uxqo/HhKdtV9fs8nbymupt0w','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('zack','$argon2id$v=19$m=65536,t=3,p=4$tvPrJSM/glE5AlNpkjO3cw$Yfy93QFxo//ZO5qQ1panKmk4+7uop7m6r6HOUZhAqEk','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('nora','$argon2id$v=19$m=65536,t=3,p=4$Pi+ZqPoONZ+0BgTsvpdGOw$iMSLbk4ME73fHC8EwrDEoCjrIYVRuR9nVFymOS2tn38','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('liam','$argon2id$v=19$m=65536,t=3,p=4$1fbXaLKFBn1vxj7qnuIiVw$OG3y2FkFt56hrykt9juSbnNVKmLvma//q9j54KMCO8I','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('mia','$argon2id$v=19$m=65536,t=3,p=4$jbT4qzFfzGm8c+/UOP6cDg$PEgp39QAgkSvaF3QD6eo1q5PTPlFetSxGXPXH0wQCmE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('noah','$argon2id$v=19$m=65536,t=3,p=4$Jo/awHrssd5s012Svl9sPQ$xmeJponBpkikKmbSMek/rUB13/lXZSdIxAy2BuLF+O0','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('emma','$argon2id$v=19$m=65536,t=3,p=4$G9GExItuVys1LpVYC0b1Tw$qhZB7GP69wUaOllZKvK9vhzdKOmd/SreBVCpDrktIEo','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('lucas','$argon2id$v=19$m=65536,t=3,p=4$lS/JJTJes/YvsJ6yfC1GRQ$BuDtoxJh+DXKZRkUaePFUKLW3DUeOafXdb/ayYi2Dj8','student',NULL);

-- classes (ids 1..4), teacher_id references users ids 2..5
INSERT INTO classes (name,teacher_id) VALUES ('Mathematics',2);
INSERT INTO classes (name,teacher_id) VALUES ('History',3);
INSERT INTO classes (name,teacher_id) VALUES ('Physics',4);
INSERT INTO classes (name,teacher_id) VALUES ('Computer Science',5);

-- enrollments + notes
INSERT INTO enrollments (student_id,class_id) VALUES (6,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (6,1,16.2,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (6,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (6,4,10.5,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (7,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (7,1,12.6,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (7,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (7,3,9.0,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (8,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (8,1,10.2,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (8,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (8,3,12.6,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (9,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (9,3,16.3,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (9,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (9,1,15.7,'Should ask more questions.');
INSERT INTO enrollments (student_id,class_id) VALUES (10,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (10,3,10.4,'Should ask more questions.');
INSERT INTO enrollments (student_id,class_id) VALUES (10,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (10,1,9.1,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (11,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (11,1,17.3,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (11,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (11,2,10.9,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (12,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (12,4,9.4,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (12,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (12,3,8.9,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (13,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (13,3,10.1,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (13,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (13,4,8.5,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (14,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (14,3,17.4,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (14,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (14,1,12.2,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (15,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (15,3,12.1,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (15,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (15,1,15.4,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (16,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (16,2,16.0,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (16,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (16,3,13.1,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (17,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (17,2,11.6,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (17,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (17,3,10.5,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (18,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (18,3,10.9,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (18,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (18,2,18.0,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (19,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (19,3,15.2,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (19,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (19,1,17.7,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (20,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (20,2,9.5,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (20,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (20,4,13.9,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (21,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (21,4,12.4,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (21,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (21,3,19.0,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (22,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (22,4,16.3,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (22,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (22,1,9.7,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (23,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (23,4,8.7,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (23,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (23,3,14.6,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (24,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (24,3,17.5,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (24,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (24,4,15.5,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (25,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (25,3,11.7,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (25,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (25,4,12.8,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (26,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (26,1,17.6,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (26,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (26,3,18.7,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (27,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (27,1,11.3,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (27,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (27,3,14.7,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (28,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (28,3,13.9,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (28,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (28,1,18.1,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (29,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (29,3,8.2,'Should ask more questions.');
INSERT INTO enrollments (student_id,class_id) VALUES (29,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (29,2,17.7,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (30,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (30,2,10.6,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (30,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (30,1,18.4,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (31,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (31,4,18.8,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (31,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (31,1,16.4,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (32,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (32,4,9.8,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (32,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (32,3,17.6,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (33,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (33,2,16.3,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (33,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (33,3,15.8,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (34,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (34,3,17.9,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (34,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (34,2,9.3,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (35,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (35,1,8.2,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (35,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (35,2,10.5,'Late submission, but good quality.');
