import unittest
from email.message import Message
from unittest.mock import patch

from api_probe import probe_url, validate_url


class FakeResponse:
    status = 200

    def __init__(self, body: bytes, url: str = "https://example.com/status"):
        self._body = body
        self._url = url
        self.headers = Message()
        self.headers["Content-Type"] = "application/json; charset=utf-8"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit: int) -> bytes:
        return self._body

    def geturl(self) -> str:
        return self._url


class ApiProbeTests(unittest.TestCase):
    def test_rejects_non_https_and_embedded_credentials(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate_url("http://example.com")
        with self.assertRaisesRegex(ValueError, "credentials"):
            validate_url("https://user:pass@example.com/status")

    @patch("urllib.request.urlopen")
    def test_reports_valid_json_without_network(self, urlopen):
        urlopen.return_value = FakeResponse(b'{"ok": true}')

        result = probe_url("https://example.com/status", timeout=1)

        self.assertEqual(result["status"], 200)
        self.assertTrue(result["json_valid"])
        self.assertEqual(result["content_type"], "application/json")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertNotIn("Authorization", request.headers)


if __name__ == "__main__":
    unittest.main()
