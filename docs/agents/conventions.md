# Conventions

Tier-2 detail for [`../../AGENTS.md`](../../AGENTS.md).
This is the authoritative source for commit, branch, and citation conventions in **llm-agent-assurance-standard**.
If a convention changes, it changes here first.

## Commits — Conventional Commits

Every commit subject follows:

```text
<type>(<scope>): <subject>
```

- **`<type>`** is one of `feat`, `fix`, `docs`, `chore`, `refactor`, `ci`, `revert`.
- **`<scope>`** is optional and names the area touched — e.g. `conformance`, `docs`, `ci`, `agents`.
  Omit it for repo-wide changes.
- **`<subject>`** is imperative mood, ≤ 50 characters, no trailing period.

Examples:

```text
feat(conformance): add widget element
docs(agents): expand glossary with new term
fix(conformance): correct field constraint wording
chore(ci): pin lychee action to commit SHA
docs(agents): add bake-window term to the glossary
```

A commit body is optional.
When present it explains *why*, wraps at 72 characters, and is separated from the subject by one blank line.

## Branches

- The default branch is **`main`**. Never `master`.
- Agent work uses **`<agent>/<scope>`** — the agent's own name, then a short kebab-case scope.
- Humans use **`feat/<scope>`**, **`fix/<scope>`**, **`docs/<scope>`**, **`chore/<scope>`**.

Examples:

```text
claude/fix-typo-readme
codex/clarify-field-constraint
human/add-open-question
```

Always branch; never open a pull request from your fork's `main`.

## Branch and commit edge cases

The cases below are logical but easy to get wrong.

- **Never work on `main` or a detached `HEAD`.** Always cut a branch first.
- **Always base off the latest `main`.** Never branch from another in-flight feature branch.
- **Continuing another agent's branch:** keep the existing `<agent>/<scope>` name.
- **Multi-scope changes:** prefer one scope per branch and PR.
  If a change genuinely spans scopes, omit `<scope>` rather than inventing a compound one.
- **`<scope>` casing:** lowercase, hyphen-separated (`my-scope`, not `myScope`).
- **Reverts and hotfixes:** branch `revert/<scope>`; commit type `revert`.
- **Commit `type` by area:**
  a `CHANGELOG.md` edit is `docs`;
  a `.github/` or CI change is `ci`;
  an edit to `AGENTS.md`, `CLAUDE.md`, or `docs/agents/**` is `docs(agents)`.
- **Subjects** are imperative mood with no trailing period; **bodies** wrap at 72 characters.
- **Worktrees** are fine — the branch inside a worktree still follows the convention.
- **Forks:** external contributors work from a fork and open a PR against this repo's `main`.

## Primary validator workflow

This repo uses **`opa`** as the primary artifact validator.
Run it on all files under `conformance/` before opening a pull request.

## Citations

- **Internal** references use `file:line` — e.g. `conformance/example.json:42`.
  Cite the absence of a thing as precisely as its presence.
- **External** references use a full bibliographic citation: author(s), title, venue, year.
- Never cite from memory. Verify the file, line, or source first.

## Changing the artifact

`conformance/` is the load-bearing tree.
When you change it:

- State the semver impact in both the commit subject and the PR body.
- Adding a new term? Add it to [`glossary.md`](glossary.md) in the same change.

## Pull requests

Publishable files (`conformance/**`, `docs/**`, `README.md`) change through a PR.
A PR states what changed and how the change was verified.
Staging files — anything matched by `.gitignore` — need no PR and can be edited directly.
