#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
DOCKER_COMPOSE_FILE="$ROOT_DIR/infra/compose/docker-compose.yml"

# Load .env if it exists to pick up BACKEND_PORT
if [[ -f "$ROOT_DIR/.env" ]]; then
  set +o allexport
  source "$ROOT_DIR/.env" 2>/dev/null || true
  set -o allexport
fi

BACKEND_PORT="${BACKEND_PORT:-5000}"

mkdir -p "$RUN_DIR" "$LOG_DIR"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run_services.sh start [local|flask|docker]
  ./scripts/run_services.sh stop [local|flask|docker]
  ./scripts/run_services.sh restart [local|flask|docker]
  ./scripts/run_services.sh cleanup
  ./scripts/run_services.sh status
  ./scripts/run_services.sh logs [backend]

Defaults:
  Mode defaults to: flask
  Port defaults to: BACKEND_PORT=5000 (or from .env)

Notes:
  - local and flask are the same mode (single Flask service for UI + API)

Examples:
  ./scripts/run_services.sh start
  ./scripts/run_services.sh start flask
  ./scripts/run_services.sh start docker
  ./scripts/run_services.sh stop flask
  ./scripts/run_services.sh cleanup
  ./scripts/run_services.sh status
  ./scripts/run_services.sh logs backend
EOF
}

is_running() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null
}

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn | awk '{print $4}' | grep -q ":$port$"
    return $?
  fi

  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi

  return 1
}

print_port_owner() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    echo "Port $port listeners:"
    lsof -iTCP:"$port" -sTCP:LISTEN || true
  else
    echo "Port $port is in use. Install lsof for process details."
  fi
}

cmdline_for_pid() {
  local pid="$1"
  if [[ -r "/proc/$pid/cmdline" ]]; then
    tr '\0' ' ' <"/proc/$pid/cmdline"
  fi
}

pid_cwd_for_pid() {
  local pid="$1"
  if [[ -L "/proc/$pid/cwd" ]]; then
    readlink "/proc/$pid/cwd"
  fi
}

is_financius_backend_pid() {
  local pid="$1"
  local cmdline
  local cwd
  cmdline="$(cmdline_for_pid "$pid")"
  cwd="$(pid_cwd_for_pid "$pid")"

  if [[ "$cmdline" == *"$ROOT_DIR"* ]] || [[ "$cwd" == "$ROOT_DIR"* ]]; then
    [[ "$cmdline" == *"backend/src/app.py"* ]] || [[ "$cmdline" == *"flask run"* ]]
    return $?
  fi

  return 1
}

kill_if_financius_backend() {
  local pid="$1"

  if [[ -z "$pid" ]]; then
    return
  fi

  if ! is_running "$pid"; then
    return
  fi

  if is_financius_backend_pid "$pid"; then
    echo "Stopping Financius backend process (PID $pid)..."
    kill "$pid"
    return
  fi

  echo "Skipping PID $pid: not recognized as a Financius-owned backend process"
}

start_flask() {
  if port_in_use "$BACKEND_PORT"; then
    echo "Cannot start backend: port $BACKEND_PORT is already in use."
    print_port_owner "$BACKEND_PORT"
    echo "Tip: run ./scripts/run_services.sh cleanup first."
    exit 1
  fi

  if [[ -f "$BACKEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$BACKEND_PID_FILE")"
    if is_running "$pid"; then
      echo "Backend is already running (PID $pid)"
      return
    fi
    rm -f "$BACKEND_PID_FILE"
  fi

  echo "Starting backend (Flask single-service mode)..."
  if [[ -d "$ROOT_DIR/.venv" ]]; then
    (
      cd "$ROOT_DIR"
      source .venv/bin/activate
      FLASK_APP=app:create_app FLASK_ENV=development PYTHONPATH=backend/src nohup flask run --host=0.0.0.0 --port="$BACKEND_PORT" >"$LOG_DIR/backend.log" 2>&1 &
      echo $! >"$BACKEND_PID_FILE"
    )
  else
    (
      cd "$ROOT_DIR"
      FLASK_APP=app:create_app FLASK_ENV=development PYTHONPATH=backend/src nohup flask run --host=0.0.0.0 --port="$BACKEND_PORT" >"$LOG_DIR/backend.log" 2>&1 &
      echo $! >"$BACKEND_PID_FILE"
    )
  fi

  sleep 1
  local pid
  pid="$(cat "$BACKEND_PID_FILE")"
  if is_running "$pid"; then
    echo "Backend started (PID $pid)"
    echo "Log: $LOG_DIR/backend.log"
    echo ""
    echo "Flask single-service mode is running:"
    echo "- App + API: http://localhost:$BACKEND_PORT"
    echo "- Health:    http://localhost:$BACKEND_PORT/api/v1/health"
  else
    echo "Backend failed to start. See log: $LOG_DIR/backend.log"
    exit 1
  fi
}

stop_flask() {
  if [[ -f "$BACKEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$BACKEND_PID_FILE")"
    if is_running "$pid"; then
      echo "Stopping backend (PID $pid)..."
      kill "$pid"
    fi
    rm -f "$BACKEND_PID_FILE"
  else
    echo "Backend is not running (no PID file)."
  fi
}

cleanup_local_financius() {
  echo "Running safe cleanup for local Financius processes..."

  if [[ -f "$BACKEND_PID_FILE" ]]; then
    kill_if_financius_backend "$(cat "$BACKEND_PID_FILE")"
    rm -f "$BACKEND_PID_FILE"
  fi

  # Remove legacy/stale frontend PID file from prior setup.
  rm -f "$RUN_DIR/frontend.pid"

  if command -v lsof >/dev/null 2>&1; then
    while IFS= read -r pid; do
      kill_if_financius_backend "$pid"
    done < <(lsof -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN || true)
  else
    echo "lsof not available; performed PID-file based cleanup only."
  fi

  echo "Cleanup finished."
}

start_docker() {
  echo "Starting backend with Docker Compose..."
  cd "$ROOT_DIR"
  docker compose -f "$DOCKER_COMPOSE_FILE" up --build -d
  echo ""
  echo "Docker mode is running:"
  echo "- App + API: http://localhost:$BACKEND_PORT"
  echo "- Health:    http://localhost:$BACKEND_PORT/api/v1/health"
}

stop_docker() {
  echo "Stopping Docker Compose services..."
  cd "$ROOT_DIR"
  docker compose -f "$DOCKER_COMPOSE_FILE" down
}

show_status() {
  echo "Local process status:"

  if [[ -f "$BACKEND_PID_FILE" ]] && is_running "$(cat "$BACKEND_PID_FILE")"; then
    echo "- Backend: running (PID $(cat "$BACKEND_PID_FILE"))"
  else
    echo "- Backend: not running"
  fi

  echo ""
  echo "Docker status:"
  (
    cd "$ROOT_DIR"
    docker compose -f "$DOCKER_COMPOSE_FILE" ps || true
  )
}

show_logs() {
  local service="${1:-backend}"

  case "$service" in
    backend)
      tail -n 100 "$LOG_DIR/backend.log"
      ;;
    *)
      echo "Only backend logs are available in Flask-only mode."
      exit 1
      ;;
  esac
}

ACTION="${1:-}"
MODE="${2:-flask}"

case "$ACTION" in
  start)
    case "$MODE" in
      local|flask) start_flask ;;
      docker) start_docker ;;
      *) echo "Unknown mode: $MODE"; usage; exit 1 ;;
    esac
    ;;
  stop)
    case "$MODE" in
      local|flask) stop_flask ;;
      docker) stop_docker ;;
      *) echo "Unknown mode: $MODE"; usage; exit 1 ;;
    esac
    ;;
  restart)
    case "$MODE" in
      local|flask)
        stop_flask
        start_flask
        ;;
      docker)
        stop_docker
        start_docker
        ;;
      *)
        echo "Unknown mode: $MODE"
        usage
        exit 1
        ;;
    esac
    ;;
  status)
    show_status
    ;;
  logs)
    show_logs "$2"
    ;;
  cleanup)
    cleanup_local_financius
    ;;
  *)
    usage
    exit 1
    ;;
esac
