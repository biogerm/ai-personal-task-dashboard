import datetime
from flask import Blueprint, Response, current_app
from src.utils.i18n import t, get_locale


voice_bp = Blueprint("voice", __name__)


def generate_summary_text(data, config):
    reminders = data.get("reminders", [])
    projects = data.get("projects", [])

    reminder_count = len(reminders)
    project_count = len(projects)

    overdue_items = [r for r in reminders if r.get("urgency") == "overdue"]

    if reminder_count == 0 and project_count == 0:
        return t("voice.no_pending")

    sentences = []
    
    # We need to decide if we use space or no space between sentences based on locale
    # English uses a space, Chinese uses no space. 
    # Let's handle separator properly
    is_zh = get_locale() == "zh"
    sep = "" if is_zh else " "
    
    if reminder_count > 0:
        sentences.append(t("voice.pending_tasks", count=reminder_count))
        if overdue_items:
            num_od = len(overdue_items)
            if num_od > 0:
                sentences.append(t("voice.overdue_count", count=num_od))

        max_read = 3
        if config and "voiceSummary" in config:
            max_read = config["voiceSummary"].get("maxRemindersToRead", 3)

        to_read = reminders[:max_read]

        try:
            from src.merger import FixedOffset
        except ImportError:
            try:
                from merger import FixedOffset
            except ImportError:

                class FixedOffset(datetime.tzinfo):

                    def __init__(self, offset_hours):
                        delta = datetime.timedelta(hours=offset_hours)
                        self._offset = delta

                    def utcoffset(self, dt):
                        return self._offset

                    def tzname(self, dt):
                        return "UTC+2"

                    def dst(self, dt):
                        return datetime.timedelta(0)

        for i, r in enumerate(to_read):
            title = r.get("title", "")
            urgency = r.get("urgency", "no-date")

            if urgency == "overdue":
                due_desc = t("voice.due.overdue")
            elif urgency == "today":
                due_desc = t("voice.due.today")
            elif urgency == "upcoming":
                due_date_str = r.get("due_date")
                if due_date_str:
                    try:
                        parts = due_date_str.split("T")[0].split("-")
                        due_date = datetime.date(
                            int(parts[0]), int(parts[1]), int(parts[2]))
                        now = datetime.datetime.now(FixedOffset(2)).date()
                        days = (due_date - now).days
                        due_desc = t("voice.due.days", days=days)
                    except Exception:
                        due_desc = t("voice.due.future")
                else:
                    due_desc = t("voice.due.future")
            else:
                due_desc = t("voice.due.none")

            ordinal_key = f"voice.ordinal.{i+1}"
            prefix = t(ordinal_key)
            if prefix == ordinal_key:
                prefix = t("voice.number_prefix", n=i+1)
            
            if is_zh:
                sentences.append(f"{prefix}，{title}，{due_desc}。")
            else:
                sentences.append(f"{prefix}, {title}, {due_desc}.")

    if project_count > 0:
        first_title = projects[0].get("title", "")
        if first_title:
            if project_count == 1:
                sentences.append(t("voice.project.one", count=project_count, first=first_title))
            else:
                sentences.append(t("voice.project.many_with_top", count=project_count, first=first_title))
        else:
            sentences.append(t("voice.project.many_no_top", count=project_count))

    return sep.join(sentences)


@voice_bp.route("/api/voice-summary")
def get_voice_summary():
    try:
        from src.app import merger
        data = merger.get_data()
        config = merger._config
    except Exception:
        try:
            from app import merger
            data = merger.get_data()
            config = merger._config
        except Exception:
            try:
                data = current_app.merger.get_data()
                config = current_app.merger._config
            except Exception:
                data = {"reminders": [], "projects": []}
                config = {}

    text = generate_summary_text(data, config)
    return Response(text, mimetype="text/plain; charset=utf-8")
