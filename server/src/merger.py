import copy
import datetime
import logging
import time

try:
    from connectors.notion import fetch_projects
except ImportError:
    try:
        from src.connectors.notion import fetch_projects
    except ImportError:
        fetch_projects = None

try:
    from src.utils.llm import get_abbreviation, rewrite_title
except ImportError:
    def get_abbreviation(title, key):
        return title[:4]
    def rewrite_title(title, max_lines, key):
        return title


class FixedOffset(datetime.tzinfo):
    def __init__(self, offset_hours):
        self._offset = datetime.timedelta(hours=offset_hours)
        self._offset_hours = offset_hours

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        if self._offset_hours >= 0:
            return "UTC+%s" % self._offset_hours
        return "UTC%s" % self._offset_hours

    def dst(self, dt):
        return datetime.timedelta(0)


def _compute_urgency(due_date_str):
    if due_date_str is None:
        return "no-date"
    try:
        parts = due_date_str.split("T")[0].split("-")
        due_date = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return "no-date"
    now = datetime.datetime.now(FixedOffset(2))
    today = now.date()
    if due_date < today:
        return "overdue"
    elif due_date == today:
        return "today"
    else:
        return "upcoming"


def _sort_reminders(reminders):
    urgency_weight_map = {
        "overdue": 0,
        "today": 1,
        "upcoming": 2,
        "no-date": 3
    }

    def get_sort_key(r):
        urgency = r.get("urgency", "no-date")
        weight = urgency_weight_map.get(urgency, 3)
        due_date_str = r.get("due_date")
        if due_date_str:
            try:
                parts = due_date_str.split("T")[0].split("-")
                due_date_val = datetime.date(
                    int(parts[0]), int(parts[1]), int(parts[2])
                )
            except Exception:
                due_date_val = datetime.date.max
        else:
            due_date_val = datetime.date.max
        created_at = r.get("created_at", "")
        return (weight, due_date_val, created_at)

    return sorted(reminders, key=get_sort_key)


def _sort_projects(projects):
    def get_sort_key_final(p):
        priority = p.get("priority_order", 999)
        due = p.get("due_date")
        if due:
            try:
                parts = due.split("T")[0].split("-")
                d_val = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            except Exception:
                d_val = datetime.date.max
        else:
            d_val = datetime.date.max
        return (priority, d_val)

    projects_sorted = sorted(projects, key=lambda x: x.get("last_edited_at", ""), reverse=True)
    return sorted(projects_sorted, key=get_sort_key_final)


class TaskMerger(object):
    def __init__(self, config):
        self._config = config
        self._cache = {
            "last_updated": None,
            "sources": {
                "reminders": {
                    "status": "pending", "last_sync": None, "count": 0
                },
                "notion": {
                    "status": "pending", "last_sync": None, "count": 0
                }
            },
            "reminders": [],
            "projects": []
        }

    def refresh(self):
        start_time = time.time()
        now_dt = datetime.datetime.now(FixedOffset(2))
        now_str = now_dt.isoformat()
        # Disable reminders fetch as iCloud CalDAV is obsolete for new lists
        self._cache["reminders"] = []
        self._cache["sources"]["reminders"]["status"] = "ok"
        self._cache["sources"]["reminders"]["last_sync"] = now_str
        self._cache["sources"]["reminders"]["count"] = 0

        try:
            if fetch_projects is not None:
                projects_data = fetch_projects(self._config)
                self._cache["projects"] = projects_data
                self._cache["sources"]["notion"]["status"] = "ok"
                self._cache["sources"]["notion"]["last_sync"] = now_str
                self._cache["sources"]["notion"]["count"] = len(projects_data)
        except Exception as e:
            logging.error("Failed to fetch projects: %s", str(e))
            self._cache["sources"]["notion"]["status"] = "error"
            
        openai_key = self._config.get("credentials", {}).get("OPENAI_API_KEY")

        for p in self._cache["projects"]:
            p["urgency"] = _compute_urgency(p.get("due_date"))
            # Abbreviation for calendar (if needed)
            if p.get("due_date"):
                p["abbr"] = get_abbreviation(p.get("title", ""), openai_key)
            else:
                p["abbr"] = ""
            
            # Rewrite long titles
            title = p.get("title", "")
            urgency = p.get("urgency", "no-date")
            if len(title) > 18:
                if urgency == "overdue":
                    p["title"] = rewrite_title(title, 2, openai_key)
                elif urgency != "today":
                    p["title"] = rewrite_title(title, 1, openai_key)

        self._cache["reminders"] = _sort_reminders(self._cache["reminders"])
        self._cache["projects"] = _sort_projects(self._cache["projects"])

        err_rem = self._cache["sources"]["reminders"]["status"] == "error"
        err_notion = self._cache["sources"]["notion"]["status"] == "error"
        if not (err_rem and err_notion):
            self._cache["last_updated"] = now_str

        elapsed = time.time() - start_time
        logging.info("Refresh complete: reminders=%d, projects=%d, elapsed=%.1fs",
                     len(self._cache["reminders"]),
                     len(self._cache["projects"]),
                     elapsed)

    def get_data(self):
        return copy.deepcopy(self._cache)
