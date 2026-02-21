#!/usr/bin/env bash
# claude-publish.sh — Push claude-kit submodule changes, then push parent repo
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
KIT_DIR="$REPO_ROOT/.claude/kit"

# Push Claude-Kit submodule first (if it has changes)
if [ -d "$KIT_DIR/.git" ] || [ -f "$KIT_DIR/.git" ]; then
  cd "$KIT_DIR"
  if [ -n "$(git status --porcelain)" ] || [ "$(git rev-parse HEAD)" != "$(git rev-parse @{u} 2>/dev/null || echo '')" ]; then
    echo "Pushing Claude-Kit submodule..."
    git push
  else
    echo "Claude-Kit submodule is up to date."
  fi
  cd "$REPO_ROOT"
fi

echo "Pushing parent repo..."
git push

echo "Publish complete."
