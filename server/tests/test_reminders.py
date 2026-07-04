import unittest
from unittest.mock import patch, Mock
from src.connectors.reminders import _parse_vtodo, _discover_calendars


class TestReminders(unittest.TestCase):

    def test_parse_vtodo_with_due(self):
        vtodo = (
            "BEGIN:VTODO\n"
            "UID:12345\n"
            "SUMMARY:Buy milk\n"
            "DUE;VALUE=DATE:20260620\n"
            "STATUS:NEEDS-ACTION\n"
            "CREATED:20260615T100000Z\n"
            "LAST-MODIFIED:20260618T083000Z\n"
            "END:VTODO"
        )
        parsed = _parse_vtodo(vtodo)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['id'], '12345')
        self.assertEqual(parsed['title'], 'Buy milk')
        self.assertEqual(parsed['due_date'], '2026-06-20')
        self.assertEqual(parsed['created_at'], '2026-06-15T10:00:00Z')
        self.assertEqual(parsed['updated_at'], '2026-06-18T08:30:00Z')

    def test_parse_vtodo_without_due(self):
        vtodo = (
            "BEGIN:VTODO\n"
            "UID:12345\n"
            "SUMMARY:Buy milk\n"
            "STATUS:NEEDS-ACTION\n"
            "CREATED:20260615T100000Z\n"
            "LAST-MODIFIED:20260618T083000Z\n"
            "END:VTODO"
        )
        parsed = _parse_vtodo(vtodo)
        self.assertIsNotNone(parsed)
        self.assertIsNone(parsed['due_date'])

    def test_parse_vtodo_completed(self):
        vtodo = (
            "BEGIN:VTODO\n"
            "UID:12345\n"
            "SUMMARY:Buy milk\n"
            "STATUS:COMPLETED\n"
            "END:VTODO"
        )
        parsed = _parse_vtodo(vtodo)
        self.assertIsNone(parsed)

    def test_parse_vtodo_unfolded_lines(self):
        vtodo = (
            "BEGIN:VTODO\n"
            "UID:12345\n"
            "SUMMARY:Buy \n"
            " milk\n"
            "STATUS:NEEDS-ACTION\n"
            "END:VTODO"
        )
        parsed = _parse_vtodo(vtodo)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['title'], 'Buy milk')

    def test_parse_vtodo_no_summary(self):
        vtodo = (
            "BEGIN:VTODO\n"
            "UID:12345\n"
            "STATUS:NEEDS-ACTION\n"
            "END:VTODO"
        )
        parsed = _parse_vtodo(vtodo)
        self.assertIsNone(parsed)

    @patch('src.connectors.reminders.requests.request')
    def test_discover_calendars(self, mock_request):
        xml_resp = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<d:multistatus xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav" '
            'xmlns:cs="http://calendarserver.org/ns/">\n'
            '  <d:response>\n'
            '    <d:href>/123/calendars/A/</d:href>\n'
            '    <d:propstat>\n'
            '      <d:prop>\n'
            '        <d:displayname>Inbox</d:displayname>\n'
            '        <d:resourcetype>\n'
            '          <d:collection/>\n'
            '          <c:calendar/>\n'
            '        </d:resourcetype>\n'
            '      </d:prop>\n'
            '      <d:status>HTTP/1.1 200 OK</d:status>\n'
            '    </d:propstat>\n'
            '  </d:response>\n'
            '  <d:response>\n'
            '    <d:href>/123/calendars/B/</d:href>\n'
            '    <d:propstat>\n'
            '      <d:prop>\n'
            '        <d:displayname>Not a calendar</d:displayname>\n'
            '        <d:resourcetype>\n'
            '          <d:collection/>\n'
            '        </d:resourcetype>\n'
            '      </d:prop>\n'
            '      <d:status>HTTP/1.1 200 OK</d:status>\n'
            '    </d:propstat>\n'
            '  </d:response>\n'
            '</d:multistatus>'
        )
        mock_response = Mock()
        mock_response.status_code = 207
        mock_response.content = xml_resp.encode('utf-8')
        mock_request.return_value = mock_response

        calendars = _discover_calendars("https://home", ("user", "pass"))
        self.assertEqual(len(calendars), 1)
        self.assertEqual(calendars[0]["name"], "Inbox")
        self.assertEqual(calendars[0]["href"], "/123/calendars/A/")


if __name__ == '__main__':
    unittest.main()
