# Gemeinsame Init-Hilfen (E16-1) — von init.sh und install.sh genutzt.

set_env_var() {
  local key="$1"
  local value="$2"
  local tmp
  tmp="$(mktemp)"
  if [[ -f .env ]] && grep -q "^${key}=" .env; then
    awk -v k="$key" -v v="$value" '
      BEGIN { done = 0 }
      $0 ~ "^" k "=" { print k "=" v; done = 1; next }
      { print }
      END { if (!done) print k "=" v }
    ' .env >"$tmp"
    mv "$tmp" .env
  else
    printf '%s=%s\n' "$key" "$value" >>.env
  fi
}

ensure_env_from_example() {
  if [[ ! -f .env ]]; then
    if [[ ! -f .env.example ]]; then
      printf 'Fehler: .env.example fehlt\n' >&2
      return 1
    fi
    cp .env.example .env
    return 0
  fi
  return 0
}

ensure_vault_dir() {
  local vault_dir="$1"
  mkdir -p "$vault_dir"
  if [[ -d vault.example ]] && [[ -z "$(ls -A "$vault_dir" 2>/dev/null || true)" ]]; then
    cp -R vault.example/. "$vault_dir/"
    return 0
  fi
  return 0
}

configure_vault_env() {
  local vault_dir="$1"
  local abs_vault
  abs_vault="$(cd "$vault_dir" && pwd)"
  set_env_var "OBSIDIAN_VAULT_HOST_PATH" "$abs_vault"
  set_env_var "OBSIDIAN_VAULT_PATH" "/vault"
}

docker_install_hint() {
  case "$(uname -s)" in
    Darwin) echo "https://docs.docker.com/desktop/setup/install/mac-install/" ;;
    Linux) echo "https://docs.docker.com/engine/install/" ;;
    *) echo "https://docs.docker.com/get-docker/" ;;
  esac
}

print_docker_status() {
  if ! command -v docker >/dev/null 2>&1; then
    printf '  [??] Docker nicht installiert — %s\n' "$(docker_install_hint)"
    return
  fi
  if docker info >/dev/null 2>&1; then
    printf '  [ok] Docker laeuft\n'
  else
    printf '  [??] Docker installiert, Daemon gestoppt — starte Docker Desktop / dockerd\n'
  fi
  if docker compose version >/dev/null 2>&1; then
    printf '  [ok] Docker Compose verfuegbar\n'
  else
    printf '  [??] Docker Compose (Plugin) fehlt\n'
  fi
}
