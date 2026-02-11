# Skill: Deploy

## Description

Promotes a source branch into a target branch via a pull request. Creates the PR, runs tests, and merges if they pass. One approval, no extra prompts.

The deployment model is three-tier: **feature branch → test → main**. The `main` branch is never used as a direct source for merging into `test`. If `/deploy test` is invoked while on `main`, a temporary staging branch is created automatically so that commits flow properly through `test` first.

Two modes:
- `/deploy` — Promotes `test` → `main` (default). Full release with branch cleanup.
- `/deploy test` — Promotes current branch → `test`. Integration deploy for feature branches.

## Trigger

- Invoked by the `/deploy` slash command.
- Source branch must be ahead of target branch.

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| target | String | No | Target branch: `main` (default) or `test` |
| tag | String | No | Version tag for the merge commit (e.g., `v1.2.0`). Only valid when target is `main`. |

## Branch Resolution

| Target | Source | Condition | Use Case |
|--------|--------|-----------|----------|
| `main` | `test` | Always | Release: promote test to production |
| `test` | current branch | Not on `main` | Integration: merge feature branch into test |
| `test` | `deploy/YYYY-MM-DD` (auto-created) | On `main`, commits ahead of `origin/main` | Staging: unpushed commits deployed via temp branch |
| `test` | *(abort)* | On `main`, clean and up-to-date | Nothing to deploy |

When target is `test` and you are not on `main`, the source is whatever branch you are on. This is typically a `bean/BEAN-NNN-<slug>` feature branch.

If a `deploy/YYYY-MM-DD` branch already exists, append `-2`, `-3`, etc. to avoid collisions.

## Process

### Phase 1: Preparation

1. **Save current branch** — Record it so we can return at the end.
2. **Check for uncommitted changes** — Run `git status --porcelain`.
   - If clean: continue to step 3.
   - If dirty: show the list of modified/untracked files and prompt the user:
     - **Commit** — Stage all changes and commit with a message summarizing the changes (follow the repo's commit style). Then continue.
     - **Stash** — Run `git stash --include-untracked -m "deploy-auto-stash"`. Restore at the end.
     - **Abort** — Stop the deploy. The user should handle uncommitted changes manually.
3. **Determine source and target:**
   - If target is `main`: source = `test`. Checkout `test`.
   - If target is `test` and NOT on `main`: source = the saved current branch. Stay on that branch.
   - If target is `test` and ON `main`:
     1. Compute staging branch name: `deploy/YYYY-MM-DD`. If that already exists, append `-2`, `-3`, etc.
     2. Check `git log origin/main..main --oneline`. If non-empty (commits ahead of origin):
        - `git branch <staging>` — create the staging branch at current HEAD.
        - `git reset --hard origin/main` — reset local main back to match remote (commits are safe on the staging branch).
        - `git checkout <staging>` — switch to the staging branch.
        - source = `<staging>`.
     3. If main matches origin/main (nothing ahead): report "Nothing to deploy — main is up-to-date with origin. Switch to a feature branch first.", restore stash, return to original branch, exit.

   **Note on stash interaction:** Step 2 resolves dirty working tree state before step 3 runs. If the user chose "Commit", changes are now committed on main and fall into case 3.2 above (commits ahead). If the user chose "Stash", changes are held separately and not deployed — stash is restored at exit.
4. **Push source** — `git push origin <source>` to ensure remote is up to date.
5. **Verify ahead of target** — `git log <target>..<source> --oneline`. If empty, report "Nothing to deploy", restore stash, return to original branch, exit.

### Phase 2: Quality Gate

6. **Run tests** — `pytest tests/` on the source branch.
   - If any fail: report failures, restore stash, return to original branch. Stop.
   - If all pass: record the count.

7. **Run ruff** — `flake8 src/ tests/`. Record result.

### Phase 3: Build Release Notes

8. **Identify beans** — Parse `git log <target>..<source> --oneline` for `BEAN-NNN:` messages. Cross-reference with `ai/beans/_index.md` for titles.

9. **Count branches to clean** (target=`main` only) — List all `bean/*` branches (local + remote). Count how many are merged into main.

### Phase 4: User Approval — ONE prompt

10. **Present summary and ask once:**
    ```
    ===================================================
    DEPLOY: <source> → <target> (via PR)
    ===================================================

    Beans: <list>
    Tests: N passed, 0 failed
    Ruff: clean / N violations

    Post-merge: N feature branches will be deleted
    (branch cleanup shown only for target=main)

    On "go": create PR, merge it, delete branches,
    restore working tree. No further prompts.
    ===================================================
    ```

11. **Single approval:**
    - Target `main`: go / go with tag / abort
    - Target `test`: go / abort

    **CRITICAL: This is the ONLY user prompt. Everything after "go" runs without stopping.**

### Phase 5: Execute (no further prompts)

12. **Create PR:**
    ```bash
    gh pr create --base <target> --head <source> \
      --title "Deploy: <date> — <bean list summary>" \
      --body "<release notes>"
    ```

13. **Merge PR:**
    ```bash
    gh pr merge <pr-number> --merge --subject "Deploy: <date> — <bean list>"
    ```
    Use `--merge` (not squash/rebase) to preserve history.

14. **Tag (optional, target=`main` only)** — If requested: `git tag <version> && git push origin --tags`.

15. **Delete local feature branches (target=`main` only)** — All `bean/*` branches merged into main: `git branch -d`. Stale/orphaned ones for Done beans: `git branch -D`.

16. **Delete remote feature branches (target=`main` only)** — Any `remotes/origin/bean/*`: `git push origin --delete`.

17. **Delete staging branch (if created)** — If a `deploy/*` staging branch was created in step 3:
    - Delete local: `git branch -D <staging>`
    - Delete remote: `git push origin --delete <staging>`

18. **Sync local target** — `git checkout <target> && git pull origin <target>`.

19. **Return to original branch** — `git checkout <original-branch>`. If a staging branch was created (original was `main`), return to `main`.

20. **Restore stash** — If the user chose "Stash" in step 2: `git stash pop`. On conflict, prefer HEAD. (No action needed if the user chose "Commit".)

21. **Report success** — PR URL, merge commit, beans deployed, branches deleted (if applicable).

## Key Rules

- **One approval gate.** User says "go" once. Everything after is automatic.
- **Uncommitted changes prompt.** If the working tree is dirty, the user chooses: commit, stash, or abort. Nothing is silently discarded.
- **PR is created AND merged.** Not just created — the full cycle completes.
- **Branch cleanup only on main deploys.** Feature branches are cleaned up when promoting to main, not when merging to test.
- **If a command is blocked by sandbox:** print the exact command for the user to run manually, then continue with the rest.

## Error Conditions

| Error | Resolution |
|-------|------------|
| Nothing to deploy | Report and exit |
| Tests fail | Report failures, restore stash, return. Fix first. |
| PR create fails | Report error. Check `gh auth status`. |
| PR merge fails | Report error. Check branch protection / conflicts. |
| User aborts | Restore stash, return to original branch |
| Command blocked | Print command for manual execution, continue |
| On main with nothing to deploy | Report and exit. Suggest switching to a feature branch. |
| Staging branch reset fails | Report error. Staging branch still holds commits for recovery. |
