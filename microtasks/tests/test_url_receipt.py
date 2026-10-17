import unittest
from email.message import Message
from unittest.mock import patch

from url_receipt import fetch_receipt, validate_public_https_url


PUBLIC_DNS = [(2, 1, 6, "", ("93.184.216.34", 443))]


class FakeResponse:
    status = 200

    def __init__(self, body: bytes):
        self._body = body
        self.headers = Message()
        self.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.headers["ETag"] = '"sample-etag"'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit: int) -> bytes:
        return self._body

    def geturl(self) -> str:
        return "https://example.com/final"


class FakeOpener:
    def __init__(self, response: FakeResponse):
        self.response = response

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


class UrlReceiptTests(unittest.TestCase):
    def test_rejects_non_https_and_embedded_credentials(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate_public_https_url("http://example.com")
        with self.assertRaisesRegex(ValueError, "credentials"):
            validate_public_https_url("https://user:pass@example.com/")

    @patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))])
    def test_rejects_non_public_resolution(self, _getaddrinfo):
        with self.assertRaisesRegex(ValueError, "non-public"):
            validate_public_https_url("https://example.com/")

    @patch("socket.getaddrinfo", return_value=PUBLIC_DNS)
    @patch("urllib.request.build_opener")
    def test_emits_reproducible_full_body_hash(self, build_opener, _getaddrinfo):
        opener = FakeOpener(FakeResponse(b"hello world"))
        build_opener.return_value = opener

        result = fetch_receipt("https://example.com/start", timeout=2)

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["final_url"], "https://example.com/final")
        self.assertEqual(
            result["sha256"],
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
        )
        self.assertEqual(result["hash_scope"], "full_response")
        self.assertEqual(result["etag"], '"sample-etag"')
        self.assertNotIn("Authorization", opener.request.headers)


if __name__ == "__main__":
    unittest.main()
