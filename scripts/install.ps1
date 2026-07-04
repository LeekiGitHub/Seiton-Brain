# Consumer-Installer fuer Seiton Brain (E20-1) — Windows (PowerShell).
#
# Voraussetzung: Docker Desktop laeuft.
# Aufruf (im Repo-Root, PowerShell):
#   .\scripts\install.ps1
# Optional:
#   $env:VAULT_DIR = "C:\Users\Du\SeitonBrain\vault"; .\scripts\install.ps1

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$VaultDir = if ($env:VAULT_DIR) { $env:VAULT_DIR } else { Join-Path $Root "vault" }
$SetupUrl = "http://localhost:8000/setup"
$ComposeArgs = @("-f", "docker-compose.yml", "-f", "docker-compose.consumer.yml", "--profile", "polling")

function Write-Info($msg) { Write-Host "==> $msg" }

function Test-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker ist nicht installiert. https://docs.docker.com/desktop/setup/install/windows-install/"
    }
    docker compose version | Out-Null
    docker info | Out-Null
}

function Set-EnvVar($key, $value) {
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
    }
    $lines = Get-Content ".env"
    $found = $false
    $newLines = foreach ($line in $lines) {
        if ($line -match "^$key=") {
            $found = $true
            "$key=$value"
        } else {
            $line
        }
    }
    if (-not $found) {
        $newLines += "$key=$value"
    }
    $newLines | Set-Content ".env" -Encoding UTF8
}

function Ensure-Vault {
    New-Item -ItemType Directory -Force -Path $VaultDir | Out-Null
    $example = Join-Path $Root "vault.example"
    if ((Test-Path $example) -and -not (Get-ChildItem $VaultDir -ErrorAction SilentlyContinue)) {
        Write-Info "Initialisiere Vault aus vault.example/"
        Copy-Item -Path (Join-Path $example "*") -Destination $VaultDir -Recurse -Force
    }
}

function Start-Stack {
    Write-Info "Starte Seiton Brain (Consumer-Modus, Telegram Long-Polling)"
    docker compose @ComposeArgs up -d --build
}

function Invoke-Migrations {
    Write-Info "Fuehre Datenbank-Migrationen aus"
    docker compose @ComposeArgs run --rm api alembic upgrade head
}

function Wait-Health {
    Write-Info "Warte auf API-Healthcheck"
    for ($i = 0; $i -lt 45; $i++) {
        try {
            Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
            return
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    Write-Warning "Healthcheck-Timeout — pruefe: docker compose logs api"
}

Write-Info "Seiton Brain — Consumer-Installation"
Test-Docker
Ensure-Vault
$absVault = (Resolve-Path $VaultDir).Path
Set-EnvVar "OBSIDIAN_VAULT_HOST_PATH" $absVault
Set-EnvVar "OBSIDIAN_VAULT_PATH" "/vault"
Start-Stack
Invoke-Migrations
Wait-Health
Start-Process $SetupUrl

Write-Host @"

Seiton Brain laeuft.

  Setup-Wizard:  $SetupUrl
  Dashboard:     http://localhost:8000/dashboard
  Status pruefen: .\scripts\doctor.ps1

Deine API-Keys bleiben lokal in der .env — nichts wird an uns gesendet.

"@
