#!/usr/bin/env bash
# claude-sync.sh — Pull latest and update claude-kit submodule
set -euo pipefail

echo "Pulling latest..."
git pull --ff-only

echo "Syncing submodules..."
git submodule sync --recursive
git submodule update --init --recursive

echo "Assembling Claude Code discovery symlinks..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/claude-assemble.sh"

echo "Sync complete."
