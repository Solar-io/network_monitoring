## Create a manage.sh script to capture the long running processes (EXAMPLE BELOW)

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

usage() {
  cat <<USAGE
Usage: scripts/manage.sh <command>

Commands:
  build     Build Docker images via docker-compose
  start     Start orchestrator and bot (docker-compose up -d)
  stop      Stop services (docker-compose down)
  status    Show container status (docker-compose ps)
  logs      Tail orchestrator and bot logs
  dev       Run orchestrator (npm dev) and bot (python) locally
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

cmd=$1
shift || true

case "$cmd" in
  build)
    docker-compose -f "$COMPOSE_FILE" build "$@"
    ;;
  start)
    docker-compose -f "$COMPOSE_FILE" up -d "$@"
    ;;
  stop)
    docker-compose -f "$COMPOSE_FILE" down "$@"
    ;;
  status)
    docker-compose -f "$COMPOSE_FILE" ps "$@"
    ;;
  logs)
    docker-compose -f "$COMPOSE_FILE" logs -f "$@"
    ;;
  dev)
    (cd "$ROOT_DIR/orchestrator" && npm install && npm run dev) &
    ORCH_PID=$!
    sleep 2
    python -m venv "$ROOT_DIR/.venv"
    source "$ROOT_DIR/.venv/bin/activate"
    pip install -r "$ROOT_DIR/bot/requirements.txt"
    python "$ROOT_DIR/bot/main.py"
    wait $ORCH_PID
    ;;
  *)
    usage
    exit 1
    ;;
esac