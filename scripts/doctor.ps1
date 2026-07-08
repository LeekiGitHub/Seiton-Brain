# Diagnose fuer lokale Seiton-Brain-Installation (E20-1) — Windows.
# Aufruf: .\scripts\doctor.ps1

$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$ComposeArgs = @("-f", "docker-compose.yml", "-f", "docker-compose.consumer.yml")
$Errors = 0

function Write-Ok($msg) { Write-Host "  [ok] $msg" }
function Write-Fail($msg) { Write-Host "  [!!] $msg" -ForegroundColor Red; $script:Errors++ }
function Write-Warn($msg) { Write-Host "  [??] $msg" -ForegroundColor Yellow }

function Get-EnvVar($key) {
    if (-not (Test-Path ".env")) { return $null }
    $line = Select-String -Path ".env" -Pattern "^$key=" | Select-Object -Last 1
    if (-not $line) { return $null }
    return ($line.Line -replace "^$key=", "").Trim('"', "'")
}

Write-Host "Seiton Brain Doctor`n"

try {
    docker info | Out-Null
    Write-Ok "Docker laeuft"
} catch {
    Write-Fail "Docker nicht verfuegbar oder Daemon gestoppt"
}

if (Test-Path ".env") {
    Write-Ok ".env vorhanden"
} else {
    Write-Fail ".env fehlt — .\scripts\install.ps1 oder .env.example kopieren"
}

$vault = Get-EnvVar "OBSIDIAN_VAULT_HOST_PATH"
if ($vault -and (Test-Path $vault)) {
    Write-Ok "Vault-Pfad vorhanden: $vault"
} else {
    Write-Fail "Vault-Pfad fehlt oder ungueltig: $vault"
}

try {
    $running = docker compose @ComposeArgs ps --status running --services 2>$null
    foreach ($svc in @("api", "worker", "db", "redis")) {
        if ($running -match "^$svc$") {
            Write-Ok "Service '$svc' laeuft"
        } else {
            Write-Fail "Service '$svc' laeuft nicht"
        }
    }
    if ($running -match "^poller$") {
        Write-Ok "Telegram Poller laeuft (Long-Polling)"
    } else {
        Write-Warn "Telegram Poller laeuft nicht — optional: --profile polling"
    }
} catch {
    Write-Warn "Compose-Status konnte nicht gelesen werden"
}

try {
    Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3 | Out-Null
    Write-Ok "API /health erreichbar"
} catch {
    Write-Fail "API /health nicht erreichbar (Port 8000)"
}

Write-Host ""
if ($Errors -gt 0) {
    Write-Host "$Errors harte(r) Fehler — siehe Hinweise oben."
    Write-Host "Hilfe: docs/self-hosting.md"
    exit 1
}
Write-Host "Alles ok."
Write-Host "Doku: docs/self-hosting.md"
