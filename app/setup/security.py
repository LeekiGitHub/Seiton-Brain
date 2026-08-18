"""Zugriffsschutz fuer Setup/UI/OpenAPI — nur localhost, proxy-sicher (E27-1).

Hinter einem lokalen Reverse-Proxy (Caddy/nginx auf derselben Maschine) ist
``request.client.host`` fuer **jeden** Request ``127.0.0.1`` — die Peer-IP
allein reicht als Localhost-Nachweis also nicht. Deshalb werden zusaetzlich
die von Proxies gesetzten Forwarded-Header ausgewertet, **fail-closed**:
Sobald ein solcher Header vorhanden ist, muessen *alle* darin gemeldeten
Client-IPs ebenfalls localhost sein, sonst wird der Zugriff verweigert.
Direkte lokale Zugriffe (curl/Browser ohne Proxy) senden keine solchen
Header und bleiben unveraendert erlaubt.
"""

import re

from fastapi import HTTPException, Request

_LOCALHOST_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "testclient"})

# RFC 7239 ``Forwarded: for=1.2.3.4;proto=https, for="[::1]:4711"``
_FORWARDED_FOR_RE = re.compile(r"for=([^;,\s]+)", re.IGNORECASE)


def _normalize_host(token: str) -> str:
    """Bereinigt Header-Tokens: Quotes, Brackets, Port-Suffixe."""
    host = token.strip().strip('"').lower()
    if host.startswith("["):
        # IPv6 in Brackets, optional mit Port: [::1]:4711
        host = host[1:].split("]", 1)[0]
    elif host.count(":") == 1:
        # IPv4 mit Port: 1.2.3.4:5678 (":"-reiche IPv6-Adressen unberuehrt)
        candidate, _, port = host.partition(":")
        if port.isdigit():
            host = candidate
    return host


def is_localhost_host(host: str) -> bool:
    return _normalize_host(host) in _LOCALHOST_HOSTS


def _forwarded_client_hosts(request: Request) -> list[str]:
    """Alle Client-IPs, die Reverse-Proxies per Header durchreichen."""
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
        # Fail-closed: ein Forwarded-Header ohne auswertbares for= laesst
        # sich nicht verifizieren → als nicht-localhost behandeln.
        hosts.extend(matches or ["unknown"])
    return hosts


def is_local_request(request: Request) -> bool:
    """Ob der Request nachweislich von localhost kommt (proxy-sicher)."""
    host = request.client.host if request.client else ""
    if not is_localhost_host(host):
        return False
    return all(is_localhost_host(h) for h in _forwarded_client_hosts(request))


def require_localhost(request: Request) -> None:
    """Guard fuer Setup-/UI-Endpunkte ohne eigene Auth — nur localhost."""
    if not is_local_request(request):
        raise HTTPException(
            status_code=403,
            detail="Setup ist nur von localhost erreichbar.",
        )
