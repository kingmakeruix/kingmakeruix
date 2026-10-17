#!/usr/bin/env python3
"""Perform read-only HTTPS GET probes and emit reproducible JSON evidence."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse


USER_AGENT = "Nodo131-ReadOnly-Probe/1.0"


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("only absolute HTTPS URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("credentials in URLs are not allowed")


def _decode_json(body: bytes, charset: str | None) -> bool:
    encoding = charset or "utf-8"
    try:
        json.loads(body.decode(encoding))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return True


def probe_url(url: str, timeout: float = 10.0) -> dict[str, Any]:
    validate_url(url)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, */*;q=0.5"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(1_000_001)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset()
            return {
                "url": url,
                "final_url": response.geturl(),
                "status": response.status,
                "elapsed_ms": elapsed_ms,
                "content_type": content_type,
                "bytes_read": min(len(body), 1_000_000),
                "truncated": len(body) > 1_000_000,
                "json_valid": _decode_json(body[:1_000_000], charset),
                "error": None,
            }
    except urllib.error.HTTPError as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "url": url,
            "final_url": error.geturl(),
            "status": error.code,
            "elapsed_ms": elapsed_ms,
            "content_type": error.headers.get_content_type(),
            "bytes_read": 0,
            "truncated": False,
            "json_valid": False,
            "error": f"HTTP {error.code}",
        }
    except urllib.error.URLError as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "url": url,
            "final_url": None,
            "status": None,
            "elapsed_ms": elapsed_ms,
            "content_type": None,
            "bytes_read": 0,
            "truncated": False,
            "json_valid": False,
            "error": str(error.reason),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="One to five public HTTPS URLs")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    if not 1 <= len(args.urls) <= 5:
        parser.error("provide between one and five URLs")
    if not 0 < args.timeout <= 30:
        parser.error("timeout must be greater than 0 and at most 30 seconds")

    checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results = [probe_url(url, args.timeout) for url in args.urls]
    print(json.dumps({"checked_at": checked_at, "results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
