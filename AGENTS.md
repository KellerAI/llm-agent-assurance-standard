# AGENTS.md — llm-agent-assurance-standard

This repository is the **LLM-Agent Assurance Standard (LAAS)** — a normative specification
and machine-checkable OPA/Rego policy that gates what actions an autonomous LLM agent may
commit, based on consequence tier and independent verification.

**Humans read [README.md](README.md). Agents start here.**
This file is the Tier-1 entry point. Deeper detail lives under [`docs/agents/`](docs/agents/).

## What this repo IS

- The **normative specification**: [`standard/LAAS.md`](standard/LAAS.md) — prose definition
  of Consequence Tiers CT0–CT4, obligation families, the governing invariant, and the
  verification floor rules. Prose is authoritative; `conformance/laas/data.json` is derived from it.
- The **enforcing OPA policy**: [`conformance/laas/laas.rego`](conformance/laas/laas.rego)
  — package `kellerai.laas.actions`; driven by [`conformance/laas/data.json`](conformance/laas/data.json).
- **Standard-body renderings**: IEEE, ISO, NIST, and SR formats under
  [`docs/laas/standards/`](docs/laas/standards/); PDF build pipeline at
  [`docs/laas/standards/pdf/`](docs/laas/standards/pdf/).
- **Reference tooling**: [`scripts/laas/`](scripts/laas/) — decision-record emitter
  (`emitter.py`), backtest harness (`backtest.py`), OSI-to-surface converter
  (`osi_to_surface.py`), and end-to-end proof scripts (`check.sh`, `osi_check.sh`).
- **Verdict policies**: [`conformance/`](conformance/) — the trust-dial Dependabot auto-merge
  verdict policy (`conformance/trust_dial.rego:2`) and the blast-radius pulse verdict policy
  (`conformance/blast_radius.rego:2`). OPA package list: `docs/agents/enforcement.md` ("Automated gates").
- Licensed **Apache-2.0** — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## What this repo is NOT

- There is **no application runtime** — no package, no build output, no API to import.
  `scripts/laas/` scripts are reference tooling and proof scripts, not production libraries.
- There is **no in-repo issue tracker**. Work is tracked in GitHub Issues.
- There is **no single verification command**. The gates are `opa check`, `opa test`, the
  sanitization script, the two LAAS proof scripts, and the Python unit tests.
  See `## Key commands` for the full list and for which of them CI runs.

## File layout — agent reading order

Load the file that answers your question. Do not load the whole tree.

| Question | Read |
|----------|------|
| What is this project? | `README.md` |
| The normative LAAS specification | `standard/LAAS.md` |
| LAAS OPA policy (quick reference) | `conformance/laas/README.md` |
| LAAS obligation bundle + tier lattice | `conformance/laas/data.json` |
| LAAS Rego policy source | `conformance/laas/laas.rego` |
| LAAS test suite | `conformance/laas/laas_test.rego` |
| Standard-body renderings (IEEE/ISO/NIST/SR) | `docs/laas/standards/` |
| PDF build pipeline | `docs/laas/standards/pdf/README.md` |
| Decision-record tooling | `scripts/laas/` |
| Design rationale / proposal | `docs/laas/proposal-v1.1.md` |
| LAAS design docs (steelman, backtest, emitter) | `docs/laas/` |
| Controlled-language (STE) profiles for decision traces | `docs/laas/profiles/` |
| Architecture decision records | `docs/adr/` |
| Article bibliography | `docs/articles/index.md` |
| Verdict policies (trust dial, blast radius) | `conformance/` |
| What a term means | `docs/agents/glossary.md` |
| Commit, branch, PR rules | `docs/agents/conventions.md` |
| How conventions are enforced | `docs/agents/enforcement.md` |
| How to cite this repo | `docs/agents/citation.md` |

## Key commands

```bash
# Gate commands (run from the repo root)
opa check conformance/laas/laas.rego conformance/laas/laas_test.rego
opa test conformance/laas/ -v
opa test conformance/ -v
bash scripts/check-sanitization.sh
bash scripts/laas/check.sh
bash scripts/laas/osi_check.sh
python3 -m unittest discover scripts/laas

# Evaluate a decision record
opa eval -d conformance/laas/laas.rego -d conformance/laas/data.json \
  -i conformance/laas/examples/action.ct4-blocked.json \
  'data.kellerai.laas.actions.summary' --format pretty
```

Expected results: `opa test conformance/laas/ -v` prints `PASS: 96/96`; `opa test conformance/ -v`
prints `PASS: 167/167` (96 tests in `conformance/laas/laas_test.rego`, 40 in
`conformance/trust_dial_test.rego`, 31 in `conformance/blast_radius_test.rego`); the sanitization
script reports `OK`; `check.sh` (emitter → `opa eval`) ends with compliant `true`; `osi_check.sh`
prints `PASS`; and the unit tests report `Ran 69 tests` and `OK`
(invocation from `scripts/laas/test_osi_to_surface.py:4`).

**What CI runs.** CI runs only the sanitization gate and `opa eval`; the other gates are local.
Detail and sources: `docs/agents/conventions.md` ("Local gates").

## Conventions agents MUST follow

- **Default branch is `main`.** Never create or use `master`.
- **Conventional Commits.** `<type>(<scope>): <subject>` — subject ≤ 50 chars,
  imperative mood. Recommended types: `feat`, `fix`, `chore`, `docs`, `refactor`.
  Scope recommended: `standard`, `conformance`, `scripts`, `docs`.
  The commit-lint workflow enforces the `@commitlint/config-conventional` preset
  (`commitlint.config.js:2`, `:7`), not this shorter list, so other conventional types such
  as `ci` also pass; the ≤ 50-character subject is documented but not enforced
  (`commitlint.config.js:3-5`).
- **Branch naming.** Agent work uses `<agent>/<scope>` — e.g.
  `claude/fix-typo`, `codex/clarify-field`. Human work uses
  `feat/*`, `fix/*`, `docs/*`, `chore/*`.
  CI checks branch names only for `external/*` branches, against the pattern
  `external/<type>-<ISSUE-KEY>-<segments>-p<N>`
  (`.github/workflows/validate-branch-name.yml:10`, `:14`, `:27`, `:31-36`).
- **PRs for publishable files.** Edits to `standard/**`, `conformance/**`, `docs/**`,
  or `README.md` require a pull request. Changes must pass `opa check` and `opa test`;
  run them locally, because no workflow in this repository runs them (see "What CI runs"
  under `## Key commands`).
- **PR target.** Contributor and agent pull requests target `dev`. Changes are promoted
  to `main` through `dev` → `qa` → `main`: the `validate-branch-tier` workflow accepts PRs into
  `main` only from `qa/**`, into `qa` only from `dev/**`, and into `dev` from `external/**`,
  `dependabot/**`, or any branch opened by a CODEOWNER
  (`.github/workflows/validate-branch-tier.yml:10-13`, `:51-53`, `:67`).
- **Policy integrity.** After editing `conformance/laas/laas.rego`, run
  `opa check conformance/laas/laas.rego conformance/laas/laas_test.rego` and
  `opa test conformance/laas/ -v` to confirm the policy still passes before committing.
- **Never delete a file** without explicit maintainer permission.
- **Semver discipline.** Every policy or spec change updates `CHANGELOG.md`.
- **Cite precisely.** Internal references use `file:line`;
  external references use a full bibliographic citation.

Full detail: [`docs/agents/conventions.md`](docs/agents/conventions.md).

## Open questions

Surface these when proposing amendments — do not silently assume an answer.

1. **OSI `custom_extension` schema versioning.** `scripts/laas/osi/kellerai_laas_extension.schema.json`
   is informally versioned; no formal change-control process exists yet.

## Tier-2 references — load on demand

- [`docs/agents/conventions.md`](docs/agents/conventions.md) — Conventional Commits,
  branch naming, PR style, citation format, the local gates and what CI runs, the Capability
  Roster (specialist plugins by domain), and shared agent scope and worktree rules.
- [`docs/agents/citation.md`](docs/agents/citation.md) — Apache-2.0 attribution,
  BibTeX, `CITATION.cff`.
- [`docs/agents/glossary.md`](docs/agents/glossary.md) — load-bearing vocabulary.
- [`docs/agents/enforcement.md`](docs/agents/enforcement.md) — automated gates,
  CODEOWNERS routing, pre-commit hook, policy integrity, the in-repo OPA packages.
