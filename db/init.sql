-- NotesApp schema + seed. Loaded automatically by postgres on first start
-- (docker-entrypoint-initdb.d). Runs only when the data volume is empty.

DROP TABLE IF EXISTS notes, enrollments, classes, users CASCADE;

CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,          -- Argon2id encoded hash (includes parameters and random salt)
    auth_version INTEGER NOT NULL DEFAULT 0 CHECK (auth_version >= 0),
    role       TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
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
    grade      NUMERIC(4,1) CHECK (grade BETWEEN 0 AND 20),
    comment    TEXT                    -- migrated to AES-GCM before the web server starts
);

-- admin (id 1)
INSERT INTO users (username,password,role,teacher_id) VALUES ('admin','$argon2id$v=19$m=65536,t=3,p=4$ws6z7ziEeBPCCKO14ompyA$6QW2HqKOAhDKMTvQn2ACO7wVhBGEuz7Y9K+YlQ2DfwU','admin',NULL);

-- teachers (ids 2..5)
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.turing','$argon2id$v=19$m=65536,t=3,p=4$acI96EzltYTAu5O+Zznh1Q$tBLpCHPXK9j8gnGoXuLYw/kQz/zmsT9SX8q2iSdgNAM','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.lovelace','$argon2id$v=19$m=65536,t=3,p=4$YrZooFxLOrikIvkGXmzuzA$04VOOLHHqw7oRSV5DHsuK4kGDUqfOBtw31nJ3aaSvXk','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.hopper','$argon2id$v=19$m=65536,t=3,p=4$RUxQ/IOUOHx5O1FATe0Jhw$O3eGLvZQzSC4IbFeT4RerPSvTMs2rcEmoheStEWrEuE','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.knuth','$argon2id$v=19$m=65536,t=3,p=4$ecbRrvhaPTocIl5p3SpQoA$tSmPuPtJOqObmTsvibN0B/Vf3tovyTipbQ9Zj9kzru4','teacher',NULL);

-- students (ids 6..35)
INSERT INTO users (username,password,role,teacher_id) VALUES ('alice','$argon2id$v=19$m=65536,t=3,p=4$4KexirsZIjYrQRNwvy9XVA$s+qo+Q5RVAIQZvas8Z1UZs3q4fZ5AjMUfuB2FE/8nrs','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('bob','$argon2id$v=19$m=65536,t=3,p=4$iyiU0fc6CW+w//X8gEWXdw$/SjgyusblQWkdUrSeO7pj0duIKcT3of2y3Ot896XlHo','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('carol','$argon2id$v=19$m=65536,t=3,p=4$dv+3A5xJcgohw7RM2bspiQ$9YYkgd8om66DrMUANqX1BxLMHuFbc9bnc+AvZwaQ0DA','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('dave','$argon2id$v=19$m=65536,t=3,p=4$YwBX8FKBpi0aK0zUoRngZA$4SPdjPKwK2MW/u2/4c9x1rRWScAaVXg0Wocz8852ijI','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('eve','$argon2id$v=19$m=65536,t=3,p=4$AyzGkI7QH4gDH1lnmuSdWQ$jdPl/MwyVt/6A74rl8Uc2krHfFtO/unckol9cPhqWYg','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('frank','$argon2id$v=19$m=65536,t=3,p=4$6OuJiLZMiX3bGsC6itLs/w$E+5fhE7cbylgcXMw4HuW6g2ysfVe5LvptZz0INcLGIM','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('grace','$argon2id$v=19$m=65536,t=3,p=4$sI9edWW0aaI9yfVrWtRh+w$NaDVu4yzqr6u0ykACOpSDxmCNMjZyQId55fizYxPMJ0','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('heidi','$argon2id$v=19$m=65536,t=3,p=4$LP+J5QanZ4NCGHo3FSj+dw$DJHI7HrLZT3HF8OuFn/S9bH/WfqDce4y6cxJ5AhpFKU','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('ivan','$argon2id$v=19$m=65536,t=3,p=4$WSUmOGCArAemEt4WSH3Xjw$o2aHMX5rOp8ghcGnJP9m3vOx3MgNaw73JhL3JDjlVyE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('judy','$argon2id$v=19$m=65536,t=3,p=4$waPvsFAd/9cOp2ElCadAJQ$rjsfiwGDLL/64JtdcKI1cOD91d94w/pcXY1FVaeLU7o','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('mallory','$argon2id$v=19$m=65536,t=3,p=4$Z7hNy+JdLi76MkmNKG4T8A$NYzqDVcaCBIDkvj1JruDrWGl/EklBHhABEBkXJKPK8U','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('niaj','$argon2id$v=19$m=65536,t=3,p=4$LUbkIU3JU5S0uTG/VYMu1A$ahRVu0GNH5HKJkapm9Mf9TL7x4MACM0AWUKc8AYxVJA','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('olivia','$argon2id$v=19$m=65536,t=3,p=4$IzQSqgl9JBmfgP5yAgI+2Q$sM2kNXfd7a7AykwSsRwNL2/jpf4OthjyLZfkh8ZG078','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('peggy','$argon2id$v=19$m=65536,t=3,p=4$GwjwU+iJ99B0uOeeE8Pn1A$MbSXFQVKyGWiuVAJJDJtrGmFCSF670qiUNecg0ua44M','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('quentin','$argon2id$v=19$m=65536,t=3,p=4$Q2FuY4pTkteiVWkGvTL2MQ$xO8yBRRF4Mbj0Jzv05JcfozqtAtXfIV4GWPKI87841Q','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('rupert','$argon2id$v=19$m=65536,t=3,p=4$hngBiBnNFWTpPS6PEMkfsw$UN+2LmWRCBrCWtALrczYn4NtP9FDprFSSvLc+J2BnsE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('sybil','$argon2id$v=19$m=65536,t=3,p=4$V7MHM41D7+r1jWJKA+d0Aw$c3th+IFW6hC/sXPp1vbRCpnwfccep629dWZBa6de4Z0','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('trent','$argon2id$v=19$m=65536,t=3,p=4$U+K9AYRDmtd2KynFMhE20g$5JQitgb+5oinIKzvCt0B7wIR55R97VCLiSo9Zumr7cI','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('ursula','$argon2id$v=19$m=65536,t=3,p=4$Ez0gmg/yRJuSUV+AfPuzPQ$7fDB15LgVEQs/EKBOH4n1Dnzbrl3VmJR+4I9LQu5+F8','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('victor','$argon2id$v=19$m=65536,t=3,p=4$PL2qGci4tx+UcqcvkrbF4w$3hpS9Fmxyo+jvAM18dYEbeS+pF1CrcNNxyzSCyMmxTs','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('wendy','$argon2id$v=19$m=65536,t=3,p=4$wmZ8YTtJD2IpS9O02BLPNg$S6UCMAPtwjpzufg2BGkFaNsS0jLzzM9VWxJlot+5Xnk','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('xavier','$argon2id$v=19$m=65536,t=3,p=4$0X2dkVfzf7aIq2i9+yPldQ$HARM2ep4V52uB3GM0VqA1L+XVIoFcnU9lGE/LwX5JJI','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('yvonne','$argon2id$v=19$m=65536,t=3,p=4$LQKf4HjQwKwTONmu6UyPQA$4ixMBNFA2tb7I0exFX8AbEx3CqZk+TQKal2+qO229GE','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('zack','$argon2id$v=19$m=65536,t=3,p=4$WM2rAXNbzNoNmZynpK5kDQ$0iCyGvZEupofMy9zEIR1KrqXJhuNOU8OmeMfizNw6wg','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('nora','$argon2id$v=19$m=65536,t=3,p=4$hO2Sz3q33zY+mRDX3IPFHQ$1A3UZYhS3Lr8fvV2d67tVOGmr7mEM+gRYU+PEcPXaBo','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('liam','$argon2id$v=19$m=65536,t=3,p=4$34Tl43BGMcIdirO8dsjq5g$mkDMNYJeoUl5wu8xxSp0HMB13aJweVZqBBugYjmxkUw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('mia','$argon2id$v=19$m=65536,t=3,p=4$QbQjFJtk9ruv/OX2zx5Ajg$0UFpysWWI2VLnZazAdp9YKHSdpJ5tc7EDprJnkcTXxQ','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('noah','$argon2id$v=19$m=65536,t=3,p=4$Z2rQKPIDbURARUz8KCoNHQ$j+j2Yy/Yfsra//uVqkugczbpQrrbs+OKbzIXgGkgt5c','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('emma','$argon2id$v=19$m=65536,t=3,p=4$xQPlOyxvPwAhMya/xnRaWg$l2DerdJSzbdMmS9kqdAVTzaFBDHbJS1Kln4RIVwTYRI','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('lucas','$argon2id$v=19$m=65536,t=3,p=4$d45DUFn0yKENg/UQkJtJtw$IOaFsc5Yl1+JsYmyiqahjiMGOWNdYyv1bDDn94o6xAQ','student',NULL);

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
