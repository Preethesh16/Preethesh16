import copy
import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('traffic', Path(__file__).with_name('update_traffic.py'))
traffic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(traffic)


class TrafficTests(unittest.TestCase):
    def test_only_explicitly_public_repositories_are_counted(self):
        self.assertEqual(traffic.public_repository_names([
            {'name': 'public', 'private': False},
            {'name': 'private', 'private': True},
            {'name': 'unknown'},
            {'name': 'public', 'private': False},
        ]), ['public'])

    def test_window_uses_calendar_days_and_daily_counts(self):
        snapshots = {
            'a': {'count': 999, 'clones': [
                {'timestamp': '2026-09-20T00:00:00Z', 'count': 100},
                {'timestamp': '2026-09-21T00:00:00Z', 'count': 2},
                {'timestamp': '2026-10-04T00:00:00Z', 'count': 4},
                {'timestamp': '2026-10-05T00:00:00Z', 'count': 100},
            ]},
            'b': {'clones': [{'timestamp': '2026-10-04T00:00:00Z', 'count': 3}]},
        }
        result = traffic.recent_window(snapshots, date(2026, 10, 4))
        self.assertEqual(len(result), 14)
        self.assertEqual(result[0], {'date': '2026-09-21', 'clones': 2})
        self.assertEqual(result[-1], {'date': '2026-10-04', 'clones': 7})
        self.assertEqual(sum(row['clones'] for row in result), 9)
        self.assertEqual(result[1]['clones'], 0)
        shifted = traffic.recent_window(snapshots, date(2026, 10, 5))
        self.assertEqual(shifted[0]['date'], '2026-09-22')
        self.assertEqual(sum(row['clones'] for row in shifted), 107)

    def test_empty_successful_response_is_fourteen_zeroes(self):
        rows = traffic.recent_window({'a': {'clones': []}}, date(2026, 1, 2))
        self.assertEqual(rows[0]['date'], '2025-12-20')
        self.assertEqual(len(rows), 14)
        self.assertEqual(sum(row['clones'] for row in rows), 0)

    def test_offline_render_preserves_sync_and_marks_partial(self):
        history = {
            'lastUpdated': '2026-10-04T09:00:00+00:00',
            'accessibleRepositories': ['a'],
            'publicRepositories': ['a'],
            'inaccessibleRepositories': ['b (403)'],
            'repositories': {
                'a': {'baselineClones': 10, 'days': {'2026-10-04': {'clones': 3}}},
                'b': {'days': {'2026-10-04': {'clones': 999}}},
            },
        }
        original = copy.deepcopy(history)
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / 'traffic.svg'
            with patch.object(traffic, 'SVG_PATH', svg), patch.object(traffic, 'BADGE_PATH', Path(directory) / 'traffic.json'):
                traffic.write_outputs(history)
            rendered = svg.read_text()
            self.assertIn('PARTIAL', rendered)
            self.assertIn('2026-09-21 — 2026-10-04 UTC', rendered)
            self.assertIn('2026-10-04: 3 clones', rendered)
            self.assertIn('SYNC / OCT 04, 2026', rendered)
            self.assertNotIn('LIVE FEED', rendered)
            self.assertIn('1012 total tracked clones; 1 repositories', rendered)
            self.assertIn('REPOS', rendered)
        self.assertEqual(history, original)


if __name__ == '__main__':
    unittest.main()
