"""Access guard for setup/UI/OpenAPI — localhost only, proxy-safe (E27-1).

Behind a local reverse proxy (Caddy/nginx on the same machine),
``request.client.host`` is ``127.0.0.1`` for **every** request — the peer IP
alone is therefore not enough as a localhost proof. Forwarded headers set by
proxies are evaluated as well, **fail-closed**: once such a header is present,
*all* client IPs reported in it must also be localhost, otherwise access is
denied. Direct local access (curl/browser without proxy) sends no such
headers and remains allowed unchanged.
"""

import re

from fastapi import HTTPException, Request

_LOCALHOST_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "testclient"})

# RFC 7239 ``Forwarded: for=1.2.3.4;proto=https, for="[::1]:4711"``
_FORWARDED_FOR_RE = re.compile(r"for=([^;,\s]+)", re.IGNORECASE)


def _normalize_host(token: str) -> str:
    """Normalize header tokens: quotes, brackets, port suffixes."""
    host = token.strip().strip('"').lower()
    if host.startswith("["):
        # IPv6 in brackets, optional port: [::1]:4711
        host = host[1:].split("]", 1)[0]
    elif host.count(":") == 1:
        # IPv4 with port: 1.2.3.4:5678 (leave colon-rich IPv6 alone)
        candidate, _, port = host.partition(":")
        if port.isdigit():
            host = candidate
    return host


def is_localhost_host(host: str) -> bool:
    return _normalize_host(host) in _LOCALHOST_HOSTS


def _forwarded_client_hosts(request: Request) -> list[str]:
    """All client IPs that reverse proxies forward via headers."""
    hosts: list[str] = []
    xff = request.headers.get("x-forwarded-for")
    if xff:
        hosts.extend(xff.split(","))
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        hosts.append(real_ip)
    forwarded = request.headers.get("forwarded")
    if forwarded:
        matches = _FORWARDED_FOR_RE.findall(forwarded)
        # Fail-closed: a Forwarded header without a parseable for=
        # cannot be verified → treat as non-localhost.
        hosts.extend(matches or ["unknown"])
    return hosts


def is_local_request(request: Request) -> bool:
    """Whether the request is verifiably from localhost (proxy-safe)."""
    host = request.client.host if request.client else ""
    if not is_localhost_host(host):
        return False
    return all(is_localhost_host(h) for h in _forwarded_client_hosts(request))


def require_localhost(request: Request) -> None:
    """Guard for setup/UI endpoints without their own auth — localhost only."""
    if not is_local_request(request):
        raise HTTPException(
            status_code=403,
            detail="Setup ist nur von localhost erreichbar.",
        )
