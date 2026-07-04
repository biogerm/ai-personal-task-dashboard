import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
from src.utils.exceptions import CalDAVError, AuthenticationError
from src.utils.logger import get_logger

logger = get_logger(__name__)

CALDAV_NS = 'urn:ietf:params:xml:ns:caldav'
DAV_NS = 'DAV:'
CS_NS = 'http://calendarserver.org/ns/'


def _check_response(response):
    if response.status_code == 401:
        raise AuthenticationError("iCloud authentication failed")
    if response.status_code != 207:
        logger.error("HTTP %s response: %s", response.status_code, response.text[:500])
        raise CalDAVError("Expected 207 Multi-Status, got %s" % response.status_code)


def _find_principal(base_url, auth):
    body = (
        '<?xml version="1.0"?>\n'
        '<d:propfind xmlns:d="DAV:">\n'
        '  <d:prop>\n'
        '    <d:current-user-principal/>\n'
        '  </d:prop>\n'
        '</d:propfind>'
    )
    headers = {'Content-Type': 'text/xml', 'Depth': '0'}
    try:
        resp = requests.request(
            'PROPFIND', base_url, headers=headers,
            data=body.encode('utf-8'), auth=auth, timeout=5
        )
    except requests.exceptions.RequestException as e:
        logger.error("Connection error in _find_principal: %s", e)
        raise ConnectionError(str(e))
    _check_response(resp)

    root = ET.fromstring(resp.content)
    href_elem = root.find('.//{DAV:}current-user-principal/{DAV:}href')
    if href_elem is not None and href_elem.text:
        return href_elem.text.strip()
    raise CalDAVError("Could not find principal URL in response")


def _find_calendar_home(principal_url, auth):
    body = (
        '<?xml version="1.0"?>\n'
        '<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">\n'
        '  <d:prop>\n'
        '    <c:calendar-home-set/>\n'
        '  </d:prop>\n'
        '</d:propfind>'
    )
    headers = {'Content-Type': 'text/xml', 'Depth': '0'}
    try:
        resp = requests.request(
            'PROPFIND', principal_url, headers=headers,
            data=body.encode('utf-8'), auth=auth, timeout=5
        )
    except requests.exceptions.RequestException as e:
        logger.error("Connection error in _find_calendar_home: %s", e)
        raise ConnectionError(str(e))
    _check_response(resp)

    root = ET.fromstring(resp.content)
    href_elem = root.find('.//{%s}calendar-home-set/{DAV:}href' % CALDAV_NS)
    if href_elem is not None and href_elem.text:
        return href_elem.text.strip()
    raise CalDAVError("Could not find calendar-home-set URL in response")


def _discover_calendars(home_url, auth):
    body = (
        '<?xml version="1.0"?>\n'
        '<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav" xmlns:cs="http://calendarserver.org/ns/">\n'
        '  <d:prop>\n'
        '    <d:displayname/>\n'
        '    <d:resourcetype/>\n'
        '    <cs:getctag/>\n'
        '  </d:prop>\n'
        '</d:propfind>'
    )
    headers = {'Content-Type': 'text/xml', 'Depth': '1'}
    try:
        resp = requests.request(
            'PROPFIND', home_url, headers=headers,
            data=body.encode('utf-8'), auth=auth, timeout=5
        )
    except requests.exceptions.RequestException as e:
        logger.error("Connection error in _discover_calendars: %s", e)
        raise ConnectionError(str(e))
    _check_response(resp)

    root = ET.fromstring(resp.content)
    calendars = []
    for response_elem in root.findall('.//{DAV:}response'):
        resourcetype = response_elem.find('.//{DAV:}resourcetype')
        if resourcetype is not None:
            calendar_elem = resourcetype.find('{%s}calendar' % CALDAV_NS)
            if calendar_elem is not None:
                displayname_elem = response_elem.find('.//{DAV:}displayname')
                href_elem = response_elem.find('.//{DAV:}href')
                if displayname_elem is not None and href_elem is not None:
                    name = displayname_elem.text
                    href = href_elem.text
                    if name and href:
                        calendars.append({"name": name.strip(), "href": href.strip()})
    return calendars


def _fetch_vtodos(calendar_url, auth):
    body = (
        '<?xml version="1.0"?>\n'
        '<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">\n'
        '  <d:prop>\n'
        '    <d:getetag/>\n'
        '    <c:calendar-data/>\n'
        '  </d:prop>\n'
        '  <c:filter>\n'
        '    <c:comp-filter name="VCALENDAR">\n'
        '      <c:comp-filter name="VTODO"/>\n'
        '    </c:comp-filter>\n'
        '  </c:filter>\n'
        '</c:calendar-query>'
    )
    headers = {'Content-Type': 'text/xml', 'Depth': '1'}
    try:
        resp = requests.request(
            'REPORT', calendar_url, headers=headers,
            data=body.encode('utf-8'), auth=auth, timeout=5
        )
    except requests.exceptions.RequestException as e:
        logger.error("Connection error in _fetch_vtodos: %s", e)
        raise ConnectionError(str(e))
    _check_response(resp)

    root = ET.fromstring(resp.content)
    vtodos = []
    for cal_data in root.findall('.//{%s}calendar-data' % CALDAV_NS):
        if cal_data.text:
            vtodos.append(cal_data.text)
    return vtodos


def _parse_vtodo(vtodo_text):
    lines = vtodo_text.replace('\r\n', '\n').split('\n')
    unfolded_lines = []
    for line in lines:
        if line.startswith(' ') or line.startswith('\t'):
            if unfolded_lines:
                unfolded_lines[-1] += line[1:]
        else:
            unfolded_lines.append(line)

    parsed = {
        'id': None,
        'title': None,
        'due_date': None,
        'status': None,
        'created_at': None,
        'updated_at': None
    }

    for line in unfolded_lines:
        if ':' not in line:
            continue
        key_part, value = line.split(':', 1)
        key_parts = key_part.split(';')
        key = key_parts[0]

        if key == 'UID':
            parsed['id'] = value
        elif key == 'SUMMARY':
            parsed['title'] = value
        elif key == 'STATUS':
            parsed['status'] = value
        elif key == 'CREATED':
            if len(value) >= 15:
                parsed['created_at'] = "%s-%s-%sT%s:%s:%s" % (
                    value[0:4], value[4:6], value[6:8],
                    value[9:11], value[11:13], value[13:15]
                )
                if value.endswith('Z'):
                    parsed['created_at'] += 'Z'
        elif key == 'LAST-MODIFIED':
            if len(value) >= 15:
                parsed['updated_at'] = "%s-%s-%sT%s:%s:%s" % (
                    value[0:4], value[4:6], value[6:8],
                    value[9:11], value[11:13], value[13:15]
                )
                if value.endswith('Z'):
                    parsed['updated_at'] += 'Z'
        elif key == 'DUE':
            if len(value) >= 8:
                parsed['due_date'] = "%s-%s-%s" % (value[0:4], value[4:6], value[6:8])

    if parsed['status'] == 'COMPLETED':
        return None

    if not parsed['title']:
        if parsed['id']:
            logger.warning("Skipping VTODO without SUMMARY: %s", parsed['id'])
        return None

    return {
        "id": parsed['id'],
        "title": parsed['title'],
        "due_date": parsed['due_date'],
        "created_at": parsed['created_at'],
        "updated_at": parsed['updated_at']
    }


def fetch_reminders(config):
    import os
    username = os.environ.get('ICLOUD_USERNAME')
    password = os.environ.get('ICLOUD_APP_PASSWORD')

    if not username or not password:
        logger.error("ICLOUD_USERNAME or ICLOUD_APP_PASSWORD not set in env")
        return []

    auth = HTTPBasicAuth(username, password)
    lists_to_fetch = config.get("reminders", {}).get("lists", [])

    base_url = "https://caldav.icloud.com"
    principal_path = _find_principal(base_url, auth)

    principal_url = base_url + principal_path if principal_path.startswith('/') else principal_path
    home_path = _find_calendar_home(principal_url, auth)

    home_url = base_url + home_path if home_path.startswith('/') else home_path
    calendars = _discover_calendars(home_url, auth)

    results = []
    for cal in calendars:
        if cal["name"] in lists_to_fetch:
            cal_url = base_url + cal["href"] if cal["href"].startswith('/') else cal["href"]
            vtodos = _fetch_vtodos(cal_url, auth)
            for vtodo_text in vtodos:
                try:
                    parsed = _parse_vtodo(vtodo_text)
                    if parsed:
                        parsed["source"] = "reminders"
                        parsed["list"] = cal["name"]
                        results.append(parsed)
                except Exception as e:
                    logger.warning("Failed to parse a VTODO item: %s", e)

    return results
