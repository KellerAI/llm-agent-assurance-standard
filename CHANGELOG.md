# Changelog

All notable changes to **llm-agent-assurance-standard** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-25

### Added

- Normative standard `standard/LAAS.md` — LLM-Agent Assurance Standard v1.1.
- OPA conformance policy `conformance/laas/laas.rego` with test suite (`laas_test.rego`), data manifest (`data.json`), and CT4 example action (`examples/action.ct4-blocked.json`).
- Standards renderings for IEEE, NIST, ISO, and SR formats under `docs/laas/standards/`, with a house-styled PDF build pipeline under `docs/laas/standards/pdf/` (per-format CSS themes and cover pages).
- LAAS reference tooling under `scripts/laas/`: emitter, backtest harness, OSI `custom_extension` schema, OSI→LaaS surface converter with tests, and `check`/`osi_check` proof scripts.
- LAAS prose documentation under `docs/laas/`: proposal, steelman, backtest report, and emitter guide.
- Annotated bibliography of 25 AI-agent assurance references at `docs/articles/index.md`.
- Agent-facing structure: `AGENTS.md`, `CLAUDE.md`, and `docs/agents/`.
- New `docs/laas/osi-adapter.md` documenting the OSI-to-surface converter (`scripts/laas/osi_to_surface.py`), its CLI, the custom-extension schema, and the `osi_check.sh` end-to-end proof.
- New `conformance/README.md` documenting the top-level repo-structure policies (`trust_dial`, `blast_radius`).
- `README.md` and `AGENTS.md` file-layout tables now list `docs/adr/`, `docs/articles/`, and the `docs/laas/` design docs.
- New "Anatomy of a decision record" section in `conformance/laas/README.md` mapping example fields to obligation families.
- Added the SR (Federal Reserve supervisory-guidance) rendering row to the PDF build source table in `docs/laas/standards/pdf/README.md`.

### Changed

- Set repository home to `KellerAI/llm-agent-assurance-standard` (organizational ownership); identity URLs, owner fields, and citation metadata updated accordingly.
- Corrected LAAS `opa test` count in documentation from 15 to 19 cases to match `conformance/laas/laas_test.rego`.

### Fixed

- Replaced the inaccurate "recompute the SHA-256 digest" policy-integrity step in `AGENTS.md` (no digest field exists in `data.json`) with the real `opa check` / `opa test` verification commands.
- Corrected the LAAS test-suite count from 15 to 19 in `README.md` and clarified the case breakdown in `conformance/laas/README.md` (12 obligation-specific + 3 pass/block/read-only + 4 OSI-adapter golden).
- Repointed broken `DEMO.md` references in `docs/laas/backtest.md` to the real `backtest-demo.md`; clarified that `evidence_ct{2,3,4}.json` are generated, not committed.
- Documented the previously-undocumented `error_ids` public output in the `conformance/laas/laas.rego` header comment.
- Corrected `MD049` emphasis style in `docs/laas/backtest.md` (underscore → asterisk) so the Markdown-lint CI gate passes.
- Replaced a dead external link in `docs/laas/osi-adapter.md` with plain text; excluded the bot-blocked IEC `electropedia.org` URL from link-checking in `.github/workflows/ci.yml`.
