#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
PID_FILE="$RUN_DIR/gh600_web.pid"
REQUIREMENTS_FILE="$ROOT_DIR/gh600_study_app/requirements.txt"

VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
VENV_PIP="$ROOT_DIR/.venv/bin/pip"
PORT="${GH600_STUDY_PORT:-5080}"

mkdir -p "$RUN_DIR" "$LOG_DIR"

usage() {
  cat <<EOF
Usage:
  ./scripts/start_gh600_web.sh start
  ./scripts/start_gh600_web.sh stop
  ./scripts/start_gh600_web.sh restart
  ./scripts/start_gh600_web.sh status
  ./scripts/start_gh600_web.sh logs

Environment:
  GH600_STUDY_PORT   Web app port (default: 5080)
  GH600_STUDY_SECRET Flask session secret (recommended)
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

wait_for_server() {
  local max_tries=20
  local i=1

  while [[ "$i" -le "$max_tries" ]]; do
    if curl -sf "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then
      echo ""
      echo "Web app is up: http://127.0.0.1:$PORT"
      return 0
    fi
    printf "."
    sleep 1
    i=$((i + 1))
  done

  echo ""
  echo "Web app did not become ready within ${max_tries}s."
  echo "Check logs with: ./scripts/start_gh600_web.sh logs"
  return 1
}

ensure_venv() {
  if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Missing virtual environment at .venv"
    echo "Create it with: python3 -m venv .venv"
    echo "Then install deps: .venv/bin/pip install -r gh600_study_app/requirements.txt"
    exit 1
  fi
}

ensure_dependencies() {
  if [[ -f "$REQUIREMENTS_FILE" ]]; then
    "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE" >/dev/null
  fi
}

start_app() {
  ensure_venv

  if [[ -f "$PID_FILE" ]]; then
    local existing_pid
    existing_pid="$(cat "$PID_FILE")"
    if is_running "$existing_pid"; then
      echo "GH600 web app already running (PID $existing_pid)"
      echo "URL: http://127.0.0.1:$PORT"
      return 0
    fi
    rm -f "$PID_FILE"
  fi

  if port_in_use "$PORT"; then
    echo "Cannot start GH600 web app: port $PORT is already in use."
    echo "Set a different port with GH600_STUDY_PORT, for example:"
    echo "  GH600_STUDY_PORT=5081 ./scripts/start_gh600_web.sh start"
    exit 1
  fi

  echo "Ensuring dependencies are installed..."
  ensure_dependencies

  echo "Starting GH600 web app on port $PORT..."
  (
    cd "$ROOT_DIR"
    nohup "$VENV_PYTHON" -m gh600_study_app >"$LOG_DIR/gh600_web.log" 2>&1 &
    echo $! >"$PID_FILE"
  )

  local pid
  pid="$(cat "$PID_FILE")"

  if is_running "$pid"; then
    echo "Started (PID $pid). Waiting for readiness"
    wait_for_server
  else
    echo "Failed to start GH600 web app."
    echo "Check logs with: ./scripts/start_gh600_web.sh logs"
    exit 1
  fi
}

stop_app() {
  if [[ ! -f "$PID_FILE" ]]; then
    echo "GH600 web app is not running (no PID file)."
    return 0
  fi

  local pid
  pid="$(cat "$PID_FILE")"

  if is_running "$pid"; then
    echo "Stopping GH600 web app (PID $pid)..."
    kill "$pid"

    local i=0
    while is_running "$pid" && [[ "$i" -lt 20 ]]; do
      sleep 0.2
      i=$((i + 1))
    done

    if is_running "$pid"; then
      echo "Process still running, sending SIGKILL..."
      kill -9 "$pid" 2>/dev/null || true
    fi

    echo "Stopped."
  else
    echo "PID file found, but process is not running."
  fi

  rm -f "$PID_FILE"
}

status_app() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if is_running "$pid"; then
      echo "GH600 web app is running (PID $pid)"
      echo "URL: http://127.0.0.1:$PORT"
      return 0
    fi
  fi

  echo "GH600 web app is not running"
}

logs_app() {
  local log_file="$LOG_DIR/gh600_web.log"
  if [[ -f "$log_file" ]]; then
    tail -n 100 "$log_file"
  else
    echo "No logs found yet. Start the app first."
  fi
}

case "${1:-start}" in
  start)
    start_app
    ;;
  stop)
    stop_app
    ;;
  restart)
    stop_app
    start_app
    ;;
  status)
    status_app
    ;;
  logs)
    logs_app
    ;;
  *)
    usage
    exit 1
    ;;
esac
