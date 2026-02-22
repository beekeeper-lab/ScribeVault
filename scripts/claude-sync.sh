#!/usr/bin/env bash
# claude-sync.sh — Pull latest, update submodule, install hooks, assemble
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$SCRIPT_DIR/githooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

# ── Install git hooks ────────────────────────────────────────────────────────
if [ -d "$HOOKS_SRC" ]; then
  echo "Installing git hooks..."
  mkdir -p "$HOOKS_DST"
  for hook in "$HOOKS_SRC"/*; do
    [ -f "$hook" ] || continue
    cp "$hook" "$HOOKS_DST/$(basename "$hook")"
    chmod +x "$HOOKS_DST/$(basename "$hook")"
  done
fi

echo "Pulling latest..."
git pull --ff-only

echo "Syncing submodules..."
git submodule sync --recursive
git submodule update --init --recursive

echo "Assembling Claude Code discovery symlinks..."
"$SCRIPT_DIR/claude-assemble.sh"

echo "Sync complete."
