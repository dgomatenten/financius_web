#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASKS_FILE_DEFAULT="$ROOT_DIR/specs/001-financius-web-companion/tasks.md"
TASKS_FILE="${SPECKIT_TASKS_FILE:-$TASKS_FILE_DEFAULT}"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/speckit_tasks.sh status
  ./scripts/speckit_tasks.sh next
  ./scripts/speckit_tasks.sh pick <pattern>
  ./scripts/speckit_tasks.sh done <TaskID>
  ./scripts/speckit_tasks.sh reopen <TaskID>

Commands:
  status            Show done/remaining counts and current phase
  next              Show first unchecked task (overall)
  pick <pattern>    Show first unchecked task matching pattern (e.g. US2 or Phase 4)
  done <TaskID>     Mark a task as completed (e.g. T023)
  reopen <TaskID>   Mark a completed task back to unchecked

Notes:
  - Default tasks file: specs/001-financius-web-companion/tasks.md
  - Override with: SPECKIT_TASKS_FILE=/path/to/tasks.md
EOF
}

die() {
  echo "Error: $*" >&2
  exit 1
}

require_tasks_file() {
  [[ -f "$TASKS_FILE" ]] || die "tasks file not found: $TASKS_FILE"
}

phase_for_line() {
  local line_number="$1"
  awk -v n="$line_number" '
    NR <= n && /^## Phase / { phase = $0 }
    END {
      if (phase == "") {
        print "## Phase Unknown"
      } else {
        print phase
      }
    }
  ' "$TASKS_FILE"
}

first_unchecked_line() {
  grep -nE '^- \[ \] T[0-9]{3}\b' "$TASKS_FILE" | head -n 1 || true
}

show_status() {
  local done_count remaining_count total_count next_line next_nr next_task phase
  done_count="$(grep -cE '^- \[x\] T[0-9]{3}\b' "$TASKS_FILE" || true)"
  remaining_count="$(grep -cE '^- \[ \] T[0-9]{3}\b' "$TASKS_FILE" || true)"
  total_count=$((done_count + remaining_count))

  echo "Tasks file: $TASKS_FILE"
  echo "Progress: $done_count/$total_count done, $remaining_count remaining"

  next_line="$(first_unchecked_line)"
  if [[ -z "$next_line" ]]; then
    echo "Current phase: complete"
    echo "Next task: none"
    return
  fi

  next_nr="${next_line%%:*}"
  next_task="${next_line#*:}"
  phase="$(phase_for_line "$next_nr")"

  echo "Current phase: $phase"
  echo "Next task: $next_task"
}

show_next() {
  local next_line next_nr next_task phase
  next_line="$(first_unchecked_line)"
  if [[ -z "$next_line" ]]; then
    echo "No unchecked tasks found."
    return
  fi

  next_nr="${next_line%%:*}"
  next_task="${next_line#*:}"
  phase="$(phase_for_line "$next_nr")"

  echo "$phase"
  echo "$next_task"
}

show_pick() {
  local pattern line line_nr task phase
  pattern="${1:-}"
  [[ -n "$pattern" ]] || die "pick requires a pattern (example: US2 or Phase 4)"

  line="$(grep -nE "^- \[ \].*${pattern}" "$TASKS_FILE" | head -n 1 || true)"
  if [[ -z "$line" ]]; then
    echo "No unchecked tasks found for pattern: $pattern"
    return
  fi

  line_nr="${line%%:*}"
  task="${line#*:}"
  phase="$(phase_for_line "$line_nr")"

  echo "$phase"
  echo "$task"
}

mark_task() {
  local from to task_id line_number
  from="$1"
  to="$2"
  task_id="$3"

  [[ "$task_id" =~ ^T[0-9]{3}$ ]] || die "Task ID must look like T023"

  line_number="$(grep -nE "^- \[$from\] ${task_id}\b" "$TASKS_FILE" | head -n 1 | cut -d: -f1 || true)"
  [[ -n "$line_number" ]] || die "Task ${task_id} with state [$from] not found"

  sed -i "${line_number}s/^- \[$from\] ${task_id}\b/- [$to] ${task_id}/" "$TASKS_FILE"
  echo "Updated ${task_id}: [$from] -> [$to]"
}

main() {
  require_tasks_file

  local command="${1:-}"
  case "$command" in
    status)
      show_status
      ;;
    next)
      show_next
      ;;
    pick)
      show_pick "${2:-}"
      ;;
    done)
      mark_task " " "x" "${2:-}"
      ;;
    reopen)
      mark_task "x" " " "${2:-}"
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      die "unknown command: $command"
      ;;
  esac
}

main "$@"
