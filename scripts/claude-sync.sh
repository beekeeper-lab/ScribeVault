#!/usr/bin/env bash
# claude-sync.sh — Pull latest and update claude-kit submodule
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Pulling latest..."
git pull --ff-only

echo "Syncing submodules..."
git submodule sync --recursive
git submodule update --init --recursive

echo "Rebuilding .claude/ symlinks..."
"$SCRIPT_DIR/claude-link.sh"

echo "Sync complete."
