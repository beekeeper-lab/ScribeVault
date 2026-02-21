# Skill: Deploy

## Description

Creates a release from the current `main` branch. Runs quality gates (tests, lint), reviews documentation, builds release notes from bean commits since the last tag, optionally tags the release, and cleans up merged feature branches. One approval, no extra prompts.

With trunk-based development, feature branches merge directly to `main` via `/merge-bean`. The deploy skill validates the accumulated work on `main` and produces a tagged release.

## Trigger

- Invoked by the `/deploy` slash command.
- Must be run on the `main` branch.
- `main` must have commits ahead of the last release tag (or ahead of the initial commit if no tags exist).

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| tag | String | No | Version tag for the release (e.g., `v1.2.0`). If not provided, a date-based tag `deploy/YYYY-MM-DD` is used (appending `-2`, `-3`, etc. on collision). |

## Process

### Phase 1: Preparation

1. **Save current branch** — Record it so we can return at the end.
2. **Check for uncommitted changes** — Run `git status --porcelain`.
   - If clean: continue to step 3.
   - If dirty: show the list of modified/untracked files and prompt the user:
     - **Commit** — Stage all changes and commit with a message summarizing the changes (follow the repo's commit style). Then continue.
     - **Stash** — Run `git stash --include-untracked -m "deploy-auto-stash"`. Restore at the end.
     - **Abort** — Stop the deploy. The user should handle uncommitted changes manually.
3. **Ensure on `main`** — If not on `main`, checkout `main`.
4. **Pull latest** — `git pull origin main` to ensure we have the latest.
5. **Determine release scope** — Find the last release tag:
   - `git describe --tags --abbrev=0 2>/dev/null` to get the most recent tag.
   - If no tags exist, use the root commit as the baseline.
   - Run `git log <last-tag>..HEAD --oneline`. If empty, report "Nothing to deploy — main has no new commits since last release", restore stash, return. Exit.

### Phase 1.5: Documentation Review

5a. **Identify what changed** — Review `git log <last-tag>..HEAD --oneline` and `git diff <last-tag>..HEAD --stat` to understand the scope of changes being deployed.

5b. **Check documentation checklist** — For each change, review the documentation checklist in `MEMORY.md` (section "Documentation Checklist") and verify that all applicable docs have been updated to reflect the changes. At minimum, always check:
   - `CLAUDE.md`, `README.md`, `ai/context/bean-workflow.md`, `ai/context/project.md`
   - All agent files in `.claude/agents/`
   - The relevant skill and command files in `.claude/skills/` and `.claude/commands/`
   - `CHANGELOG.md`
   - `docs/` for any project documentation

5c. **Search broadly** — Don't just grep for exact strings. Search for related concepts, synonyms, and soft references that may have become stale. For example, if the change modifies the team wave model, search for "wave", "BA", "Architect", "persona", "team", "decompose", etc.

5d. **Update stale docs** — If any documentation is stale, update it now on `main`. Commit the documentation updates before proceeding.

5e. **Check if the checklist itself needs updating** — If the change introduces a new document or removes an existing one, update the Documentation Checklist in `MEMORY.md`.

5f. **Skip conditions** — This phase may be skipped if the deploy contains only documentation changes (no code or workflow changes) or if the user explicitly requests a fast deploy.

### Phase 2: Quality Gate

6. **Run tests** — `uv run pytest` on `main`.
   - If any fail: report failures, restore stash, return to original branch. Stop.
   - If all pass: record the count.

7. **Run ruff** — `uv run ruff check foundry_app/`. Record result.

### Phase 3: Build Release Notes

8. **Identify beans** — Parse `git log <last-tag>..HEAD --oneline` for `BEAN-NNN:` messages. Cross-reference with `ai/beans/_index.md` for titles.

9. **Count branches to clean** — List all `bean/*` branches (local + remote). Count how many are merged into main.

### Phase 4: User Approval — ONE prompt

10. **Present summary and ask once:**
    ```
    ===================================================
    DEPLOY: main @ <short-sha> (tag: <tag>)
    ===================================================

    Beans: <list>
    Tests: N passed, 0 failed
    Ruff: clean / N violations

    Post-deploy: N feature branches will be deleted

    On "go": tag release, push tag, delete branches,
    restore working tree. No further prompts.
    ===================================================
    ```

11. **Single approval:** go / abort

    **CRITICAL: This is the ONLY user prompt. Everything after "go" runs without stopping.**

### Phase 5: Execute (no further prompts)

12. **Create tag** — Determine the tag name:
    - If `--tag <version>` was provided, use that (e.g., `v1.2.0`).
    - Otherwise, use `deploy/YYYY-MM-DD` (appending `-2`, `-3`, etc. on collision).
    - Create annotated tag: `git tag -a <tag> -m "Deploy: <date> — <bean list>"`.
    - Push tag: `git push origin --tags`.

12a. **Sync claude-kit subtree** — Push `.claude/` to the `claude-kit` remote to keep the shared config in sync:
    - `git fetch claude-kit main` — fetch latest claude-kit refs.
    - Compare tree hashes: `git rev-parse HEAD:.claude` vs `git rev-parse FETCH_HEAD^{tree}`.
    - If they differ: run `git subtree push --prefix=.claude claude-kit main`.
    - If they match: already in sync, skip.
    - If the `claude-kit` remote doesn't exist: warn and skip.

13. **Delete local feature branches** — All `bean/*` branches merged into main: `git branch -d`. Stale/orphaned ones for Done beans: `git branch -D`.

14. **Delete remote feature branches** — Any `remotes/origin/bean/*` that are merged: `git push origin --delete`.

15. **Return to original branch** — `git checkout <original-branch>`.

16. **Restore stash** — If the user chose "Stash" in step 2: `git stash pop`. On conflict, prefer HEAD. (No action needed if the user chose "Commit".)

17. **Report success** — Tag name, commit hash, beans deployed, branches deleted.

### Phase 6: Status Check

18. **Run `/git-status`** — After the deploy report, run the `/git-status` command to show the current sync state of all branches. This confirms the deploy landed and shows if `test` needs syncing.

## Key Rules

- **One approval gate.** User says "go" once. Everything after is automatic.
- **Uncommitted changes prompt.** If the working tree is dirty, the user chooses: commit, stash, or abort. Nothing is silently discarded.
- **Tag is created AND pushed.** Not just created locally — the tag is pushed to the remote.
- **Branch cleanup happens on every deploy.** Merged feature branches are cleaned up.
- **If a command is blocked by sandbox:** print the exact command for the user to run manually, then continue with the rest.

## Error Conditions

| Error | Resolution |
|-------|------------|
| Nothing to deploy | No new commits since last tag — report and exit |
| Tests fail | Report failures, restore stash, return. Fix first. |
| Tag already exists | Append suffix or prompt for a different tag name |
| Tag push fails | Report error. Check permissions. |
| User aborts | Restore stash, return to original branch |
| Command blocked | Print command for manual execution, continue |
