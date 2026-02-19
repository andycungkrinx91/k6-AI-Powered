import ipaddress
import os
import socket

import httpx


class UnsafeUrlError(ValueError):
    pass


def _is_ip_blocked(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)

    if addr.is_loopback or addr.is_private or addr.is_link_local:
        return True
    if addr.is_multicast or addr.is_reserved or addr.is_unspecified:
        return True
    return False


def _resolve_host(host: str) -> set[str]:
    out: set[str] = set()
    for family, _, _, _, sockaddr in socket.getaddrinfo(host, None):
        if family == socket.AF_INET:
            out.add(sockaddr[0])
        elif family == socket.AF_INET6:
            out.add(sockaddr[0])
    return out


def validate_target_url(raw: str) -> str:
    """Validate and normalize a user-provided target URL.

    Security goals:
    - only allow http/https
    - block private/loopback/link-local/reserved IPs (SSRF)
    - restrict ports by default (80/443)
    """

    if not raw or not isinstance(raw, str):
        raise UnsafeUrlError("missing url")

    url = raw.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"

    parsed = httpx.URL(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("unsupported scheme")
    if not parsed.host:
        raise UnsafeUrlError("missing host")

    allow_ports_env = os.getenv("ALLOWED_TARGET_PORTS", "80,443")
    allowed_ports = {int(p.strip()) for p in allow_ports_env.split(",") if p.strip().isdigit()}
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if allowed_ports and port not in allowed_ports:
        raise UnsafeUrlError("port not allowed")

    try:
        ips = _resolve_host(parsed.host)
    except Exception as exc:  # noqa: BLE001
        raise UnsafeUrlError(f"dns resolution failed: {exc}") from exc

    if not ips:
        raise UnsafeUrlError("dns resolution returned no addresses")
    if any(_is_ip_blocked(ip) for ip in ips):
        raise UnsafeUrlError("host resolves to a blocked network")

    # Return normalized string (keeps path/query)
    return str(parsed)
