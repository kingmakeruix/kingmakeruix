#!/usr/bin/env python3
"""Fetch one public HTTPS URL and emit a content-fingerprint receipt."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import socket
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urljoin, urlparse


USER_AGENT = "Nodo131-Public-URL-Receipt/1.0"
MAX_BYTES = 1_000_000


def validate_public_https_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("only absolute HTTPS URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("credentials in URLs are not allowed")

    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    except socket.gaierror as error:
        raise ValueError(f"hostname did not resolve: {error}") from error

    resolved = {item[4][0].split("%", 1)[0] for item in addresses}
    if not resolved:
        raise ValueError("hostname did not resolve")
    if any(not ipaddress.ip_address(address).is_global for address in resolved):
        raise ValueError("URL resolves to a non-public address")


class PublicHttpsRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects that leave HTTPS or resolve to a non-public address."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        target = urljoin(req.full_url, newurl)
        validate_public_https_url(target)
        return super().redirect_request(req, fp, code, msg, headers, target)


def fetch_receipt(url: str, timeout: float = 10.0) -> dict[str, Any]:
    validate_public_https_url(url)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    opener = urllib.request.build_opener(PublicHttpsRedirectHandler())
    started = time.perf_counter()
    with opener.open(request, timeout=timeout) as response:
        body = response.read(MAX_BYTES + 1)
        captured = body[:MAX_BYTES]
        truncated = len(body) > MAX_BYTES
        return {
            "requested_url": url,
            "final_url": response.geturl(),
            "status": response.status,
            "content_type": response.headers.get_content_type(),
            "content_length_header": response.headers.get("Content-Length"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "bytes_hashed": len(captured),
            "truncated": truncated,
            "hash_scope": "first_1000000_bytes" if truncated else "full_response",
            "sha256": hashlib.sha256(captured).hexdigest(),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="One public HTTPS URL")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    if not 0 < args.timeout <= 30:
        parser.error("timeout must be greater than 0 and at most 30 seconds")

    try:
        receipt = fetch_receipt(args.url, args.timeout)
    except (ValueError, urllib.error.URLError) as error:
        parser.error(str(error))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
