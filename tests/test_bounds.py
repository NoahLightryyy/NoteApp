"""Exercise pagination and export limits on small, isolated boundary fixtures."""
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch
import csv
import io

from tests.test_security import DatabaseFixture
from comment_crypto import encrypt_comment
from csv_hmac import verify_csv


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.tables = []
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and "href" in values:
            self.links.append(values["href"])
        elif tag == "table":
            self.tables.append([])
        elif tag == "tr":
            self.row = []
        elif tag == "td":
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row and self.tables:
                self.tables[-1].append(self.row)
            self.row = None


class BoundedQueryTests(DatabaseFixture):
    def add_note(self, *, class_number=1, student="student1", comment):
        row = self.query(
            "INSERT INTO notes(student_id,class_id,grade,comment) VALUES(%s,%s,10,NULL) RETURNING id",
            (self.ids[student], self.classes[class_number]), one=True,
        )
        self.query("UPDATE notes SET comment=%s WHERE id=%s", (
            encrypt_comment(comment, row["id"], self.module.COMMENT_KEY), row["id"],
        ))
        return row["id"]

    def add_class(self, number):
        self.classes[number] = self.query(
            "INSERT INTO classes(name,teacher_id) VALUES(%s,%s) RETURNING id",
            (self.prefix + "_class" + str(number), self.ids["teacher1"]), one=True,
        )["id"]
        return self.classes[number]

    def page(self, client, path):
        response = client.get(path, base_url="https://localhost")
        self.assertEqual(response.status_code, 200)
        parser = PageParser()
        body = response.get_data(as_text=True)
        parser.feed(body)
        return parser, body

    def next_link(self, parser, current, field):
        before = parse_qs(urlsplit(current).query).get(field, ["0"])[0]
        matches = []
        for link in parser.links:
            parsed = urlsplit(link)
            values = parse_qs(parsed.query)
            after = values.get(field, [before])[0]
            if parsed.path == urlsplit(current).path and after != before:
                self.assertGreater(int(after), int(before), "Keyset cursors must advance")
                matches.append(link)
        self.assertLessEqual(len(matches), 1, "Each list must expose at most one next-page link")
        return matches[0] if matches else None

    def test_student_and_teacher_note_pages_are_complete_bounded_and_scoped(self):
        expected = [self.notes[1]]
        for number in range(4):
            expected.append(self.add_note(comment=self.prefix + "_page_note_" + str(number)))
        with patch.object(self.module, "PAGE_SIZE", 2):
            for role, first in (("student1", "/dashboard"), ("teacher1", "/teacher")):
                with self.subTest(role=role):
                    client = self.module.app.test_client()
                    self.login(role, client=client)
                    path, seen, pages = first, [], 0
                    while path:
                        pages += 1
                        self.assertLessEqual(pages, 3, "Pagination must terminate without repeating a cursor")
                        parser, body = self.page(client, path)
                        rows = parser.tables[0]
                        self.assertLessEqual(len(rows), 2)
                        seen.extend(int(row[0]) for row in rows)
                        self.assertNotIn(self.prefix + "_private2", body)
                        self.assertNotIn(self.prefix + "_class2", body)
                        path = self.next_link(parser, path, "after")
                    self.assertEqual(seen, expected, "Every authorized note must appear exactly once")
                    self.assertEqual(pages, 3)

    def test_admin_users_and_classes_have_independent_complete_pages(self):
        for number in (3, 4, 5):
            self.add_class(number)
        self.login("admin")
        users_start = min(self.ids.values()) - 1
        classes_start = min(self.classes.values()) - 1
        first = f"/admin?users_after={users_start}&classes_after={classes_start}"
        with patch.object(self.module, "PAGE_SIZE", 2):
            path, user_ids, pages = first, [], 0
            while path:
                pages += 1
                self.assertLessEqual(pages, 3)
                parser, _ = self.page(self.client, path)
                self.assertLessEqual(len(parser.tables[0]), 2)
                user_ids.extend(int(row[0]) for row in parser.tables[0])
                following = self.next_link(parser, path, "users_after")
                if following:
                    self.assertEqual(parse_qs(urlsplit(following).query)["classes_after"], [str(classes_start)])
                path = following
            self.assertEqual(user_ids, sorted(self.ids.values()))

            path, class_numbers, pages = first, [], 0
            while path:
                pages += 1
                self.assertLessEqual(pages, 3)
                parser, body = self.page(self.client, path)
                displayed = [n for n in self.classes if self.prefix + "_class" + str(n) in body]
                self.assertLessEqual(len(displayed), 2)
                class_numbers.extend(displayed)
                following = self.next_link(parser, path, "classes_after")
                if following:
                    self.assertEqual(parse_qs(urlsplit(following).query)["users_after"], [str(users_start)])
                path = following
            self.assertEqual(class_numbers, list(self.classes))

    def test_invalid_cursors_are_rejected_instead_of_ignoring_the_filter(self):
        for role, path, fields in (("student1", "/dashboard", ("after",)),
                                   ("teacher1", "/teacher", ("after",)),
                                   ("admin", "/admin", ("users_after", "classes_after"))):
            client = self.module.app.test_client()
            self.login(role, client=client)
            for field in fields:
                self.assertEqual(client.get(path + "?" + field + "=0", base_url="https://localhost").status_code, 200)
                for invalid in ("-1", "abc", "2147483648", "1.5", "1%20OR%201=1"):
                    with self.subTest(path=path, field=field, invalid=invalid):
                        response = client.get(path + "?" + field + "=" + invalid, base_url="https://localhost")
                        self.assertEqual(response.status_code, 400)

    def test_export_over_limit_is_rejected_whole_and_class_filter_remains_usable(self):
        self.login("teacher1")
        with patch.object(self.module, "MAX_EXPORT_ROWS", 2):
            self.add_note(comment=self.prefix + "_export_at_limit")
            exact = self.client.get("/export.csv", base_url="https://localhost")
            self.assertEqual(exact.status_code, 200)
            self.assertEqual(len(list(csv.DictReader(io.StringIO(exact.get_data(as_text=True))))), 2)
            self.add_note(comment=self.prefix + "_export_over_limit")
            for query in ("", "?signed=1", f"?class_id={self.classes[1]}"):
                response = self.client.get("/export.csv" + query, base_url="https://localhost")
                self.assertEqual(response.status_code, 413)
                self.assertNotIn("Content-Disposition", response.headers)
                self.assertNotIn("X-CSV-HMAC-SHA256", response.headers)
                self.assertNotIn(self.prefix, response.get_data(as_text=True))
                self.assertFalse(response.data.startswith(b"PK"), "Do not return a partial signed ZIP")
            self.add_class(3)
            self.query("INSERT INTO enrollments(student_id,class_id) VALUES(%s,%s)",
                       (self.ids["student1"], self.classes[3]))
            self.add_note(class_number=3, comment=self.prefix + "_filtered_export")
            filtered = self.client.get(f"/export.csv?class_id={self.classes[3]}", base_url="https://localhost")
            self.assertEqual(filtered.status_code, 200)
            self.assertTrue(verify_csv(filtered.data, filtered.headers["X-CSV-HMAC-SHA256"], self.module.CSV_HMAC_KEY))
            rows = list(csv.DictReader(io.StringIO(filtered.get_data(as_text=True))))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["comment"], self.prefix + "_filtered_export")

    def test_teacher_class_selector_rejects_overflow_without_silent_truncation(self):
        self.login("teacher1")
        with patch.object(self.module, "MAX_SELECTOR_ROWS", 2):
            self.add_class(3)
            self.assertEqual(self.client.get("/teacher", base_url="https://localhost").status_code, 200)
            self.add_class(4)
            response = self.client.get("/teacher", base_url="https://localhost")
            self.assertEqual(response.status_code, 413)
            self.assertNotIn("<select", response.get_data(as_text=True))

    def test_teacher_student_selector_rejects_overflow_without_silent_truncation(self):
        self.login("teacher1")
        with patch.object(self.module, "MAX_SELECTOR_ROWS", 2):
            self.query("INSERT INTO enrollments(student_id,class_id) VALUES(%s,%s)",
                       (self.ids["student2"], self.classes[1]))
            self.assertEqual(self.client.get("/teacher", base_url="https://localhost").status_code, 200)
            self.query("INSERT INTO enrollments(student_id,class_id) VALUES(%s,%s)",
                       (self.ids["unenrolled"], self.classes[1]))
            response = self.client.get("/teacher", base_url="https://localhost")
            self.assertEqual(response.status_code, 413)
            self.assertNotIn("<select", response.get_data(as_text=True))
