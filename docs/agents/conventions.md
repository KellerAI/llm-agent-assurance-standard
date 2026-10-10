# Conventions

Tier-2 detail for [`../../AGENTS.md`](../../AGENTS.md).
This is the authoritative source for commit, branch, and citation conventions in **llm-agent-assurance-standard**.
If a convention changes, it changes here first.

## Commits — Conventional Commits

Every commit subject follows:

```text
<type>(<scope>): <subject>
```

- **`<type>`** — this project uses `feat`, `fix`, `docs`, `chore`, `refactor`, `ci`, and `revert`.
  CI accepts any type in the `@commitlint/config-conventional` preset:
  `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`.
- **`<scope>`** is optional and names the area touched — e.g. `standard`, `conformance`, `scripts`, `docs`, `ci`, `agents`.
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

### What CI enforces

The `Commit lint` workflow runs `commitlint` over every commit in a pull request (`.github/workflows/commitlint.yml:18-26`).
`commitlint.config.js:7` extends `@commitlint/config-conventional`, which the workflow installs unpinned (`.github/workflows/commitlint.yml:22`).
The rules below are from that preset at version 21.2.3, resolved on 2026-09-29.

| Rule | Status |
|------|--------|
| Type is in the preset list above, lowercase | Enforced (preset `type-enum`, `type-case`) |
| Type and subject are non-empty | Enforced (preset `type-empty`, `subject-empty`) |
| No trailing period in the subject | Enforced (preset `subject-full-stop`) |
| Header ≤ 100 characters | Enforced (preset `header-max-length`) |
| Body and footer lines ≤ 100 characters | Enforced (preset `body-max-line-length`, `footer-max-line-length`) |
| Blank line before the body | Warning only (preset `body-leading-blank`) |
| Subject case | Not checked — disabled at `commitlint.config.js:9` |
| Subject ≤ 50 characters | Convention, not a build-breaking rule (`commitlint.config.js:3-5`) |
| Body wrapped at 72 characters | Convention; CI checks only the 100-character limit |
| Imperative mood, lowercase scope | Convention; the preset has no rule for either |

Source: `@commitlint/config-conventional` 21.2.3, npm package `@commitlint/config-conventional`, rules printed from its default export on 2026-09-29.

## Branches

- The default branch is **`main`**. Never `master`.
- Pull requests target **`dev`**, not `main`.
  Changes reach `main` only through `dev` → `qa` → `main`.
- Agent work uses **`<agent>/<scope>`** — the agent's own name, then a short kebab-case scope.
- Humans use **`feat/<scope>`**, **`fix/<scope>`**, **`docs/<scope>`**, **`chore/<scope>`**.
- External contributors use **`external/<type>-<ISSUE-KEY>-<segments>-p<N>`** (see below).

Examples:

```text
claude/fix-typo-readme
codex/clarify-field-constraint
docs/add-open-question
external/feat-ABC-123-auth-adding-oauth-p1
```

Always branch; never open a pull request from your fork's `main`.

### Branch tiers (`validate-branch-tier`)

The `validate-branch-tier` workflow checks every pull request's source branch against its target (`.github/workflows/validate-branch-tier.yml:10-13`, rules at `:50-54`):

- `main` accepts pull requests only from `qa` or `qa/…` branches (`:51`).
- `qa` accepts pull requests only from `dev` or `dev/…` branches (`:52`).
- `dev` accepts pull requests from `external/…` and `dependabot/…` branches (`:53`),
  or from any branch when the pull request author is listed in `.github/CODEOWNERS` (`.github/workflows/validate-branch-tier.yml:33-47`, `:67`).
- A target with no rule (any other branch) is not checked (`:56-59`).

Agent branches such as `claude/<scope>` pass the `dev` check only when a CODEOWNER opens the pull request.

### External branch names (`validate-branch-name`)

The `validate-branch-name` workflow runs only when the source branch starts with `external/` (`.github/workflows/validate-branch-name.yml:14`); other branch names are unrestricted (`:10`).
It requires the pattern `^external/(<type>)-[A-Z]+-\d+(-[a-z][a-z0-9]*)+-p[0-4]$` (`:31-36`), where:

- `<type>` is one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `build`, `perf`, `revert`, `style`, `hotfix`, `spike`, `wip`, `release`, `rnd` (`:23-26`);
- the issue key is uppercase letters, a hyphen, and digits — e.g. `ABC-123` (`:28`);
- one or more lowercase segments give the scope and a gerund (`:29`);
- `p0`–`p4` is the priority, critical to backlog (`:30`).

The workflow's own example is `external/feat-ABC-123-auth-adding-oauth-p1` (`:42`).

## Branch and commit edge cases

The cases below are logical but easy to get wrong.

- **Never work on `main` or a detached `HEAD`.** Always cut a branch first.
- **Always base off the latest `dev`.** Never branch from another in-flight feature branch.
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
- **Forks:** external contributors work from a fork, name the branch `external/…` (see [External branch names](#external-branch-names-validate-branch-name)), and open a PR against this repo's `dev`.

## Local gates

Run these from the repository root before opening a pull request:

```sh
opa check conformance/laas/laas.rego conformance/laas/laas_test.rego
opa test conformance/laas/ -v
opa test conformance/ -v
bash scripts/check-sanitization.sh
bash scripts/laas/check.sh
bash scripts/laas/osi_check.sh
python3 -m unittest discover scripts/laas
```

Expected: `PASS: 96/96` for `conformance/laas/` and `PASS: 167/167` for all of `conformance/`.

In CI, this repository's workflows run the sanitization gate (`bash scripts/check-sanitization.sh`, in `ci.yml`) and invoke OPA only as `opa eval` (in the trust-dial gate workflow, and in the blast-radius pulse workflow via `scripts/pulse.sh`); `opa check`, `opa test`, the Python unit tests, `scripts/laas/check.sh`, and `scripts/laas/osi_check.sh` are local gates that no workflow in this repository's `.github/workflows/` runs, and what the external reusable conformance workflow called from `ci.yml` runs cannot be inspected from this repository.

Sources: `.github/workflows/ci.yml:33-34` (sanitization gate), `.github/workflows/ci.yml:37` (external reusable conformance workflow), `.github/workflows/trust-dial-gate.yml:113` and `scripts/pulse.sh:242` (`opa eval`), `.github/workflows/blast-radius-pulse.yml:60` (runs `scripts/pulse.sh`).

## Citations

- **Internal** references use `file:line` — e.g. `conformance/laas/data.json:14`.
  Cite the absence of a thing as precisely as its presence.
- **External** references use a full bibliographic citation: author(s), title, venue, year.
- Never cite from memory. Verify the file, line, or source first.

## Changing the artifact

`conformance/` is the load-bearing tree.
When you change it:

- State the semver impact in both the commit subject and the PR body.
- Adding a new term? Add it to [`glossary.md`](glossary.md) in the same change.

## Pull requests

Publishable files (`standard/**`, `conformance/**`, `docs/**`, `README.md`) change through a PR.
A PR states what changed and how the change was verified.
Staging files — anything matched by `.gitignore` — need no PR and can be edited directly.

## Capability Roster

When a task needs a specialist capability, prefer the canonical plugin for the
domain. The roster lists KellerAI's defaults; adopters may substitute rows.

| Domain | Canonical capability | Secondary |
| ------ | -------------------- | --------- |
| Session mining | `thoughtbox` | — |
| Capability analysis | `kellerai-repo-audit` | — |
| Repo architecture & scaffolding | `kellerai-repo-audit` | `kellerai-skill-creator` |
| Conformance & policy | `opa-rego` | `kellerai-grc` |
| CI/CD authoring | `git-workflow-tools` | `beads-workflow` |
| Governance & traceability | `kellerai-feature-spec` | `thoughtbox` |
| Documentation | `documentation-audit` | `claude-md-management` |

<!-- BEGIN LOCAL AGENT MODERNIZATION v:1 -->

## Shared agent scope and worktrees

- `AGENTS.md` is the shared project instruction entrypoint. Put shared agent resources in `.agents/`; retain Claude-specific settings, hooks, and plugins in `.claude/`.
- Keep project rules in repository or nested `AGENTS.md` files. Keep machine-local configuration outside tracked shared instructions; do not copy credentials or runtime state into `.agents/`.
- New manually managed worktrees use `<main-checkout>/.worktrees/<branch-slug>`. Verify the exact path is ignored before creation. Preserve existing worktrees and the roots used by Codex/Claude managed worktree tools.
- Before changing tracker storage or commands, verify the intended store and supported CLI. Preserve issue IDs, existing data, uncommitted files, and registered worktrees. Instruction modernization does not authorize storage conversion or checkout relocation.

<!-- END LOCAL AGENT MODERNIZATION -->
