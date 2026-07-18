"""HTTP client with SSRF guards."""

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from app.config import get_settings


class SSRFError(ValueError):
    pass


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
    )


def validate_url(url: str, *, allow_private: bool | None = None) -> str:
    settings = get_settings()
    if allow_private is None:
        allow_private = settings.allow_private_networks

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFError(f"Unsupported URL scheme: {parsed.scheme}")
    if not parsed.hostname:
        raise SSRFError("URL must include a hostname")

    hostname = parsed.hostname.lower()
    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if not allow_private and hostname in blocked_hosts:
        raise SSRFError(f"Blocked hostname: {hostname}")

    if not allow_private:
        try:
            addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        except socket.gaierror as exc:
            raise SSRFError(f"Cannot resolve hostname: {hostname}") from exc

        for info in addr_info:
            ip = info[4][0]
            if _is_private_ip(ip):
                raise SSRFError(f"Blocked private/reserved IP: {ip}")

    return url


async def fetch_url(url: str, *, allow_private: bool | None = None) -> tuple[str, str]:
    """Fetch URL and return (final_url, text body)."""
    settings = get_settings()
    safe_url = validate_url(url, allow_private=allow_private)

    async with httpx.AsyncClient(
        timeout=settings.http_timeout_seconds,
        follow_redirects=True,
        max_redirects=settings.http_max_redirects,
        headers={"User-Agent": "JobPosting/1.0 (+https://github.com/jobposting)"},
    ) as client:
        response = await client.get(safe_url)
        response.raise_for_status()
        return str(response.url), response.text
