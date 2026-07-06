# Gemeinsame Deploy-Hilfen (E20-1/2/4) — von install, doctor, update genutzt.

read_env_var() {
  local key="$1"
  if [[ ! -f .env ]]; then
    return 1
  fi
  grep -E "^${key}=" .env | tail -1 | cut -d= -f2- | sed 's/^["'\''"]//; s/["'\''"]$//'
}

resolve_deploy_mode() {
  local mode="${SEITON_DEPLOY_MODE:-}"
  if [[ -z "$mode" ]]; then
    mode="$(read_env_var SEITON_DEPLOY_MODE 2>/dev/null || true)"
  fi
  printf '%s' "${mode:-consumer}"
}

# Setzt COMPOSE_FILES und COMPOSE_PROFILE (Array) fuer den aktuellen Modus.
load_compose_config() {
  local mode="${1:-$(resolve_deploy_mode)}"
  if [[ "$mode" == "vps" ]]; then
    COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.vps.yml)
    COMPOSE_PROFILE=()
  else
    COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.consumer.yml)
    COMPOSE_PROFILE=(--profile polling)
  fi
}

compose_cmd() {
  if ((${#COMPOSE_PROFILE[@]})); then
    docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" "$@"
  else
    docker compose "${COMPOSE_FILES[@]}" "$@"
  fi
}
