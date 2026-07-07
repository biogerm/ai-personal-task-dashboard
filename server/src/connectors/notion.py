import time
import requests
from src.utils.logger import get_logger
from src.utils.exceptions import (
    AuthenticationError,
    NotionQueryError,
    NotionRateLimitError
)

logger = get_logger("notion_connector")


def _query_database(db_id, token, filter_body, start_cursor=None):
    url = "https://api.notion.com/v1/databases/{}/query".format(db_id)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    payload = {
        "filter": filter_body,
        "sorts": [
            {
                "property": "Priority",
                "direction": "ascending"
            },
            {
                "timestamp": "last_edited_time",
                "direction": "descending"
            }
        ],
        "page_size": 100
    }

    if start_cursor:
        payload["start_cursor"] = start_cursor

    retries = 0
    while retries <= 3:
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=10)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                logger.warning(
                    "Notion API rate limited. Retrying after %s seconds.",
                    retry_after
                )
                time.sleep(retry_after)
                retries += 1
                continue

            if response.status_code == 401:
                raise AuthenticationError("Notion Authentication Failed")

            if response.status_code == 400:
                logger.error("Notion Query Error: %s", response.text)
                raise NotionQueryError(
                    "Invalid request: {}".format(response.text))

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise ConnectionError("Notion API connection timeout")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Notion API connection error")

    raise NotionRateLimitError(
        "Exceeded maximum retries for Notion API rate limit")


def _parse_page(page, config):
    priority_values = config["notion"].get("priorityValues", [])
    try:
        title_array = page["properties"]["Name"]["title"]
        if not title_array:
            logger.warning("Page %s missing title.", page.get("id"))
            return None
        title = "".join(t.get("plain_text", "") for t in title_array)
        if not title:
            logger.warning("Page %s title is empty.", page.get("id"))
            return None
    except KeyError:
        logger.warning("Page %s missing title property.", page.get("id"))
        return None

    try:
        priority_select = page["properties"]["Priority"]["select"]
        priority = priority_select["name"] if priority_select else None
    except KeyError:
        priority = None

    priority_label = None
    priority_emoji = None
    if priority:
        try:
            # Extract "High" from formats like "1 - High ‼️"
            priority_label = priority.split("-")[1].strip().split(" ")[0]
            
            orig_parts = priority.split(" ")
            if len(orig_parts) > 1:
                priority_emoji = orig_parts[-1]
        except IndexError:
            priority_label = None
            priority_emoji = None
        except Exception:
            priority_label = None
            priority_emoji = None

    priority_order = _priority_order(priority, priority_values)

    due_date = None
    try:
        date_prop = page["properties"].get("Due Date")
        if date_prop and date_prop.get("date"):
            due_date = date_prop["date"]["start"].split("T")[0]
    except KeyError:
        pass

    created_by_id = page.get("created_by", {}).get("id")
    bot_id = config.get("notion", {}).get("integrationBotId")
    is_ios_reminder = (created_by_id == bot_id) if bot_id else False

    return {
        "id": page.get("id"),
        "source": "notion",
        "is_ios_reminder": is_ios_reminder,
        "title": title,
        "priority": priority,
        "priority_label": priority_label,
        "priority_emoji": priority_emoji,
        "priority_order": priority_order,
        "due_date": due_date,
        "last_edited_at": page.get("last_edited_time"),
        "url": page.get("url")
    }


def _priority_order(priority_value, priority_values):
    if priority_value is None:
        return 999
    try:
        return priority_values.index(priority_value)
    except ValueError:
        return 999


def fetch_projects(config):
    token = config["credentials"]["NOTION_API_TOKEN"]
    db_id = config["credentials"]["NOTION_DATABASE_ID"]
    status_field = config["notion"]["statusField"]

    filter_body = {
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
                        "property": status_field,
                        "select": {
                            "equals": "To Do"
                        }
                    },
                    {
                        "property": status_field,
                        "select": {
                            "equals": "Doing"
                        }
                    }
                ]
            }
        ]
    }

    projects = []
    has_more = True
    next_cursor = None

    while has_more:
        results = _query_database(db_id, token, filter_body, next_cursor)
        for page in results.get("results", []):
            project = _parse_page(page, config)
            if project is not None:
                projects.append(project)

        has_more = results.get("has_more", False)
        next_cursor = results.get("next_cursor")

    return projects
