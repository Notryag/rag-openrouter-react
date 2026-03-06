#!/usr/bin/env bash

set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-$HOME/workspace/rag-openrouter-react}"

log() {
  printf '[migrate_to_wsl] %s\n' "$1"
}

fail() {
  printf '[migrate_to_wsl] %s\n' "$1" >&2
  exit 1
}

if [[ "$SOURCE_DIR" != /mnt/* ]]; then
  fail "This helper is meant to be run from a Windows-mounted path such as /mnt/d/..."
fi

if ! command -v rsync >/dev/null 2>&1; then
  fail "rsync is required but was not found."
fi

mkdir -p "$(dirname "$TARGET_DIR")"

if [[ -e "$TARGET_DIR" ]]; then
  fail "Target already exists: $TARGET_DIR"
fi

log "Copying repository to $TARGET_DIR ..."
rsync -a \
  --exclude 'backend/.venv/' \
  --exclude 'frontend/node_modules/' \
  --exclude 'frontend/dist/' \
  --exclude 'frontend/.pnpm-store/' \
  --exclude 'frontend/.vite/' \
  --exclude 'frontend/.vite-temp/' \
  "$SOURCE_DIR/" "$TARGET_DIR/"

log "Done."
log "Next steps:"
log "  cd $TARGET_DIR"
log "  git status"
log "  bash scripts/start_dev.sh"
