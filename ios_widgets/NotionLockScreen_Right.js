// Variables used by Scriptable.
// icon-color: gray; icon-glyph: list-ul;

const NOTION_API_KEY = "__NOTION_API_KEY__";
const NOTION_DB_ID = "__NOTION_DB_ID__";
const NOTION_VIEW_URL = `notion://www.notion.so/${NOTION_DB_ID}?v=__NOTION_VIEW_ID__`;
const OPENAI_API_KEY = "__OPENAI_API_KEY__";

const fm = FileManager.local();
const cachePath = fm.joinPath(fm.documentsDirectory(), "notion_abbr_cache.json");

const APP_LOCALE = "__APP_LOCALE__";
const LOCALE = APP_LOCALE.includes("__APP") ? "zh" : APP_LOCALE;

const I18N = {
  en: { cleared: "🎉 Cleared", untitled: "Untitled" },
  zh: { cleared: "🎉 清空", untitled: "未命名" }
};
function t(key) {
  let lang = I18N[LOCALE] ? LOCALE : "zh";
  return I18N[lang][key] || I18N["en"][key] || key;
}

const LLM_PROMPT = {
  en: (maxV) => `You are a smart text abbreviator. Abbreviate the task name. Requirements: 1. Visual width must not exceed ${maxV} (1 Chinese char=2 width, 1 letter=1 width). 2. Keep the original meaning as much as possible without exceeding the limit. 3. No punctuation. 4. Never reply with error prompts.`,
  zh: (maxV) => `你是一个智能文本缩写助手。请缩写这个任务名。要求：1. 视觉宽度绝对不可超过 ${maxV} ！（1个汉字算2宽度，1个字母算1宽度）。2. 在不超长的前提下，【尽可能多地保留原意和单词】，切忌过度缩写！绝不能太短。3. 不要任何标点。4. 绝对不要回复'无效任务'或其他提示语。`
};
const LLM_RETRY = {
  en: (abbr, vLen, maxV) => `The abbreviation "${abbr}" has visual width ${vLen}, exceeding the limit ${maxV}! Please shorten it further strictly following the limit!`,
  zh: (abbr, vLen, maxV) => `你给的缩写 "${abbr}" 视觉宽度是 ${vLen}，超过了最大限制 ${maxV}！请进一步缩短，必须严格遵守长度限制！`
};
function getPrompt(maxV) { return LLM_PROMPT[LOCALE] ? LLM_PROMPT[LOCALE](maxV) : LLM_PROMPT["zh"](maxV); }
function getRetry(abbr, vLen, maxV) { return LLM_RETRY[LOCALE] ? LLM_RETRY[LOCALE](abbr, vLen, maxV) : LLM_RETRY["zh"](abbr, vLen, maxV); }


async function fetchTasks() {
  const url = `https://api.notion.com/v1/databases/${NOTION_DB_ID}/query`;
  let req = new Request(url);
  req.method = "POST";
  req.headers = {
    "Authorization": `Bearer ${NOTION_API_KEY}`,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
  };
  req.body = JSON.stringify({
    "filter": {
      "and": [
        { "property": "Task Type", "select": { "equals": "Task" } },
        { "or": [
          { "property": "Status", "select": { "equals": "To Do" } },
          { "property": "Status", "select": { "equals": "Doing" } },
          { "property": "Status", "select": { "is_empty": true } }
        ]}
      ]
    }
  });
  try {
    const res = await req.loadJSON();
    return res.results || [];
  } catch(e) { return []; }
}

function getVisualLength(str) {
  let len = 0;
  for (let i = 0; i < str.length; i++) {
    if (str.charCodeAt(i) > 255) len += 2;
    else len += 1;
  }
  return len;
}

async function getShortName(taskId, originalName, isLockScreen, maxAvailableVLen) {
  let cache = {};
  if (fm.fileExists(cachePath)) {
    try { cache = JSON.parse(fm.readString(cachePath)); } catch(e){}
  }
  
  if (getVisualLength(originalName) <= maxAvailableVLen) return originalName; 
  
  let cacheKey = taskId + (isLockScreen ? "_lock_" : "_large_") + maxAvailableVLen;
  if (cache[cacheKey]) return cache[cacheKey];
  
  let req = new Request("https://api.openai.com/v1/chat/completions");
  req.method = "POST";
  req.headers = {
    "Authorization": `Bearer ${OPENAI_API_KEY}`,
    "Content-Type": "application/json"
  };
  
  let messages = [
    {
      role: "system",
      content: getPrompt(maxAvailableVLen)
    },
    {
      role: "user",
      content: originalName
    }
  ];
  
  let finalStr = originalName;
  
  for (let attempt = 0; attempt < 2; attempt++) {
    req.body = JSON.stringify({
      model: "gpt-4o-mini",
      messages: messages,
      temperature: 0.1
    });
    
    try {
      let res = await req.loadJSON();
      if (res && res.choices && res.choices.length > 0) {
        let abbr = res.choices[0].message.content.trim();
        if (!abbr.includes("invalid") && !abbr.includes("sorry")) {
          finalStr = abbr;
          let vLen = getVisualLength(abbr);
          if (vLen <= maxAvailableVLen) {
            break; 
          } else {
            messages.push({ role: "assistant", content: abbr });
            messages.push({ role: "user", content: getRetry(abbr, vLen, maxAvailableVLen)});
          }
        } else {
          break; 
        }
      }
    } catch(e) { break; }
  }
  
  cache[cacheKey] = finalStr;
  fm.writeString(cachePath, JSON.stringify(cache));
  
  return finalStr;
}

function processRightWidgetTasks(tasks) {
  const now = new Date();
  const offset = now.getTimezoneOffset();
  const localToday = new Date(now.getTime() - (offset*60*1000)).toISOString().split('T')[0];
  
  const nextMonthDate = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
  const localNextMonth = new Date(nextMonthDate.getTime() - (offset*60*1000)).toISOString().split('T')[0];
  const prioScore = { "1 - High ‼️": 3, "2 - Medium 😈": 2, "3 - Low 💃🏻": 1 };

  let within30 = [];
  let noDue = [];
  let after30 = [];

  for (let t of tasks) {
    let dateStr = t.properties["Due Date"]?.date?.start;
    if (!dateStr) {
      noDue.push(t);
    } else {
      let dateOnly = dateStr.substring(0, 10);
      if (dateOnly > localToday && dateOnly <= localNextMonth) {
        within30.push(t);
      } else if (dateOnly > localNextMonth) {
        after30.push(t);
      }
    }
  }

  const sortPriorityDate = (a, b) => {
    let sA = prioScore[a.properties["Priority"]?.select?.name] || 0;
    let sB = prioScore[b.properties["Priority"]?.select?.name] || 0;
    if (sA !== sB) return sB - sA;
    let dA = a.properties["Due Date"]?.date?.start?.substring(0,10) || "9999-99-99";
    let dB = b.properties["Due Date"]?.date?.start?.substring(0,10) || "9999-99-99";
    return dA.localeCompare(dB);
  };

  within30.sort(sortPriorityDate);
  noDue.sort(sortPriorityDate);
  after30.sort(sortPriorityDate);

  return { within30, noDue, after30 };
}

function getPrefix(pName, dateStr, localToday, isLockScreen) {
  let diffDays = null;
  if (dateStr && dateStr !== "9999-99-99") {
    let dateOnly = dateStr.substring(0, 10);
    let todayDate = new Date(localToday);
    let dueDate = new Date(dateOnly);
    diffDays = Math.round((dueDate - todayDate) / (1000 * 60 * 60 * 24));
  }
  let pSymbolLock = "";
  let pSymbolLarge = "";
  if (pName === "1 - High ‼️") { pSymbolLock = "!!"; pSymbolLarge = "‼️"; }
  else if (pName === "2 - Medium 😈") { pSymbolLock = "!"; pSymbolLarge = "😈"; }
  else if (pName === "3 - Low 💃🏻") { pSymbolLock = "-"; pSymbolLarge = "💃"; }
  else { pSymbolLock = ""; pSymbolLarge = "🔵"; } 
  
  if (isLockScreen) {
    let dateStrLock = "";
    if (diffDays !== null) {
      if (diffDays < 0) dateStrLock = "x"; 
      else if (diffDays === 0) dateStrLock = "*"; 
      else if (diffDays > 99) dateStrLock = "99d";
      else dateStrLock = diffDays + "d"; 
    }
    return dateStrLock + pSymbolLock;
  } else {
    let dateStrLarge = "";
    if (diffDays !== null) dateStrLarge = diffDays + "d";
    return pSymbolLarge + (dateStrLarge ? " " + dateStrLarge : "");
  }
}

async function createWidget(groupedTasks, isLockScreen) {
  let w = new ListWidget();
  
  let maxLines = 14; 
  if (config.widgetFamily === "small") maxLines = 6;
  else if (config.widgetFamily === "medium") maxLines = 7;
  else if (config.widgetFamily === "large") maxLines = 14;
  else if (config.widgetFamily === "accessoryRectangular") maxLines = 4;

  if (!isLockScreen) {
    let gradient = new LinearGradient();
    gradient.colors = [new Color("#2c2c2e"), new Color("#1c1c1e")];
    gradient.locations = [0.0, 1.0];
    w.backgroundGradient = gradient;
    w.setPadding(10, 16, 10, 16); 
  } else {
    w.setPadding(2, 2, 2, 2);
    w.url = NOTION_VIEW_URL; 
  }

  const flatTasks = [...groupedTasks.within30, ...groupedTasks.noDue, ...groupedTasks.after30];
  if (flatTasks.length === 0) {
    let stack = w.addStack();
    stack.layoutHorizontally();
    let t = stack.addText(t("cleared"));
    t.font = Font.systemFont(13);
    if (!isLockScreen) t.textColor = Color.white();
    return w;
  }

  const now = new Date();
  const offset = now.getTimezoneOffset();
  const localToday = new Date(now.getTime() - (offset*60*1000)).toISOString().split('T')[0];

  let mainStack = w.addStack();
  mainStack.layoutVertically();
  let currentLines = 0;

  async function renderSection(title, tasksList) {
    if (tasksList.length === 0) return;
    
    let requiredSpace = isLockScreen ? 1 : 1.5; 
    if (currentLines + requiredSpace > maxLines) return;

    if (!isLockScreen && title !== "") {
      let headerStack = mainStack.addStack();
      let hText = headerStack.addText(title);
      hText.font = Font.boldSystemFont(9); 
      hText.textColor = new Color("#ffffff", 0.4); 
      currentLines += 0.5;
    }

    for (let t of tasksList) {
      if (currentLines + 1 > maxLines) break; 
      
      let titleArr = t.properties["Name"]?.title;
      let originalName = titleArr && titleArr.length > 0 ? titleArr[0].plain_text : t("untitled");

      let dateStr = t.properties["Due Date"]?.date?.start;
      let pName = t.properties["Priority"]?.select?.name;
      let prefix = getPrefix(pName, dateStr, localToday, isLockScreen);
      
      let prefixVLen = getVisualLength(prefix);
      let totalMaxVLen = isLockScreen ? 20 : 38; 
      let maxAvailableVLen = totalMaxVLen - prefixVLen; 

      let taskName = await getShortName(t.id, originalName, isLockScreen, maxAvailableVLen);

      let rowStack = mainStack.addStack();
      rowStack.layoutHorizontally();
      rowStack.centerAlignContent(); 
      
      if (!isLockScreen) {
        rowStack.backgroundColor = new Color("#ffffff", 0.08);
        rowStack.cornerRadius = 8;
        rowStack.setPadding(4, 10, 4, 10);
        rowStack.url = t.url.replace("https://", "notion://");
      }
      
      let textNode = rowStack.addText(prefix + (isLockScreen ? "" : " ") + taskName);
      
      if (isLockScreen) {
        textNode.font = Font.mediumSystemFont(13);
      } else {
        textNode.font = Font.systemFont(14);
        textNode.textColor = new Color("#e5e5ea");
      }
      textNode.lineLimit = 1;
      
      rowStack.addSpacer();
      currentLines++;
      if (currentLines < maxLines) mainStack.addSpacer(isLockScreen ? 2 : 2);
    }
    
    if (!isLockScreen && currentLines < maxLines) {
      mainStack.addSpacer(2); 
    }
  }

  if (isLockScreen) {
    await renderSection("", flatTasks);
  } else {
    await renderSection("WITHIN 30 DAYS", groupedTasks.within30);
    await renderSection("NO DATE", groupedTasks.noDue);
    await renderSection("AFTER 30 DAYS", groupedTasks.after30);
  }
  
  w.addSpacer();
  return w;
}

const isLockScreen = config.widgetFamily === "accessoryRectangular";
const tasks = await fetchTasks();
const finalTasks = processRightWidgetTasks(tasks);
const widget = await createWidget(finalTasks, isLockScreen);

if (config.runsInWidget) Script.setWidget(widget);
else widget.presentLarge();
Script.complete();
