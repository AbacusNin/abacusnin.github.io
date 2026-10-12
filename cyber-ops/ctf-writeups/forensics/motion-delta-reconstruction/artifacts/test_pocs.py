import unittest
from pathlib import Path

from motion_delta_review import review, svg
from telemetry_sequence_hunt import hunt, load_events


HERE = Path(__file__).parent


class MotionReviewTests(unittest.TestCase):
    def test_synthetic_strokes_and_axis_choice(self):
        summary, segments = review(HERE / "fixture_motion.csv")
        self.assertEqual((summary["rows"], summary["pen_down_rows"], summary["stroke_segments"]), (6, 4, 2))
        self.assertEqual((summary["x_range"], summary["y_range"]), ([0.0, 4.0], [0.0, 4.0]))
        self.assertEqual(segments[0], [(0.0, 0.0), (0.0, 2.0), (0.0, 4.0)])
        self.assertNotEqual(svg(segments, "math"), svg(segments, "screen"))

    def test_invalid_state_and_time_rejected(self):
        class MemorySource:
            def __init__(self, data):
                self.data = data

            def open(self, mode):
                from io import BytesIO
                return BytesIO(self.data)

        for line in ("16,1,1,2", "0,1,1,1", "16,nan,1,1"):
            with self.subTest(line=line):
                path = MemorySource(("time_ms,dx,dy,pen_down\n0,0,0,0\n" + line + "\n").encode())
                with self.assertRaises(ValueError):
                    review(path)


class EventHuntTests(unittest.TestCase):
    def test_positive_benign_and_process_mismatch(self):
        leads = hunt(load_events(HERE / "fixture_events.jsonl"))
        self.assertEqual([lead["process_guid"] for lead in leads], ["case-positive"])
        self.assertIn("unproven", leads[0]["classification"])

    def test_legitimate_full_sequence_is_a_false_positive(self):
        events = [
            {"time_ms": 1, "host": "lab", "process_guid": "vendor", "kind": "input_open"},
            {"time_ms": 2, "host": "lab", "process_guid": "vendor", "kind": "telemetry_write", "path": "profile.csv"},
            {"time_ms": 3, "host": "lab", "process_guid": "vendor", "kind": "network_connection", "destination": "approved.example"},
        ]
        self.assertEqual(len(hunt(events)), 1)

    def test_event_order_and_window(self):
        events = load_events(HERE / "fixture_events.jsonl")[:3]
        late = [dict(event) for event in events]
        late[-1]["time_ms"] = 400_000
        self.assertEqual(hunt(late), [])
        backwards = [dict(event) for event in events]
        backwards[-1]["time_ms"] = 1500
        self.assertEqual(hunt(backwards), [])


if __name__ == "__main__":
    unittest.main()
