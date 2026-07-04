import os

def fix_widget(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add I18N dictionary at the top (after fm declaration)
    if "const APP_LOCALE" not in content:
        i18n_code = """
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
"""
        content = content.replace(
            'const cachePath = fm.joinPath(fm.documentsDirectory(), "notion_abbr_cache.json");',
            'const cachePath = fm.joinPath(fm.documentsDirectory(), "notion_abbr_cache.json");\n' + i18n_code
        )
    
    # 2. Replace hardcoded strings
    import re
    content = re.sub(r'content:\s*`You are a smart text abbreviator.*?`', 'content: getPrompt(maxAvailableVLen)', content, flags=re.DOTALL)
    content = re.sub(r'content:\s*`The abbreviation .*?`', 'content: getRetry(abbr, vLen, maxAvailableVLen)', content, flags=re.DOTALL)
    
    content = content.replace('"🎉 Cleared"', 't("cleared")')
    content = content.replace('"Untitled"', 't("untitled")')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

fix_widget("ios_widgets/NotionLockScreen_Left.js")
fix_widget("ios_widgets/NotionLockScreen_Right.js")
