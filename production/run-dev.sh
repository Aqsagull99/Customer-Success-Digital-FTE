#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

log() {
  printf '[run-dev] %s\n' "$*"
}

docker_available() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

start_local_backend() {
  log "Starting local backend (KAFKA_REQUIRED=false) ..."

  if [[ ! -d ".venv" ]]; then
    log "Creating virtualenv ..."
    python3 -m venv .venv
  fi

  # shellcheck disable=SC1091
  source .venv/bin/activate

  if ! python -c "import uvicorn" >/dev/null 2>&1; then
    log "Installing Python dependencies ..."
    pip install -r requirements.txt
  fi

  log "Backend URL: http://localhost:8000"
  exec env KAFKA_REQUIRED=false python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
}

if docker_available; then
  log "Docker detected. Starting postgres + kafka + api containers ..."

  # Start core services first
  docker compose up -d postgres kafka

  # Start API without waiting for kafka health checks
  docker compose up -d --no-deps api || true

  # Quick status output
  docker compose ps
  log "Backend URL: http://localhost:8000"
  log "If API is not up yet, check logs: docker compose logs -f api kafka postgres"
  exit 0
fi

log "Docker not available/reachable in this shell. Falling back to local mode."
start_local_backend
