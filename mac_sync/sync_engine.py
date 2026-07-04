import os
import sys
import json
import subprocess
import urllib.request
import re
from datetime import datetime, timezone

from dotenv import load_dotenv

# --- CONFIGURATION ---
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, 'server', '.env')
load_dotenv(env_path)

NOTION_API_KEY = os.environ.get("NOTION_API_TOKEN")
NOTION_DB_ID = os.environ.get("NOTION_DATABASE_ID")
REMINDERS_LIST = os.environ.get("APPLE_REMINDERS_LIST", "Inbox")
STATE_FILE = "sync_state.json"

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
SWIFT_CLI = os.path.join(DIR_PATH, "reminders_cli.swift")
STATE_PATH = os.path.join(DIR_PATH, STATE_FILE)

# Apple -> Notion Priority Mapping
PRIORITY_A2N = {1: "1 - High ‼️", 5: "2 - Medium 😈", 9: "3 - Low 💃🏻", 0: None}
# Notion -> Apple Priority Mapping
PRIORITY_N2A = {"1 - High ‼️": 1, "2 - Medium 😈": 5, "3 - Low 💃🏻": 9}

# --- NOTION API HELPERS ---
def notion_request(endpoint, method="GET", payload=None):
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = json.dumps(payload).encode('utf-8') if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Notion API Error ({endpoint}): {e}")
        return None

def parse_iso(date_str):
    if not date_str: return 0.0
    date_str = date_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(date_str).timestamp()
    except:
        return 0.0

def fetch_notion_tasks():
    payload = {
        "filter": {
            "property": "Task Type",
            "select": {"equals": "Task"}
        }
    }
    res = notion_request(f"databases/{NOTION_DB_ID}/query", method="POST", payload=payload)
    if not res: return []
    
    tasks = []
    for page in res.get("results", []):
        props = page.get("properties", {})
        title_prop = props.get("Name", {}).get("title", [])
        title = title_prop[0]["text"]["content"] if title_prop else "Untitled"
        status_prop = props.get("Status", {}).get("select", {})
        status = status_prop.get("name") if status_prop else "To Do"
        
        priority_prop = props.get("Priority", {}).get("select", {})
        priority = priority_prop.get("name") if priority_prop else None
        
        date_prop = props.get("Due Date", {}).get("date", {})
        due_date_str = date_prop.get("start") if date_prop else None
        
        due_ts = parse_iso(due_date_str)
        
        notes_prop = props.get("Notes", {}).get("rich_text", [])
        notes = "".join(t.get("plain_text", "") for t in notes_prop) if notes_prop else ""
            
        tasks.append({
            "id": page["id"],
            "title": title,
            "status": status,
            "priority": priority,
            "due_ts": due_ts,
            "notes": notes,
            "archived": page.get("archived", False),
            "last_edited": parse_iso(page.get("last_edited_time", ""))
        })
    return tasks

def update_notion_task(page_id, status=None, priority=None, due_ts=None, title=None, notes=None):
    props = {}
    if status is not None:
        props["Status"] = {"select": {"name": status}}
    
    if priority is not None:
        props["Priority"] = {"select": {"name": priority}} if priority else {"select": None}
        
    if due_ts is not None:
        if due_ts > 0:
            iso_date = datetime.fromtimestamp(due_ts, tz=timezone.utc).astimezone().isoformat()
            props["Due Date"] = {"date": {"start": iso_date}}
        else:
            props["Due Date"] = {"date": None}
            
    if title is not None:
        props["Name"] = {"title": [{"text": {"content": title}}]}
        
    if notes is not None:
        props["Notes"] = {"rich_text": [{"text": {"content": notes}}]}

    if not props: return
    
    payload = {"properties": props}
    notion_request(f"pages/{page_id}", method="PATCH", payload=payload)

def create_notion_task(title, priority=0, due_ts=0, notes=""):
    props = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Task Type": {"select": {"name": "Task"}},
        "Status": {"select": {"name": "To Do"}}
    }
    
    p_name = PRIORITY_A2N.get(priority)
    if p_name:
        props["Priority"] = {"select": {"name": p_name}}
        
    if due_ts > 0:
        iso_date = datetime.fromtimestamp(due_ts, tz=timezone.utc).astimezone().isoformat()
        props["Due Date"] = {"date": {"start": iso_date}}
        
    if notes:
        props["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": props
    }
    res = notion_request("pages", method="POST", payload=payload)
    return res.get("id") if res else None

# --- REMINDERS CLI HELPERS ---
def run_swift(command, *args):
    cmd = ["swift", SWIFT_CLI, command] + list(args)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Swift Error: {e.stderr}")
        return None

def fetch_reminders():
    out = run_swift("fetch", REMINDERS_LIST)
    if out:
        try:
            return json.loads(out)
        except: return []
    return []

def complete_reminder(rem_id):
    run_swift("complete", rem_id)

def update_reminder_full(rem_id, title=None, notes=None, priority=None, due_ts=None):
    t = title if title is not None else ""
    n = notes if notes is not None else ""
    p = str(priority) if priority is not None else "-1"
    d = str(due_ts) if due_ts is not None else "-1"
    run_swift("update-full", rem_id, t, n, p, d)

# --- STATE MANAGEMENT ---
def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, 'r') as f:
                return json.load(f)
        except: pass
    return {}

def save_state(state):
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)

# --- ENGINE LOGIC ---
def sync():
    print(f"[{datetime.now()}] Starting Sync Engine...")
    state = load_state()
    
    reminders = fetch_reminders()
    notion_tasks = fetch_notion_tasks()
    notion_map = { t['id']: t for t in notion_tasks }
    
    new_state = {}
    
    for r in reminders:
        r_id = r["id"]
        r_title = r["title"]
        r_notes_raw = r.get("notes", "")
        r_comp = r["isCompleted"]
        r_prio = r["priority"]
        r_due = r.get("dueDate", 0)
        r_mod = r.get("lastModifiedDate", 0)
        
        # Clean Notes (remove Notion tag)
        r_notes_clean = re.sub(r'\n?\[Notion:\s*[a-zA-Z0-9\-]+\s*\]\n?', '', r_notes_raw).strip()
        
        match = re.search(r'\[Notion:\s*([a-zA-Z0-9\-]+)\s*\]', r_notes_raw)
        
        if not match:
            if not r_comp:
                print(f"Pushing new task to Notion: {r_title}")
                
                # Default to Medium if no priority is set during import
                update_prio_on_create = None
                if r_prio == 0:
                    r_prio = 5
                    update_prio_on_create = 5
                    
                n_id = create_notion_task(r_title, r_prio, r_due, r_notes_clean)
                if n_id:
                    new_notes_raw = (r_notes_clean + f"\n[Notion:{n_id}]").strip()
                    update_reminder_full(r_id, notes=new_notes_raw, priority=update_prio_on_create)
                    new_state[n_id] = {
                        "rem_id": r_id, "status": "To Do", "is_completed": False,
                        "priority": r_prio, "due_ts": r_due, "title": r_title, "notes": r_notes_clean
                    }
            continue
            
        n_id = match.group(1)
        if n_id not in notion_map: continue
            
        n_task = notion_map[n_id]
        n_status = n_task["status"]
        n_prio_name = n_task["priority"]
        n_mod = n_task["last_edited"]
        n_due = n_task["due_ts"]
        n_title = n_task["title"]
        n_notes = n_task["notes"]
        
        last = state.get(n_id, {"status": "To Do", "is_completed": False, "priority": 0, "due_ts": 0, "title": "", "notes": ""})
        
        # 1. Sync Completion Status (Bidirectional)
        if r_comp and not last.get("is_completed", False):
            if n_status != "Done 🙌":
                print(f"Marking Notion task as Done: {r_title}")
                update_notion_task(n_id, status="Done 🙌")
                n_status = "Done 🙌"
        elif n_status == "Done 🙌" and last.get("status") != "Done 🙌":
            if not r_comp:
                print(f"Marking Reminder as Done: {r_title}")
                complete_reminder(r_id)
                r_comp = True
                
        # 2. Sync Properties (State-based 3-Way Merge + Timestamp Conflict Resolution)
        def resolve_conflict(r_val, n_val, last_val, is_date=False):
            if is_date:
                r_changed = abs(r_val - last_val) > 60 and abs(r_val - n_val) > 60
                n_changed = abs(n_val - last_val) > 60 and abs(n_val - r_val) > 60
            else:
                r_changed = (r_val != last_val) and (r_val != n_val)
                n_changed = (n_val != last_val) and (n_val != r_val)
                
            if r_changed and n_changed:
                # Conflict! Both changed since last sync. Last-Writer-Wins using timestamps.
                if r_mod > n_mod:
                    return "r", r_val
                else:
                    return "n", n_val
            elif r_changed:
                return "r", r_val
            elif n_changed:
                return "n", n_val
            return None, None

        update_n_prio, update_n_due, update_n_title, update_n_notes = None, None, None, None
        update_r_prio, update_r_due, update_r_title, update_r_notes = None, None, None, None
        
        n_prio_int = PRIORITY_N2A.get(n_prio_name, 0)
        
        # Priority mapping
        winner, new_val = resolve_conflict(r_prio, n_prio_int, last.get("priority", 0))
        if winner == "r":
            update_n_prio = PRIORITY_A2N.get(new_val, False)
            n_prio_int = new_val
        elif winner == "n":
            update_r_prio = new_val
            r_prio = new_val
            
        # Due Date mapping
        winner, new_val = resolve_conflict(r_due, n_due, last.get("due_ts", 0), is_date=True)
        if winner == "r":
            update_n_due = new_val
            n_due = new_val
        elif winner == "n":
            update_r_due = new_val
            r_due = new_val
            
        # Title mapping
        winner, new_val = resolve_conflict(r_title, n_title, last.get("title", ""))
        if winner == "r":
            update_n_title = new_val
            n_title = new_val
        elif winner == "n":
            update_r_title = new_val
            r_title = new_val
            
        # Notes mapping
        winner, new_val = resolve_conflict(r_notes_clean, n_notes, last.get("notes", ""))
        if winner == "r":
            update_n_notes = new_val
            n_notes = new_val
        elif winner == "n":
            update_r_notes = (new_val + f"\n[Notion:{n_id}]").strip()
            r_notes_clean = new_val

        if update_n_prio is not None or update_n_due is not None or update_n_title is not None or update_n_notes is not None:
            print(f"Updating Notion metadata for: {r_title}")
            update_notion_task(n_id, priority=update_n_prio, due_ts=update_n_due, title=update_n_title, notes=update_n_notes)
            
        if update_r_prio is not None or update_r_due is not None or update_r_title is not None or update_r_notes is not None:
            print(f"Updating Reminder metadata for: {r_title}")
            update_reminder_full(r_id, priority=update_r_prio, due_ts=update_r_due, title=update_r_title, notes=update_r_notes)

        new_state[n_id] = {
            "rem_id": r_id, "status": n_status, "is_completed": r_comp,
            "priority": r_prio, "due_ts": r_due, "title": r_title, "notes": r_notes_clean
        }
        
    save_state(new_state)
    print(f"[{datetime.now()}] Sync Complete.")

if __name__ == "__main__":
    sync()
