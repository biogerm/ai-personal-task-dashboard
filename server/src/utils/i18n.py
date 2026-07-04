import os

_DICTIONARIES = {
    "en": {
        "voice.no_pending": "You currently have no pending tasks.",
        "voice.pending_tasks": "You have {count} pending tasks.",
        "voice.overdue_count": "{count} are overdue.",
        "voice.due.overdue": "Overdue",
        "voice.due.today": "Due Today",
        "voice.due.future": "due in future",
        "voice.due.days": "due in {days} days",
        "voice.due.none": "no due date",
        "voice.number_prefix": "Number {n}",
        "voice.project.one": "There is {count} active project on Notion, the highest priority is {first}.",
        "voice.project.many_with_top": "There are {count} active projects on Notion, the highest priority is {first}.",
        "voice.project.many_no_top": "There are {count} active projects on Notion.",
        
        # Ordinals
        "voice.ordinal.1": "First",
        "voice.ordinal.2": "Second",
        "voice.ordinal.3": "Third",
        "voice.ordinal.4": "Fourth",
        "voice.ordinal.5": "Fifth",
        "voice.ordinal.6": "Sixth",
        "voice.ordinal.7": "Seventh",
        "voice.ordinal.8": "Eighth",
        "voice.ordinal.9": "Ninth",
        "voice.ordinal.10": "Tenth",
    },
    "zh": {
        "voice.no_pending": "你目前没有待办任务。",
        "voice.pending_tasks": "你有 {count} 个待办任务。",
        "voice.overdue_count": "其中 {count} 个已过期。",
        "voice.due.overdue": "已过期",
        "voice.due.today": "今天到期",
        "voice.due.future": "未来到期",
        "voice.due.days": "{days} 天后到期",
        "voice.due.none": "无期限",
        "voice.number_prefix": "第 {n} 个",
        "voice.project.one": "Notion 上有 {count} 个项目在进行中，最高优先级的是 {first}。",
        "voice.project.many_with_top": "Notion 上有 {count} 个项目在进行中，最高优先级的是 {first}。",
        "voice.project.many_no_top": "Notion 上有 {count} 个项目在进行中。",
        
        "voice.ordinal.1": "第一",
        "voice.ordinal.2": "第二",
        "voice.ordinal.3": "第三",
        "voice.ordinal.4": "第四",
        "voice.ordinal.5": "第五",
        "voice.ordinal.6": "第六",
        "voice.ordinal.7": "第七",
        "voice.ordinal.8": "第八",
        "voice.ordinal.9": "第九",
        "voice.ordinal.10": "第十",
    }
}

def get_locale():
    return os.environ.get("APP_LOCALE", "en").lower()

def t(key, **kwargs):
    locale = get_locale()
    # Fallback to en if locale or key is missing
    dict_locale = _DICTIONARIES.get(locale, _DICTIONARIES["en"])
    text = dict_locale.get(key)
    if text is None:
        text = _DICTIONARIES["en"].get(key, key)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
