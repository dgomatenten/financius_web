#!/usr/bin/env bash
# Start the Django backend + Postgres via Docker Compose.
# Usage:
#   ./scripts/dev.sh           — start (detached)
#   ./scripts/dev.sh stop      — stop containers
#   ./scripts/dev.sh logs      — tail all logs
#   ./scripts/dev.sh restart   — stop then start
#   ./scripts/dev.sh status    — show container state
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/infra/compose/docker-compose.yml"
COMPOSE="docker compose -f $COMPOSE_FILE"

_start() {
    echo "==> Building images (if changed)..."
    $COMPOSE build --quiet

    echo "==> Starting db + backend..."
    $COMPOSE up -d

    echo ""
    echo "==> Waiting for backend to be ready..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8001/api/v1/health/ >/dev/null 2>&1; then
            echo ""
            echo "✓  Backend is up:  http://localhost:8001"
            echo "   Health:         http://localhost:8001/api/v1/health/"
            echo "   Postgres port:  localhost:5433"
            echo ""
            echo "   Logs: ./scripts/dev.sh logs"
            echo "   Stop: ./scripts/dev.sh stop"
            exit 0
        fi
        printf "."
        sleep 2
    done
    echo ""
    echo "ERROR: backend did not respond within 60 seconds."
    $COMPOSE logs --tail=30
    exit 1
}

_stop() {
    echo "==> Stopping containers..."
    $COMPOSE down
    echo "Stopped."
}

_logs() {
    $COMPOSE logs -f
}

_status() {
    $COMPOSE ps
}

case "${1:-start}" in
    start)   _start ;;
    stop)    _stop ;;
    logs)    _logs ;;
    restart) _stop; _start ;;
    status)  _status ;;
    *)
        echo "Usage: $0 [start|stop|logs|restart|status]"
        exit 1
        ;;
esac
