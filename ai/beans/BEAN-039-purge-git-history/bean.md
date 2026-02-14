# BEAN-039: Purge Git History for Publication

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-039     |
| Title     | Purge Git History for Publication |
| Type      | enhancement |
| Priority  | P0 |
| Status    | In Progress  |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The repository is about to be published on GitHub. A security audit found two critical issues in git history that must be addressed before the first public push:

1. **Real meeting transcripts with sensitive business data** committed in the `summaries/` directory. These contain real people's names (Nick, Ricky), company details (Zebra Technologies VAR, ~30 employees), business strategy discussions, settlement negotiations, and client project specifics. A simple `git rm` only removes them from HEAD -- the data persists in all prior commits.

2. **Personal/professional email addresses in commit metadata** that link the developer's real identity and employer to the project:
   - `gregg@beekeeper-lab.com` (personal domain)
   - `gregg.reed@stonewatersconsulting.com` (employer domain, reveals full name)
   - `Gregg Reed <reed@example.com>` (full name)

Once the repository is pushed to a public remote, this data cannot be removed (forks, caches, mirrors will preserve it).

## Goal

All sensitive data is removed from every commit in git history. All commit author/committer identities are unified to a single, chosen identity. The repository is safe for public publication.

## Scope

### In Scope

- Install `git-filter-repo` if not already available
- Remove the entire `summaries/` directory from all git history
- Unify all author/committer identities to a single identity (e.g., `Gregg Reed <reed@example.com>`) using a mailmap
- Verify no traces of sensitive data remain with `git log --all --diff-filter=A -- 'summaries/'`
- Run `git log --all --format='%an <%ae>' | sort -u` to verify unified identity
- Force-push the rewritten history to all remotes (if any exist)

### Out of Scope

- Rewriting commit messages (only metadata and file removal)
- Changing the "Beekeeper Lab" organization name in source files (that's an identity/branding decision, not a security concern)
- Purging the 2MB PNG images from history (would require LFS migration, separate concern)

## Acceptance Criteria

- [ ] `git log --all -- 'summaries/'` returns zero results
- [ ] `git log --all --format='%an <%ae>' | sort -u` shows only the chosen unified identity plus `ScribeVault AI Team <ai-team@scribevault.dev>` and `snyk-bot <snyk-bot@snyk.io>`
- [ ] No file matching `summaries/*.md` exists in any commit
- [ ] `git filter-repo` ran successfully without errors
- [ ] Repository still builds/runs after history rewrite
- [ ] All branch references are intact

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create mailmap file with identity mappings | developer | | TODO |
| 2 | Run git filter-repo to remove summaries/ and rewrite identities | developer | 1 | TODO |
| 3 | Verify no sensitive data remains in any commit | tech-qa | 2 | TODO |
| 4 | Verify repository integrity (branches, tags, build) | tech-qa | 2 | TODO |
| 5 | Force-push rewritten history to remotes | developer | 3-4 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

**This bean MUST be completed before any public push.** Once history is public, it cannot be un-published.

The mailmap should map:
```
Gregg Reed <reed@example.com> <gregg@beekeeper-lab.com>
Gregg Reed <reed@example.com> <gregg.reed@stonewatersconsulting.com>
```

The `beekeeper-lab` committer name should also be rewritten:
```
Gregg Reed <reed@example.com> beekeeper-lab <gregg.reed@stonewatersconsulting.com>
Gregg Reed <reed@example.com> Gregg <gregg@beekeeper-lab.com>
```

After running `git filter-repo`, all local clones and remotes will need to be force-updated. Any existing forks would retain the old history.

Depends on BEAN-035 (Root-Level Test Files & Repo Hygiene) — to add `summaries/` to `.gitignore` so it doesn't get re-committed after the history rewrite.
