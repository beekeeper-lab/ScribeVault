# /deploy Command

Creates a release from the current `main` branch. Runs tests, reviews documentation, builds release notes, optionally tags the release, and cleans up merged feature branches — all after a single user approval.

## Usage

```
/deploy [--tag <version>]
```

- `--tag <version>` -- Optional. Tag the release with a version (e.g., `v1.2.0`). If not provided, a date-based tag `deploy/YYYY-MM-DD` is used.

| Command | What It Does |
|---------|-------------|
| `/deploy` | Tag current `main` HEAD with date-based release tag, clean up branches |
| `/deploy --tag v2.0.0` | Tag current `main` HEAD with version tag, clean up branches |

## Process

1. **Check for uncommitted changes** — if dirty, prompt: **Commit** (stage + commit), **Stash** (stash, restore at end), or **Abort**
2. **Ensure on `main`** — checkout `main` if not already there, pull latest
3. **Determine release scope** — find commits since last tag. If none, report "Nothing to deploy" and exit
4. **Review documentation** — Check all docs in the Documentation Checklist (MEMORY.md) for stale references. Search broadly for related concepts. Update any stale docs and commit before proceeding.
5. **Run tests** (`uv run pytest`) and **ruff** (`uv run ruff check foundry_app/`) — stop if they fail
6. **Build release notes** from bean commits in `git log <last-tag>..HEAD`
7. **One approval prompt** — user says "go" or "abort"
8. **Create tag** — annotated tag with release notes, push to remote
9. **Delete** merged feature branches, local + remote
10. **Restore** stash if applicable, return to original branch
11. **Report** — tag name, commit hash, beans deployed, branches deleted

## Examples

```
/deploy              # Tag main HEAD with date-based tag, clean up branches
/deploy --tag v2.0.0 # Tag main HEAD with version tag, clean up branches
```

**Approval prompt:**
```
===================================================
DEPLOY: main @ a1b2c3d (tag: deploy/2026-02-21)
===================================================

Beans: BEAN-029, BEAN-030, BEAN-033
Tests: 750 passed, 0 failed
Ruff: clean

Post-deploy: 3 feature branches will be deleted

On "go": tag release, push tag, delete branches,
restore working tree. No further prompts.
===================================================
```

## Error Handling

| Error | Resolution |
|-------|------------|
| Nothing to deploy | No new commits since last tag — report and exit |
| Tests fail | Report failures, stop. Fix first. |
| Tag already exists | Append suffix or prompt for a different tag name |
| Tag push fails | Check permissions |
| Uncommitted changes | Prompted to commit, stash, or abort before proceeding |
| User aborts | Restore stash, return to original branch |
| Command blocked by sandbox | Prints exact command for manual execution, continues |
