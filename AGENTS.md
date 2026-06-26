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
- **Repo-structure conformance**: [`conformance/`](conformance/) — OPA policy
  `kellerai.oss.conformance` validates this repo's own file and directory structure.
- Licensed **Apache-2.0** — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## What this repo is NOT

- There is **no application runtime** — no package, no build output, no API to import.
  `scripts/laas/` scripts are reference tooling and proof scripts, not production libraries.
- There is **no in-repo issue tracker**. Work is tracked in GitHub Issues.
- The only verification commands are `opa check` and `opa test`. See `## Key commands`.

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
| Architecture decision records | `docs/adr/` |
| Article bibliography | `docs/articles/index.md` |
| Repo-structure conformance rules | `conformance/` |
| What a term means | `docs/agents/glossary.md` |
| Commit, branch, PR rules | `docs/agents/conventions.md` |
| How conventions are enforced | `docs/agents/enforcement.md` |
| How to cite this repo | `docs/agents/citation.md` |

## Key commands

```bash
# LAAS policy: syntax check + test suite (expect: 19/19 PASS)
opa check conformance/laas/laas.rego conformance/laas/laas_test.rego
opa test conformance/laas/ -v

# Evaluate a decision record
opa eval -d conformance/laas/laas.rego -d conformance/laas/data.json \
  -i conformance/laas/examples/action.ct4-blocked.json \
  'data.kellerai.laas.actions.summary' --format pretty

# End-to-end proof (emitter → opa eval)
bash scripts/laas/check.sh
```

## Conventions agents MUST follow

- **Default branch is `main`.** Never create or use `master`.
- **Conventional Commits.** `<type>(<scope>): <subject>` — subject ≤ 50 chars,
  imperative mood. Types: `feat`, `fix`, `chore`, `docs`, `refactor`.
  Scope recommended: `standard`, `conformance`, `scripts`, `docs`.
- **Branch naming.** Agent work uses `<agent>/<scope>` — e.g.
  `claude/fix-typo`, `codex/clarify-field`. Human work uses
  `feat/*`, `fix/*`, `docs/*`, `chore/*`.
- **PRs for publishable files.** Edits to `standard/**`, `conformance/**`, `docs/**`,
  or `README.md` require a pull request. Changes must pass `opa check` and `opa test`.
- **Policy integrity.** After editing `conformance/laas/laas.rego`, run
  `opa check conformance/laas/laas.rego conformance/laas/laas_test.rego` and
  `opa test conformance/laas/ -v` to confirm the policy still passes before committing.
- **Never delete a file** without explicit maintainer permission.
- **Semver discipline.** Every policy or spec change updates `CHANGELOG.md`.
- **Cite precisely.** Internal references use `file:line`;
  external references use a full bibliographic citation.

Full detail: [`docs/agents/conventions.md`](docs/agents/conventions.md).

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

## Open questions

Surface these when proposing amendments — do not silently assume an answer.

1. **OSI `custom_extension` schema versioning.** `scripts/laas/osi/kellerai_laas_extension.schema.json`
   is informally versioned; no formal change-control process exists yet.

## Tier-2 references — load on demand

- [`docs/agents/conventions.md`](docs/agents/conventions.md) — Conventional Commits,
  branch naming, PR style, citation format, the `opa` workflow.
- [`docs/agents/citation.md`](docs/agents/citation.md) — Apache-2.0 attribution,
  BibTeX, `CITATION.cff`.
- [`docs/agents/glossary.md`](docs/agents/glossary.md) — load-bearing vocabulary.
- [`docs/agents/enforcement.md`](docs/agents/enforcement.md) — automated gates,
  CODEOWNERS routing, pre-commit hook, policy integrity.
