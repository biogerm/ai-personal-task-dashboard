import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))
from src.routes.voice import generate_summary_text  # noqa: E402


def test_no_tasks():
    data = {"reminders": [], "projects": []}
    config = {}
    text = generate_summary_text(data, config)
    assert text == "You currently have no pending tasks."


def test_with_overdue():
    data = {
        "reminders": [
            {"title": "Pay Rent", "urgency": "overdue"},
            {"title": "Buy Milk", "urgency": "today"},
        ],
        "projects": []
    }
    config = {}
    text = generate_summary_text(data, config)
    expected = "You have 2 pending tasks. 1 are overdue. First, Pay Rent, Overdue. Second, Buy Milk, Due Today."
    assert text == expected


def test_all_upcoming():
    class FixedOffset(datetime.tzinfo):

        def __init__(self, offset_hours):
            self._offset = datetime.timedelta(hours=offset_hours)

        def utcoffset(self, dt):
            return self._offset

        def tzname(self, dt):
            return "UTC+2"

        def dst(self, dt):
            return datetime.timedelta(0)

    now = datetime.datetime.now(FixedOffset(2)).date()
    due = now + datetime.timedelta(days=3)
    due_str = due.isoformat()

    data = {
        "reminders": [
            {"title": "Haircut", "urgency": "upcoming", "due_date": due_str},
        ],
        "projects": []
    }
    config = {}
    text = generate_summary_text(data, config)
    expected = "You have 1 pending tasks. First, Haircut, due in 3 days."
    assert text == expected


def test_full_summary():
    data = {
        "reminders": [
            {"title": "Buy Milk", "urgency": "today"},
        ],
        "projects": [
            {"title": "Personal Website Refactor"}
        ]
    }
    config = {}
    text = generate_summary_text(data, config)
    expected = ("You have 1 pending tasks. First, Buy Milk, Due Today. "
                "There is 1 active project on Notion, the highest priority is Personal Website Refactor.")
    assert text == expected


def test_max_reminders():
    data = {
        "reminders": [
            {"title": "A", "urgency": "today"},
            {"title": "B", "urgency": "today"},
            {"title": "C", "urgency": "today"},
            {"title": "D", "urgency": "today"},
        ],
        "projects": []
    }
    config = {"voiceSummary": {"maxRemindersToRead": 2}}
    text = generate_summary_text(data, config)
    expected = "You have 4 pending tasks. First, A, Due Today. Second, B, Due Today."
    assert text == expected
