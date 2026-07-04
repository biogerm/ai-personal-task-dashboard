window.APP_LOCALE = "en"; // Default, updated on API fetch

const I18N_DICT = {
    en: {
        "ui.no_active": "No active projects",
        "ui.due_today": "Due Today",
        "ui.overdue": "Overdue",
        "ui.other_projects": "Other Projects",
        "ui.more": "More...",
        "ui.more_projects": "And {count} more projects...",
        "ui.overdue_tag": "Overdue",
        "ui.today_tag": "Today",
        "ui.offline": "⚠ Offline - Last updated: {time}",
        "ui.sync_failed": "⚠ {sources} Sync Failed",
        "ui.loading": "⏳ Loading...",
        "ui.last_sync": "Last sync: {time}",
        "ui.unknown": "Unknown"
    },
    zh: {
        "ui.no_active": "暂无进行中的项目",
        "ui.due_today": "今天到期",
        "ui.overdue": "已过期",
        "ui.other_projects": "其他项目",
        "ui.more": "还有...",
        "ui.more_projects": "还有 {count} 个项目...",
        "ui.overdue_tag": "已过期",
        "ui.today_tag": "今天",
        "ui.offline": "⚠ 离线 — 上次更新: {time}",
        "ui.sync_failed": "⚠ {sources} 同步失败",
        "ui.loading": "⏳ 正在加载...",
        "ui.last_sync": "上次同步: {time}",
        "ui.unknown": "未知"
    }
};

function t(key, params = {}) {
    let lang = I18N_DICT[window.APP_LOCALE] ? window.APP_LOCALE : "en";
    let text = I18N_DICT[lang][key] || I18N_DICT["en"][key] || key;
    
    for (let k in params) {
        text = text.replace(`{${k}}`, params[k]);
    }
    return text;
}
