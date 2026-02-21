# Skill: Run

## Description

Pulls the latest code from `main` and launches the Foundry PySide6 desktop app. Designed for the workflow where development happens on a remote server and the app is run locally from freshly pulled code.

## Trigger

- Invoked by the `/run` slash command.

## Usage

```
/run              # Pull main and run
/run main         # Pull main branch and run (explicit)
```

## Process

1. **Save current branch** — Record which branch we're on.
2. **Auto-stash if dirty** — If `git status --porcelain` shows changes, run `git stash --include-untracked -m "run-auto-stash"`. Do NOT ask — just stash.
3. **Fetch latest** — `git fetch origin`.
4. **Checkout branch** — `git checkout main`.
5. **Pull** — `git pull origin main`.
6. **Sync dependencies** — `uv sync` to ensure packages match the pulled code.
7. **Launch app** — `uv run foundry`. This runs in the foreground — the app window opens and Claude waits for it to exit.
8. **Restore** — After the app exits:
   - `git checkout <original-branch>`
   - If we stashed: `git stash pop`
9. **Report** — What branch was run, commit hash, any dependency changes.

## Key Rules

- **Only `main` is a valid target branch.** Reject anything else.
- **No prompts.** This is a pull-and-run — no approval needed.
- **Auto-stash, auto-restore.** Working tree handled silently.
- **`uv sync` before run.** The pulled code may have new/changed dependencies. Always sync first.
- **Foreground execution.** The app runs in the foreground so Claude can detect when it exits and clean up.

## Error Conditions

| Error | Resolution |
|-------|------------|
| Invalid branch | Report: only `main` is a valid target |
| Pull fails | Report error. Check network / remote state. |
| `uv sync` fails | Report error. May need manual dependency resolution. |
| App crashes on launch | Report the error output. Stay on the pulled branch for debugging. |
| Command blocked | Print exact command for manual execution |
