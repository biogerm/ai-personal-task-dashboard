import json
import os
import requests
from src.utils.logger import get_logger

logger = get_logger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'abbr_cache.json')

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load abbr cache: %s", e)
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Failed to save abbr cache: %s", e)

def get_abbreviation(title, api_key):
    if not api_key:
        return title[:4]
        
    cache = load_cache()
    if title in cache:
        return cache[title]
        
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(api_key)
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": 'Please simplify the following task into a short phrase that captures its core meaning (not an acronym). For example, "Check snowboard marketplace for used items" should be simplified to "Snowboard market", and "Apply for US Visa" should be simplified to "US Visa". Keep it as short as possible (around 3-5 characters) while remaining easily understandable. Only output the simplified text, no quotes, no extra text. Task: "{}"'.format(title)
                }
            ],
            "max_tokens": 10,
            "temperature": 0.0
        }
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        abbr = result["choices"][0]["message"]["content"].strip()
        
        # Clean up possible quotes
        if abbr.startswith('"') and abbr.endswith('"'):
            abbr = abbr[1:-1]
            
        cache[title] = abbr
        save_cache(cache)
        return abbr
    except Exception as e:
        logger.error("Error generating abbreviation for '%s': %s", title, e)
        return title[:4]

def rewrite_title(title, max_lines, api_key):
    if not api_key:
        return title
        
    cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'rewrite_cache.json')
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            pass
            
    if title in cache and str(max_lines) in cache[title]:
        return cache[title][str(max_lines)]
        
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(api_key)
        }
        if max_lines == 1:
            prompt = 'Please summarize the following task title to fit on a dashboard single line. The output MUST be strictly between 12 and 13 Chinese characters (treat 2 English letters as 1 Chinese character). This is a hard physical limit. Do not make it shorter than 11 characters. Focus on the core action. Use Chinese. No quotes, no extra text. Task: "{}"'.format(title)
        else:
            prompt = 'Please refine the following task title so it reads naturally and fits within two lines of a dashboard (approximately 40-50 Chinese characters max). Preserve as much of the original information and context as possible, do NOT over-summarize. Use Chinese. No quotes, no extra text. Task: "{}"'.format(title)
            
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 30,
            "temperature": 0.0
        }
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result["choices"][0]["message"]["content"].strip()
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1]
            
        if title not in cache:
            cache[title] = {}
        cache[title][str(max_lines)] = rewritten
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
            
        return rewritten
    except Exception as e:
        logger.error("Error rewriting title '%s': %s", title, e)
        return title
