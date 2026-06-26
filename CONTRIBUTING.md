# Contributing to llm-agent-assurance-standard

Thanks for helping improve this project.
Agents should start at [`AGENTS.md`](AGENTS.md) — it and [`docs/agents/`](docs/agents/) are authoritative for every convention summarized below.

## Before you start

- For anything beyond a typo, open an **issue** first using one of the
  [issue forms](.github/ISSUE_TEMPLATE) — defects, clarifications, amendment
  proposals, and integration questions each have a structured form.
- The default branch is `main`.
  Branch from it.
  Never commit to `main` directly, and never open a pull request from your fork's `main`.

## Branches and commits

- **Branch naming:** `<agent>/<scope>` for agent work (e.g. `claude/fix-typo`);
  `feat/…  fix/…  docs/…  chore/…` for human work.
  Edge cases are documented in [`docs/agents/conventions.md`](docs/agents/conventions.md).
- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org):
  `<type>(<scope>): <subject>`, imperative mood, subject ideally ≤ 50 characters.
  `commitlint` enforces this as a hard CI gate.

## Validation

Before opening a pull request, run:

```sh
bash scripts/check-sanitization.sh
opa --help   # see docs/agents/conventions.md for the full gate command
```

Both must pass.
CI additionally runs Markdown lint and a link check.
To run the gates automatically on every commit, install the hook with `lefthook install` (optional but recommended).

## Semver policy

The artifact is versioned with Semantic Versioning:

- **major** — a breaking change to an interface, contract, or load-bearing element.
- **minor** — an additive, backward-compatible change.
- **patch** — a clarification or editorial change with no contract impact.

State the classification in your pull request — the PR template has a checklist.

## Pull request checklist

- [ ] Branched from `main`; the branch name follows the convention.
- [ ] Commit messages are valid Conventional Commits.
- [ ] `check-sanitization.sh` passes.
- [ ] The primary validator (`opa`) passes on affected artifacts.
- [ ] New vocabulary is added to [`docs/agents/glossary.md`](docs/agents/glossary.md).
- [ ] The pull request template's sections are filled in.

## Conduct

Be precise, cite your sources, and assume good faith.
Discussion happens on issues and pull requests.
