import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
import os
import sys

# Add mac_sync to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sync_engine import (
    parse_iso, fetch_notion_tasks, update_notion_task, create_notion_task,
    run_swift, fetch_reminders, complete_reminder, update_reminder_full,
    sync, load_state, save_state, PRIORITY_A2N, PRIORITY_N2A
)

def test_parse_iso():
    assert parse_iso(None) == 0.0
    assert parse_iso("") == 0.0
    assert parse_iso("invalid") == 0.0
    ts = parse_iso("2026-06-18T14:30:00.000Z")
    assert ts > 0

@patch("sync_engine.urllib.request.urlopen")
def test_fetch_notion_tasks(mock_urlopen):
    mock_res = MagicMock()
    mock_res.read.return_value = json.dumps({
        "results": [
            {
                "id": "page-1",
                "properties": {
                    "Name": {"title": [{"text": {"content": "Test Task"}}]},
                    "Status": {"select": {"name": "To Do"}},
                    "Priority": {"select": {"name": "1 - High ‼️"}},
                    "Due Date": {"date": {"start": "2026-06-30T00:00:00.000Z"}},
                    "Notes": {"rich_text": [{"plain_text": "Some notes"}]}
                },
                "last_edited_time": "2026-06-18T14:30:00.000Z",
                "archived": False
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_res
    
    tasks = fetch_notion_tasks()
    assert len(tasks) == 1
    t = tasks[0]
    assert t["id"] == "page-1"
    assert t["title"] == "Test Task"
    assert t["status"] == "To Do"
    assert t["priority"] == "1 - High ‼️"
    assert t["notes"] == "Some notes"

@patch("sync_engine.subprocess.run")
def test_run_swift(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = "[\n  {\"id\":\"123\", \"title\":\"R1\"}\n]"
    mock_run.return_value = mock_res
    
    out = run_swift("fetch", "List")
    assert out == "[\n  {\"id\":\"123\", \"title\":\"R1\"}\n]"
    mock_run.assert_called_once()

@patch("sync_engine.run_swift")
def test_fetch_reminders(mock_rs):
    mock_rs.return_value = '[{"id": "1", "title": "R1"}]'
    rems = fetch_reminders()
    assert len(rems) == 1
    assert rems[0]["id"] == "1"

@patch("sync_engine.os.path.exists", return_value=True)
@patch("sync_engine.open", new_callable=mock_open, read_data='{"page-1": {"status": "To Do"}}')
def test_load_state(mock_file, mock_exists):
    state = load_state()
    assert "page-1" in state
    assert state["page-1"]["status"] == "To Do"

@patch("sync_engine.fetch_reminders")
@patch("sync_engine.fetch_notion_tasks")
@patch("sync_engine.load_state")
@patch("sync_engine.save_state")
@patch("sync_engine.create_notion_task")
@patch("sync_engine.update_reminder_full")
def test_sync_new_reminder(mock_upd_r, mock_create_n, mock_save, mock_load, mock_fetch_n, mock_fetch_r):
    mock_load.return_value = {}
    mock_fetch_n.return_value = []
    mock_fetch_r.return_value = [
        {"id": "r1", "title": "New Apple Task", "isCompleted": False, "priority": 0, "dueDate": 0, "notes": ""}
    ]
    mock_create_n.return_value = "n1"
    
    sync()
    
    mock_create_n.assert_called_once_with("New Apple Task", 5, 0, "") # defaults to 5
    mock_upd_r.assert_called_once_with("r1", priority=5, notes="[Notion:n1]")
    mock_save.assert_called_once()
    saved_state = mock_save.call_args[0][0]
    assert "n1" in saved_state
    assert saved_state["n1"]["title"] == "New Apple Task"
