import datetime
import sys
import os
import unittest

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

try:
    from unittest import mock
except ImportError:
    import mock

from src.merger import (  # noqa: E402
    _compute_urgency,
    _sort_reminders,
    _sort_projects,
    TaskMerger
)


class TestMerger(unittest.TestCase):

    @mock.patch('src.merger.datetime')
    def test_compute_urgency(self, mock_datetime):
        mock_now = mock.Mock()
        mock_now.date.return_value = datetime.date(2026, 6, 20)
        mock_datetime.datetime.now.return_value = mock_now
        mock_datetime.date = datetime.date

        self.assertEqual(_compute_urgency("2026-06-19"), "overdue")
        self.assertEqual(_compute_urgency("2026-06-20"), "today")
        self.assertEqual(_compute_urgency("2026-06-21"), "upcoming")
        self.assertEqual(_compute_urgency(None), "no-date")
        self.assertEqual(_compute_urgency("invalid-date"), "no-date")

    def test_sort_reminders(self):
        reminders = [
            {"id": 1, "urgency": "no-date", "due_date": None,
             "created_at": "2026-06-18"},
            {"id": 2, "urgency": "upcoming", "due_date": "2026-06-25",
             "created_at": "2026-06-18"},
            {"id": 3, "urgency": "overdue", "due_date": "2026-06-15",
             "created_at": "2026-06-18"},
            {"id": 4, "urgency": "today", "due_date": "2026-06-20",
             "created_at": "2026-06-18"},
            {"id": 5, "urgency": "overdue", "due_date": "2026-06-14",
             "created_at": "2026-06-18"},
        ]
        sorted_r = _sort_reminders(reminders)
        ids = [r["id"] for r in sorted_r]
        self.assertEqual(ids, [5, 3, 4, 2, 1])

    def test_sort_projects(self):
        projects = [
            {"id": 1, "priority_order": 1,
             "last_edited_at": "2026-06-18T10:00:00Z"},
            {"id": 2, "priority_order": 0,
             "last_edited_at": "2026-06-17T10:00:00Z"},
            {"id": 3, "priority_order": 0,
             "last_edited_at": "2026-06-19T10:00:00Z"},
            {"id": 4, "priority_order": 999,
             "last_edited_at": "2026-06-16T10:00:00Z"}
        ]
        sorted_p = _sort_projects(projects)
        ids = [p["id"] for p in sorted_p]
        self.assertEqual(ids, [3, 2, 1, 4])

    @mock.patch('src.merger.fetch_projects')
    @mock.patch('src.merger.datetime')
    def test_refresh_m2_fail(
        self, mock_datetime, mock_fetch_projects
    ):
        mock_now = mock.Mock()
        mock_now.date.return_value = datetime.date(2026, 6, 20)
        mock_now.isoformat.return_value = "2026-06-20T12:00:00+02:00"
        mock_datetime.datetime.now.return_value = mock_now
        mock_datetime.date = datetime.date

        config = {}
        merger = TaskMerger(config)

        merger._cache["projects"] = [{"id": "old_p"}]
        merger._cache["sources"]["notion"]["status"] = "error"

        mock_fetch_projects.side_effect = Exception("Notion API Error")

        merger.refresh()
        data = merger.get_data()

        self.assertEqual(data["sources"]["notion"]["status"], "error")
        self.assertEqual(len(data["projects"]), 1)
        self.assertEqual(data["projects"][0]["id"], "old_p")
        self.assertEqual(data["last_updated"], "2026-06-20T12:00:00+02:00")



    def test_get_data_deep_copy(self):
        config = {}
        merger = TaskMerger(config)
        merger._cache["reminders"] = [{"id": "1"}]

        data = merger.get_data()
        data["reminders"][0]["id"] = "2"

        self.assertEqual(merger._cache["reminders"][0]["id"], "1")


if __name__ == "__main__":
    unittest.main()
