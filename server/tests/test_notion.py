from unittest.mock import patch
from src.connectors.notion import _parse_page, _priority_order, fetch_projects


def test_priority_order():
    priority_values = ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"]
    assert _priority_order("1 - High ‼️", priority_values) == 0
    assert _priority_order("3 - Low 💃🏻", priority_values) == 2
    assert _priority_order(None, priority_values) == 999
    assert _priority_order("Unknown", priority_values) == 999


def test_parse_page_with_priority():
    page = {
        "id": "123",
        "properties": {
            "Name": {
                "title": [{"plain_text": "Test Project"}]
            },
            "Priority": {
                "select": {"name": "1 - High ‼️"}
            },
            "Due Date": {
                "date": {"start": "2026-06-30"}
            }
        },
        "last_edited_time": "2026-06-18T14:30:00.000Z",
        "url": "https://notion.so/123"
    }
    config = {"notion": {"priorityValues": ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"]}}
    result = _parse_page(page, config)
    assert result is not None
    assert result["id"] == "123"
    assert result["title"] == "Test Project"
    assert result["priority"] == "1 - High ‼️"
    assert result["priority_label"] == "High"
    assert result["priority_order"] == 0
    assert result["due_date"] == "2026-06-30"
    assert result["last_edited_at"] == "2026-06-18T14:30:00.000Z"
    assert result["url"] == "https://notion.so/123"

def test_parse_page_medium_priority():
    page = {
        "id": "123a",
        "properties": {
            "Name": {"title": [{"plain_text": "Medium Proj"}]},
            "Priority": {"select": {"name": "2 - Medium 😈"}}
        }
    }
    config = {"notion": {"priorityValues": ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"]}}
    result = _parse_page(page, config)
    assert result["priority_label"] == "Medium"
    assert result["priority_order"] == 1

def test_parse_page_low_priority():
    page = {
        "id": "123b",
        "properties": {
            "Name": {"title": [{"plain_text": "Low Proj"}]},
            "Priority": {"select": {"name": "3 - Low 💃🏻"}}
        }
    }
    config = {"notion": {"priorityValues": ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"]}}
    result = _parse_page(page, config)
    assert result["priority_label"] == "Low"
    assert result["priority_order"] == 2

def test_parse_page_unknown_priority():
    page = {
        "id": "123c",
        "properties": {
            "Name": {"title": [{"plain_text": "Unknown Proj"}]},
            "Priority": {"select": {"name": "Unknown"}}
        }
    }
    config = {"notion": {"priorityValues": ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"]}}
    result = _parse_page(page, config)
    # Does not crash, and parses cleanly or returns None
    assert result["priority"] == "Unknown"
    assert result["priority_label"] is None

def test_parse_page_without_priority():
    page = {
        "id": "124",
        "properties": {
            "Name": {
                "title": [{"plain_text": "Test Project No Priority"}]
            },
            "Priority": {
                "select": None
            }
        },
        "last_edited_time": "2026-06-18T14:30:00.000Z",
        "url": "https://notion.so/124"
    }
    config = {"notion": {"priorityValues": ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"]}}
    result = _parse_page(page, config)
    assert result is not None
    assert result["priority"] is None
    assert result["priority_label"] is None
    assert result["priority_order"] == 999
    assert result["due_date"] is None


def test_parse_page_empty_title():
    page = {
        "id": "125",
        "properties": {
            "Name": {
                "title": []
            }
        }
    }
    config = {"notion": {"priorityValues": ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"]}}
    assert _parse_page(page, config) is None


@patch('src.connectors.notion._query_database')
def test_fetch_projects(mock_query):
    config = {
        "credentials": {
            "NOTION_API_TOKEN": "token",
            "NOTION_DATABASE_ID": "dbid"
        },
        "notion": {
            "priorityValues": ["1 - High ‼️", "2 - Medium 😈", "3 - Low 💃🏻"],
            "statusField": "Status",
            "doneValue": "Done 🙌"
        }
    }

    mock_query.side_effect = [
        {
            "results": [
                {
                    "id": "1",
                    "properties": {
                        "Name": {
                            "title": [{"plain_text": "P1"}]
                        },
                        "Priority": {
                            "select": {"name": "1 - High ‼️"}
                        }
                    },
                    "last_edited_time": "2026-06-18T14:30:00.000Z",
                    "url": "https://notion.so/1"
                }
            ],
            "has_more": True,
            "next_cursor": "cursor1"
        },
        {
            "results": [
                {
                    "id": "2",
                    "properties": {
                        "Name": {
                            "title": [{"plain_text": "P2"}]
                        },
                        "Priority": {
                            "select": None
                        }
                    },
                    "last_edited_time": "2026-06-18T14:30:00.000Z",
                    "url": "https://notion.so/2"
                }
            ],
            "has_more": False,
            "next_cursor": None
        }
    ]

    projects = fetch_projects(config)
    assert len(projects) == 2
    assert projects[0]["title"] == "P1"
    assert projects[1]["title"] == "P2"
    assert mock_query.call_count == 2
    expected_filter = {
        "and": [
            {
                "property": "Task Type",
                "select": {
                    "equals": "Task"
                }
            },
            {
                "or": [
                    {
                        "property": "Status",
                        "select": {
                            "equals": "To Do"
                        }
                    },
                    {
                        "property": "Status",
                        "select": {
                            "equals": "Doing"
                        }
                    }
                ]
            }
        ]
    }

    mock_query.assert_any_call(
        "dbid", "token",
        expected_filter,
        None
    )
    mock_query.assert_any_call(
        "dbid", "token",
        expected_filter,
        "cursor1"
    )
