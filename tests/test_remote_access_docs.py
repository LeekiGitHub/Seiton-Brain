"""Tests fuer Remote-Zugang-Doku und Proxy-Beispiele (E9-3)."""

from pathlib import Path

REMOTE = Path("docs/remote-access.md")
DEPLOY = Path("deploy")


def test_remote_access_doc_exists():
    assert REMOTE.is_file()
    text = REMOTE.read_text(encoding="utf-8")
    for needle in (
        "E9-3",
        "Caddy",
        "nginx",
        "Cloudflare Tunnel",
        "SSH-Tunnel",
        "Tailscale",
        "vps-deployment.md",
        "127.0.0.1:8000",
    ):
        assert needle in text, f"missing in remote-access.md: {needle}"


def test_proxy_example_configs_exist():
    caddy = DEPLOY / "Caddyfile.example"
    nginx = DEPLOY / "nginx-seiton.conf.example"
    tunnel = DEPLOY / "cloudflared-config.example.yml"
    assert caddy.is_file()
    assert "reverse_proxy" in caddy.read_text(encoding="utf-8")
    assert nginx.is_file()
    nginx_text = nginx.read_text(encoding="utf-8")
    assert "proxy_pass http://127.0.0.1:8000" in nginx_text
    assert tunnel.is_file()
    tunnel_text = tunnel.read_text(encoding="utf-8")
    assert "127.0.0.1:8000" in tunnel_text
    assert "ingress:" in tunnel_text


def test_self_hosting_links_remote_access():
    text = Path("docs/self-hosting.md").read_text(encoding="utf-8")
    assert "remote-access.md" in text


def test_vps_deployment_links_remote_access():
    text = Path("docs/vps-deployment.md").read_text(encoding="utf-8")
    assert "remote-access.md" in text
