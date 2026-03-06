#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_ENV_FILE="$BACKEND_DIR/.env"
BACKEND_ENV_EXAMPLE="$BACKEND_DIR/.env.example"
BACKEND_VENV_DIR="$BACKEND_DIR/.venv"
BACKEND_VENV_PYTHON="$BACKEND_VENV_DIR/bin/python"

backend_pid=""
frontend_pid=""

log() {
  printf '[start_dev] %s\n' "$1"
}

fail() {
  printf '[start_dev] %s\n' "$1" >&2
  exit 1
}

warn_if_windows_mount() {
  if [[ "$ROOT_DIR" == /mnt/* ]]; then
    log "Warning: repository is running from $ROOT_DIR"
    log "Vite hot reload is often unreliable on /mnt/... paths under WSL."
    log "Recommended: move the repo into a WSL-native path such as ~/workspace/rag-openrouter-react"
    log "Helper: bash scripts/migrate_to_wsl.sh"
  fi
}

cleanup() {
  local exit_code=$?

  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
  fi

  if [[ -n "$frontend_pid" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid" 2>/dev/null || true
  fi

  wait "$backend_pid" "$frontend_pid" 2>/dev/null || true

  if [[ $exit_code -ne 0 ]]; then
    log "Stopped with exit code $exit_code."
  fi
}

trap cleanup EXIT INT TERM

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi

  fail "Python 3 is required but was not found."
}

find_node_runner() {
  if command -v pnpm >/dev/null 2>&1; then
    printf 'pnpm'
    return
  fi

  if command -v npm >/dev/null 2>&1; then
    printf 'npm'
    return
  fi

  fail "pnpm or npm is required but neither was found."
}

ensure_backend_env() {
  if [[ -f "$BACKEND_ENV_FILE" ]]; then
    return
  fi

  if [[ -f "$BACKEND_ENV_EXAMPLE" ]]; then
    cp "$BACKEND_ENV_EXAMPLE" "$BACKEND_ENV_FILE"
    fail "Created backend/.env from .env.example. Fill AI_API_KEY and rerun."
  fi

  fail "backend/.env is missing."
}

ensure_backend_venv() {
  local python_bin="$1"

  if [[ -x "$BACKEND_VENV_PYTHON" ]]; then
    return
  fi

  log "Creating backend virtualenv..."
  "$python_bin" -m venv "$BACKEND_VENV_DIR"
  "$BACKEND_VENV_PYTHON" -m pip install --upgrade pip
  "$BACKEND_VENV_PYTHON" -m pip install -r "$BACKEND_DIR/requirements.txt"
}

ensure_frontend_deps() {
  local node_runner="$1"

  if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
    return
  fi

  log "Installing frontend dependencies..."
  (
    cd "$FRONTEND_DIR"
    if [[ "$node_runner" == "pnpm" ]]; then
      pnpm install
    else
      npm install
    fi
  )
}

start_backend() {
  log "Starting backend on http://localhost:$BACKEND_PORT ..."
  (
    cd "$BACKEND_DIR"
    exec "$BACKEND_VENV_PYTHON" -m uvicorn app:app --reload --port "$BACKEND_PORT"
  ) &
  backend_pid=$!
}

start_frontend() {
  local node_runner="$1"

  log "Starting frontend on http://localhost:$FRONTEND_PORT ..."
  (
    cd "$FRONTEND_DIR"
    if [[ "$node_runner" == "pnpm" ]]; then
      exec pnpm dev --host 0.0.0.0 --port "$FRONTEND_PORT"
    fi

    exec npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"
  ) &
  frontend_pid=$!
}

main() {
  local python_bin
  local node_runner

  python_bin="$(find_python)"
  node_runner="$(find_node_runner)"

  warn_if_windows_mount
  ensure_backend_env
  ensure_backend_venv "$python_bin"
  ensure_frontend_deps "$node_runner"

  start_backend
  start_frontend "$node_runner"

  log "Backend PID: $backend_pid"
  log "Frontend PID: $frontend_pid"
  log "Press Ctrl+C to stop both processes."

  wait -n "$backend_pid" "$frontend_pid"
}

main "$@"
