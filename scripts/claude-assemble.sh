#!/usr/bin/env bash
# claude-assemble.sh — Build .claude/commands/ and .claude/skills/ from shared + local
#
# Claude Code discovers commands at .claude/commands/*.md and skills at
# .claude/skills/*/SKILL.md.  The shared kit and local extensions live in
# subdirectories (.claude/shared/, .claude/local/) that Claude Code does NOT
# scan automatically.  This script bridges the gap by creating symlinks in the
# top-level discovery directories.
#
# Run after: git submodule update, or whenever shared/local assets change.
# Called automatically by scripts/claude-sync.sh.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$REPO_ROOT/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"
SKILLS_DIR="$CLAUDE_DIR/skills"

# ── Helpers ──────────────────────────────────────────────────────────────────

link_commands() {
  local src_dir="$1"
  [ -d "$src_dir" ] || return 0
  for f in "$src_dir"/*.md; do
    [ -f "$f" ] || continue
    local name
    name="$(basename "$f")"
    ln -sfn "$(realpath --relative-to="$COMMANDS_DIR" "$f")" "$COMMANDS_DIR/$name"
  done
  # Recurse one level for internal/ subdirectory
  if [ -d "$src_dir/internal" ]; then
    mkdir -p "$COMMANDS_DIR/internal"
    for f in "$src_dir/internal"/*.md; do
      [ -f "$f" ] || continue
      local name
      name="$(basename "$f")"
      ln -sfn "$(realpath --relative-to="$COMMANDS_DIR/internal" "$f")" "$COMMANDS_DIR/internal/$name"
    done
  fi
}

link_skills() {
  local src_dir="$1"
  [ -d "$src_dir" ] || return 0
  for d in "$src_dir"/*/; do
    [ -d "$d" ] || continue
    local name
    name="$(basename "$d")"
    # Skip the "internal" meta-directory — handle its children directly
    if [ "$name" = "internal" ]; then
      for id in "$d"*/; do
        [ -d "$id" ] || continue
        local iname
        iname="$(basename "$id")"
        ln -sfn "$(realpath --relative-to="$SKILLS_DIR" "$id")" "$SKILLS_DIR/$iname"
      done
      continue
    fi
    ln -sfn "$(realpath --relative-to="$SKILLS_DIR" "$d")" "$SKILLS_DIR/$name"
  done
}

# ── Clean previous assembly ──────────────────────────────────────────────────

rm -rf "$COMMANDS_DIR" "$SKILLS_DIR"
mkdir -p "$COMMANDS_DIR" "$SKILLS_DIR"

# ── Assemble from shared (kit) ──────────────────────────────────────────────

link_commands "$CLAUDE_DIR/shared/commands"
link_skills  "$CLAUDE_DIR/shared/skills"

# ── Assemble from local ─────────────────────────────────────────────────────

link_commands "$CLAUDE_DIR/local/commands"
link_skills  "$CLAUDE_DIR/local/skills"

# ── Summary ──────────────────────────────────────────────────────────────────

cmd_count=$(find "$COMMANDS_DIR" -name "*.md" | wc -l)
skill_count=$(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 -type l | wc -l)
echo "Assembled $cmd_count commands and $skill_count skills into .claude/"
