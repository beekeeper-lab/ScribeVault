#!/usr/bin/env bash
# claude-link.sh — Rebuild .claude/ assembly symlinks from kit + local
# Run after: submodule update, adding/removing local assets, or kit changes
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$REPO_ROOT/.claude"
KIT_DIR="$CLAUDE_DIR/kit"
LOCAL_DIR="$CLAUDE_DIR/local"

if [ ! -d "$KIT_DIR" ]; then
  echo "ERROR: claude-kit submodule not found at $KIT_DIR"
  echo "Run: git submodule update --init --recursive"
  exit 1
fi

# --- Commands ---
echo "Linking commands..."
mkdir -p "$CLAUDE_DIR/commands"

# Remove existing symlinks (preserve real files)
find "$CLAUDE_DIR/commands" -maxdepth 1 -type l -delete

# Link kit commands (top-level .md files)
for f in "$KIT_DIR/commands/"*.md; do
  [ -f "$f" ] || continue
  ln -sfn "../kit/commands/$(basename "$f")" "$CLAUDE_DIR/commands/$(basename "$f")"
done

# Link kit commands/internal/ directory
if [ -d "$KIT_DIR/commands/internal" ]; then
  ln -sfn ../kit/commands/internal "$CLAUDE_DIR/commands/internal"
fi

# Link local commands (override kit if name collides)
for f in "$LOCAL_DIR/commands/"*.md; do
  [ -f "$f" ] || continue
  ln -sfn "../local/commands/$(basename "$f")" "$CLAUDE_DIR/commands/$(basename "$f")"
done

# --- Skills ---
echo "Linking skills..."
mkdir -p "$CLAUDE_DIR/skills"

# Remove existing symlinks (preserve real dirs)
find "$CLAUDE_DIR/skills" -maxdepth 1 -type l -delete

# Link kit skills (top-level directories)
for d in "$KIT_DIR/skills"/*/; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  ln -sfn "../kit/skills/$name" "$CLAUDE_DIR/skills/$name"
done

# Link kit skills/internal/ directory
if [ -d "$KIT_DIR/skills/internal" ]; then
  ln -sfn ../kit/skills/internal "$CLAUDE_DIR/skills/internal"
fi

# Link local skills (override kit if name collides)
for d in "$LOCAL_DIR/skills"/*/; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  ln -sfn "../local/skills/$name" "$CLAUDE_DIR/skills/$name"
done

# --- Agents ---
echo "Linking agents..."
mkdir -p "$CLAUDE_DIR/agents"

# Remove existing symlinks
find "$CLAUDE_DIR/agents" -maxdepth 1 -type l -delete

# Link kit agents
for f in "$KIT_DIR/agents/"*.md; do
  [ -f "$f" ] || continue
  ln -sfn "../kit/agents/$(basename "$f")" "$CLAUDE_DIR/agents/$(basename "$f")"
done

# Link local agents (override kit if name collides)
for f in "$LOCAL_DIR/agents/"*.md; do
  [ -f "$f" ] || continue
  ln -sfn "../local/agents/$(basename "$f")" "$CLAUDE_DIR/agents/$(basename "$f")"
done

# --- Hooks & Settings ---
echo "Linking hooks and settings..."
ln -sfn kit/hooks "$CLAUDE_DIR/hooks"
ln -sfn kit/settings.json "$CLAUDE_DIR/settings.json"

echo "Done. Linked assets from kit + local into .claude/"
