# Remote-Zugang für VPS (E9-3)

Optionale Wege, die Seiton-API auf einem **Linux-VPS** von außen erreichbar zu
machen — für **Telegram-Webhook** und ggf. REST. Die Web-UI ist ohne weitere
Konfiguration **localhost-only**; Admin-Zugriff läuft über SSH (oder ein
privates Netz).

> **UI-Auth (E23-1):** Mit gesetztem `UI_PASSWORD` in der `.env` verlangt die
> Web-UI einen Login (Session-Cookie, 7 Tage gültig) und darf dann auch remote
> erreichbar sein — **ausschließlich hinter TLS** (Caddy/nginx/Tunnel, s. u.).
> Der Setup-Wizard (`/setup`) bleibt immer localhost-only, weil er Secrets in
> die `.env` schreibt. Passwortwechsel meldet alle Sessions ab.

> **Proxy-sicherer Localhost-Guard (E27-1):** Der Guard erkennt Requests, die
> ein Reverse-Proxy weiterleitet (`X-Forwarded-For`/`X-Real-IP`/`Forwarded`),
> und lehnt sie **fail-closed** ab, wenn die Original-IP nicht localhost ist —
> `/setup` und `/docs` sind also auch dann dicht, wenn der Proxy „alles"
> weiterreicht. Zusätzlich blocken die Beispiel-Configs (`deploy/`) diese
> Pfade direkt im Proxy. Admin-Zugriff auf `/setup` vom Laptop: SSH-Tunnel
> (`ssh -L 8000:127.0.0.1:8000 user@vps`), dann `http://localhost:8000/setup`.

> **PWA (E23-2):** Ist die UI so erreichbar (HTTPS + Login), lässt sie sich am
> Handy/Desktop **installieren** („Zum Home-Bildschirm hinzufügen") — eigenes
> Icon, Vollbild ohne Browser-Chrome. Offline-Capture-Queue folgt mit E23-3.

> **Consumer / Heim-Box:** kein öffentlicher Zugang nötig — Long-Polling (E1-5),
> siehe [`packaging.md`](packaging.md). Diese Seite gilt für **VPS-Webhook**.
>
> **Stack deployen:** zuerst [`vps-deployment.md`](vps-deployment.md) (E20-2).

Die API lauscht nur auf `127.0.0.1:8000`. Von außen kommt Traffic nur über einen
TLS-fähigen Proxy oder Tunnel.

---

## Welche Variante?

| Situation | Empfehlung |
|-----------|------------|
| Eigene Domain, Port 443 offen | **Caddy** (Default in E20-2) |
| Du kennst nginx besser | **nginx** + Let's Encrypt (`certbot`) |
| Keine offenen Ports / keine Cert-Pflege | **Cloudflare Tunnel** |
| Nur Setup/Settings vom Laptop | **SSH-Tunnel** (kein öffentlicher UI-Zugang) |
| Privates Fernnetz (Heim + VPS) | **Tailscale** o. Ä. für UI/SSH; Webhook weiter per Caddy/Tunnel |

---

## A — Caddy (TLS + Reverse-Proxy)

Kurzfassung — Details in [`vps-deployment.md`](vps-deployment.md#4-tls-mit-caddy).

```bash
sudo apt install -y caddy
sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile
# Domain anpassen, dann:
sudo systemctl reload caddy
PUBLIC_URL=https://brain.deine-domain.tld ./scripts/register-telegram-webhook.sh
```

Beispiel: [`deploy/Caddyfile.example`](../deploy/Caddyfile.example).

---

## B — nginx + Let's Encrypt

Beispiel-Config: [`deploy/nginx-seiton.conf.example`](../deploy/nginx-seiton.conf.example).

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo cp deploy/nginx-seiton.conf.example /etc/nginx/sites-available/seiton
# server_name anpassen
sudo ln -sf /etc/nginx/sites-available/seiton /etc/nginx/sites-enabled/seiton
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d brain.deine-domain.tld
PUBLIC_URL=https://brain.deine-domain.tld ./scripts/register-telegram-webhook.sh
```

nginx terminiert TLS und proxyt nach `127.0.0.1:8000`. Port 8000 nicht
öffentlich freigeben.

---

## C — Cloudflare Tunnel

Stabiler öffentlicher HTTPS-Endpunkt **ohne** Port-Forwarding und ohne eigenes
Zertifikat auf dem VPS. Geeignet, wenn die Firewall nur SSH erlaubt.

Voraussetzungen: Cloudflare-Account, Domain bei Cloudflare (DNS),
[`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).

```bash
# Einmalig (lokal oder auf dem VPS, eingeloggt mit cloudflared)
cloudflared tunnel login
cloudflared tunnel create seiton-brain
cloudflared tunnel route dns seiton-brain brain.deine-domain.tld
```

Config-Beispiel: [`deploy/cloudflared-config.example.yml`](../deploy/cloudflared-config.example.yml)
— Tunnel-ID und Credentials-Pfad eintragen, dann:

```bash
# dauerhaft z. B. als systemd-Service (siehe Cloudflare-Doku)
cloudflared tunnel --config /etc/cloudflared/config.yml run
```

Webhook registrieren:

```bash
PUBLIC_URL=https://brain.deine-domain.tld ./scripts/register-telegram-webhook.sh
```

Für **lokale Entwicklung** (ngrok-Alternative) reicht oft:

```bash
cloudflared tunnel run --url http://localhost:8000 seiton-brain
```

Siehe auch [`setup.md`](setup.md) (Variante B).

---

## D — SSH-Tunnel (Web-UI / OpenAPI)

`/setup`, `/settings`, `/docs` sind nur von **localhost** erreichbar — absichtlich
(siehe [`SECURITY.md`](../SECURITY.md)).

Vom Laptop:

```bash
ssh -L 8000:127.0.0.1:8000 user@DEINE-VPS-IP
```

Browser: http://localhost:8000/setup

Kein Ersatz für den öffentlichen Webhook — nur für Admin/UI.

---

## E — Privates Netz (Tailscale o. Ä.)

Für Fernzugriff auf UI/SSH **ohne** die Web-UI öffentlich zu exposen:

1. Tailscale (oder vergleichbar) auf Laptop + VPS
2. Über die Tailscale-IP des VPS per SSH tunneln, oder
3. optional lokal `ssh -L …` gegen die Tailscale-IP

Telegram-Webhook braucht weiterhin eine **öffentliche HTTPS-URL** (Caddy, nginx
oder Cloudflare Tunnel). Tailscale ersetzt den Webhook nicht.

---

## Sicherheit (Kurz)

- API nur auf `127.0.0.1:8000` (Compose VPS-Profil)
- Öffentlich: nur Proxy/Tunnel mit TLS; Port 8000 geschlossen
- Web-UI nur mit gesetztem `UI_PASSWORD` **und** TLS ins Internet legen —
  sonst gar nicht
- `SEITON_API_KEY`, Telegram-Webhook-Secret, Firewall/SSH härten
- Details: [`SECURITY.md`](../SECURITY.md)

---

## Troubleshooting

| Problem | Prüfen |
|---------|--------|
| Telegram antwortet nicht | `getWebhookInfo`, Proxy-/Tunnel-Logs, `curl https://…/health` |
| 502 Bad Gateway | `curl http://127.0.0.1:8000/health` auf dem VPS |
| Certbot/Caddy TLS-Fehler | DNS A-Record, Port 80/443, Rate-Limits |
| Tunnel up, Webhook 401 | `TELEGRAM_WEBHOOK_SECRET` vs. `secret_token` bei `setWebhook` |
| Setup-UI von außen 403 | erwartet — SSH-Tunnel nutzen |

Mehr: [`troubleshooting.md`](troubleshooting.md), `./scripts/doctor.sh`.
