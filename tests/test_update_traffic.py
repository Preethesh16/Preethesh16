import unittest
from datetime import date

from scripts.update_traffic import recent_daily_counts


class RecentDailyCountsTests(unittest.TestCase):
    def test_empty_window_has_fourteen_zero_days(self):
        self.assertEqual(recent_daily_counts({}, date(2026, 10, 4)), [0] * 14)

    def test_sparse_days_keep_calendar_spacing_across_month_boundary(self):
        snapshots = {"repo": {"clones": [
            {"timestamp": "2026-09-21T00:00:00Z", "count": 3},
            {"timestamp": "2026-10-04T00:00:00Z", "count": 7},
        ]}}
        self.assertEqual(
            recent_daily_counts(snapshots, date(2026, 10, 4)),
            [3] + [0] * 12 + [7],
        )

    def test_multiple_repositories_are_summed_by_day(self):
        snapshots = {
            "one": {"clones": [{"timestamp": "2026-10-03T00:00:00Z", "count": 2}]},
            "two": {"clones": [{"timestamp": "2026-10-03T00:00:00Z", "count": 5}]},
            "empty": {},
        }
        self.assertEqual(
            recent_daily_counts(snapshots, date(2026, 10, 4)),
            [0] * 12 + [7, 0],
        )

    def test_dates_outside_window_are_excluded(self):
        snapshots = {"repo": {"clones": [
            {"timestamp": "2026-09-20T00:00:00Z", "count": 100},
            {"timestamp": "2026-10-05T00:00:00Z", "count": 200},
        ]}}
        self.assertEqual(recent_daily_counts(snapshots, date(2026, 10, 4)), [0] * 14)


if __name__ == "__main__":
    unittest.main()
