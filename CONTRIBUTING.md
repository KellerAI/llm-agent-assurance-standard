# Contributing to llm-agent-assurance-standard

Thanks for helping improve this project.
Agents should start at [`AGENTS.md`](AGENTS.md) — it and [`docs/agents/`](docs/agents/) are authoritative for every convention summarized below.

## Before you start

- For anything beyond a typo, open an **issue** first using one of the
  [issue forms](.github/ISSUE_TEMPLATE) — defects, clarifications, amendment
  proposals, and integration questions each have a structured form.
- The default branch is `main`, but pull requests target `dev`.
  Changes reach `main` only through `dev` → `qa` → `main`.
  CI enforces this tier model (`.github/workflows/validate-branch-tier.yml:10-13`):
  `main` accepts pull requests only from `qa/**`, `qa` only from `dev/**`,
  and `dev` only from `external/**`, `dependabot/**`, or a branch opened by `son-of-anton-ai` (`.github/workflows/validate-branch-tier.yml:37-41`, `:54`).
  Never commit to `main` directly, and never open a pull request from your fork's `main`.

## Branches and commits

- **Branch naming:** `<agent>/<scope>` for agent work (e.g. `claude/fix-typo`);
  `feat/…  fix/…  docs/…  chore/…` for human work.
  CI checks names only for `external/*` branches, against the pattern `external/<type>-<ISSUE-KEY>-<segments>-p<N>` (`.github/workflows/validate-branch-name.yml:14`, `:31-36`).
  Edge cases are documented in [`docs/agents/conventions.md`](docs/agents/conventions.md).
- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org):
  `<type>(<scope>): <subject>`, imperative mood, subject ideally ≤ 50 characters.
  `commitlint` checks every pull request commit against the Conventional Commits format as a hard CI gate (`commitlint.config.js:2`, `:7`; `.github/workflows/commitlint.yml:18`).
  The ≤ 50-character subject is a convention, not a build-breaking rule (`commitlint.config.js:3-5`), and subject case is not checked (`commitlint.config.js:9`).

## Validation

Before opening a pull request, run:

```sh
opa check conformance/laas/laas.rego conformance/laas/laas_test.rego
opa test conformance/laas/ -v
opa test conformance/ -v
bash scripts/check-sanitization.sh
bash scripts/laas/check.sh
bash scripts/laas/osi_check.sh
python3 -m unittest discover scripts/laas
```

Every command must exit 0.

In CI, this repository's workflows run the sanitization gate (`bash scripts/check-sanitization.sh`, in `ci.yml`) and invoke OPA only as `opa eval` (in the trust-dial gate workflow, and in the blast-radius pulse workflow via `scripts/pulse.sh`); `opa check`, `opa test`, the Python unit tests, `scripts/laas/check.sh`, and `scripts/laas/osi_check.sh` are local gates that no workflow in this repository's `.github/workflows/` runs, and what the external reusable conformance workflow called from `ci.yml` runs cannot be inspected from this repository.

Sources: `.github/workflows/ci.yml:33-34` (sanitization gate), `.github/workflows/ci.yml:37` (external reusable conformance workflow), `.github/workflows/trust-dial-gate.yml:113` and `scripts/pulse.sh:242` (`opa eval`), `.github/workflows/blast-radius-pulse.yml:60` (runs `scripts/pulse.sh`).
CI also runs a JSON well-formedness check (`.github/workflows/ci.yml:18`), Markdown lint (`.github/workflows/ci.yml:30-31`), and a link check (`.github/workflows/ci.yml:47-48`).

`lefthook install` sets up a pre-commit hook that runs only the sanitization gate (the `sanitization` command in `lefthook.yml`); run the other commands by hand.

## Semver policy

The artifact is versioned with Semantic Versioning:

- **major** — a breaking change to an interface, contract, or load-bearing element.
- **minor** — an additive, backward-compatible change.
- **patch** — a clarification or editorial change with no contract impact.

State the classification in your pull request — the PR template has a checklist.

## Pull request checklist

- [ ] The pull request targets `dev`; the branch name follows the convention.
- [ ] Commit messages are valid Conventional Commits.
- [ ] `check-sanitization.sh` passes.
- [ ] The other gate commands under [Validation](#validation) pass.
- [ ] New vocabulary is added to [`docs/agents/glossary.md`](docs/agents/glossary.md).
- [ ] The pull request template's sections are filled in.

## Conduct

Be precise, cite your sources, and assume good faith.
Discussion happens on issues and pull requests.
