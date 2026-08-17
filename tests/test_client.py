import unittest
from unittest.mock import Mock, patch

from notion_automation.client import NotionAPIError, NotionClient


class ClientTests(unittest.TestCase):
    def test_paginates_data_source_query(self):
        session = Mock()
        first = Mock(ok=True, status_code=200, headers={})
        first.json.return_value = {"results": [{"id": "one"}], "has_more": True, "next_cursor": "next"}
        second = Mock(ok=True, status_code=200, headers={})
        second.json.return_value = {"results": [{"id": "two"}], "has_more": False, "next_cursor": None}
        session.request.side_effect = [first, second]
        client = NotionClient("fake-token", session=session)
        self.assertEqual([x["id"] for x in client.query_data_source("fake-source")], ["one", "two"])
        self.assertEqual(session.request.call_count, 2)

    @patch("notion_automation.client.time.sleep", return_value=None)
    def test_retries_rate_limit(self, _sleep):
        session = Mock()
        limited = Mock(ok=False, status_code=429, headers={"Retry-After": "0"})
        limited.json.return_value = {"message": "rate limited"}
        success = Mock(ok=True, status_code=200, headers={})
        success.json.return_value = {"results": [], "has_more": False}
        session.request.side_effect = [limited, success]
        client = NotionClient("fake-token", session=session)
        self.assertEqual(client.query_data_source("fake-source"), [])

    def test_invalid_json_is_reported(self):
        session = Mock()
        response = Mock(ok=True, status_code=200, headers={})
        response.json.side_effect = ValueError("bad json")
        session.request.return_value = response
        with self.assertRaises(NotionAPIError):
            NotionClient("fake-token", session=session).query_data_source("fake-source")


if __name__ == "__main__":
    unittest.main()
