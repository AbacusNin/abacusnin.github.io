"""Small invented log cases for the offline candidate generator."""

import unittest
from datetime import datetime, timedelta

from booking_hunt import analyze, parse_line, sessions


def event(ip, second, method, path):
    return {"ip": ip, "time": datetime(2026, 4, 1) + timedelta(seconds=second),
            "method": method, "path": path, "status": "200"}


class BookingHuntTests(unittest.TestCase):
    def test_rotation_and_overnight_gap(self):
        items = []
        for base, ip in [(0, "actor-a"), (86400, "actor-a"), (172800, "actor-b")]:
            items.extend(event(ip, base + n * 60, "GET", "/availability") for n in range(5))
            items.extend(event(ip, base + 240, "POST", "/reserve") for _ in range(2))
        found = analyze(items, "/availability", "/reserve")
        self.assertEqual([x["source"] for x in found], ["actor-a", "actor-b"])
        self.assertEqual(len(sessions([x["time"] for x in items if x["ip"] == "actor-a"])), 2)

    def test_benign_auto_refresh_without_booking(self):
        items = [event("monitor", n * 60, "GET", "/availability") for n in range(5)]
        self.assertEqual(analyze(items, "/availability", "/reserve"), [])

    def test_near_miss_irregular_and_double_click(self):
        items = [event("user", n, "GET", "/availability") for n in (0, 57, 124, 215, 301)]
        items += [event("user", 302, "POST", "/reserve"), event("user", 305, "POST", "/reserve")]
        self.assertEqual(analyze(items, "/availability", "/reserve"), [])

    def test_burst_in_later_session_does_not_join(self):
        items = [event("shared-ip", n * 60, "GET", "/availability") for n in range(5)]
        items += [event("shared-ip", 86400, "POST", "/reserve"), event("shared-ip", 86400, "POST", "/reserve")]
        self.assertEqual(analyze(items, "/availability", "/reserve"), [])

    def test_parser_accepts_exercise_shape_and_rejects_bad_line(self):
        row = '192.0.2.4 - - [01/Apr/2026:00:33:45 ] "GET /availability HTTP/1.1" 200 42 "-" "Example"'
        self.assertEqual(parse_line(row)["path"], "/availability")
        with self.assertRaises(ValueError):
            parse_line('192.0.2.4 - - [bad] "GET /availability HTTP/1.1" 200 42 "-" "Example"')


if __name__ == "__main__":
    unittest.main()
