# /merge-bean Command

Claude Code slash command that merges a bean's feature branch into a target branch (default: `main`) using a safe merge sequence.

## Purpose

After a bean has been verified and committed on its feature branch, the Merge Captain safely merges the work into `main`. This is the final stage of the bean execution wave — it integrates completed work so other beans and the team can build on it.

## Usage

```
/merge-bean <bean-id> [--target <branch>]
```

- `bean-id` -- The bean ID to merge (e.g., `BEAN-011` or just `11`).
- `--target <branch>` -- Target branch to merge into (default: `main`).

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| Bean ID | Command argument | Yes |
| Bean directory | `ai/beans/BEAN-NNN-<slug>/` | Yes (must exist with status `Done`) |
| Feature branch | `bean/BEAN-NNN-<slug>` | Yes (must exist in git) |
| Target branch | `--target` flag or default `main` | Yes |

## Process

1. **Validate bean status** — Read `bean.md` and confirm status is `Done`. If not Done, report error and stop.
2. **Populate Changes section** — On the feature branch, run `git diff --stat <target>...HEAD` to generate a file-level change summary. Parse the output into a markdown table (File, Lines columns) and write it to the `## Changes` section in `bean.md`. Commit the update before proceeding.
3. **Identify feature branch** — Derive branch name `bean/BEAN-NNN-<slug>` from the bean directory name.
4. **Verify feature branch exists** — Run `git branch --list bean/BEAN-NNN-<slug>`. If it doesn't exist, report error and stop.
5. **Save current branch** — Record the current branch name so it can be restored after the merge.
6. **Checkout target branch** — `git checkout <target>`.
7. **Pull latest** — `git pull origin <target>` to get any work merged by other workers since the last pull.
8. **Merge feature branch** — `git merge bean/BEAN-NNN-<slug> --no-ff` (no fast-forward to preserve the merge commit).
9. **Check for conflicts** — If the merge has conflicts:
   - Report the conflicting files.
   - Abort the merge: `git merge --abort`.
   - Return to the feature branch: `git checkout bean/BEAN-NNN-<slug>`.
   - Stop with a clear message listing the conflicts for manual resolution.
10. **Push to target** — `git push origin <target>`.
11. **Delete feature branch** — `git branch -d bean/BEAN-NNN-<slug>`. If also on remote, `git push origin --delete bean/BEAN-NNN-<slug>`.
12. **Return to original branch** — `git checkout <original-branch>` (the branch recorded in step 5).
13. **Report success** — Output: bean title, feature branch (deleted), target branch, merge commit hash.

## Output

| Artifact | Path | Description |
|----------|------|-------------|
| Merge commit | Git history on target branch | Feature branch merged into target |
| Progress report | Console output | Summary of merge result |

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `BeanNotDone` | Bean status is not `Done` | Report error — bean must complete before merging |
| `BranchNotFound` | Feature branch doesn't exist | Report error — was the bean processed on a branch? |
| `MergeConflict` | Auto-merge fails | Report conflicting files, abort merge, return to feature branch |
| `PushFailure` | Push to target branch fails | Report error — check permissions and branch protection |
| `TargetNotFound` | Target branch doesn't exist locally | Verify the target branch exists. Check remote configuration. |

## Examples

**Merge a single bean:**
```
/merge-bean 11
```
Merges `bean/BEAN-011-merge-captain-auto-merge` into `main`.

**Merge to the test branch (used by /long-run):**
```
/merge-bean 11 --target test
```
Merges the feature branch into `test` instead of `main`.

**Merge to a custom branch:**
```
/merge-bean 11 --target dev
```
Merges the feature branch into `dev` instead of `main`.

**Typical output:**
```
✓ Merged BEAN-011 (Merge Captain Auto-Merge)
  Branch: bean/BEAN-011-merge-captain-auto-merge → main
  Commit: f4e5d6c
  Cleaned: branch deleted (local + remote)
```

**Conflict output:**
```
✗ Merge conflict for BEAN-011
  Conflicting files:
    - .claude/skills/long-run/SKILL.md
    - ai/context/bean-workflow.md
  Merge aborted. Returned to bean/BEAN-011-merge-captain-auto-merge.
  Resolve conflicts manually, then re-run /merge-bean 11.
```
