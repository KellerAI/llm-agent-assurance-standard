# Glossary

Tier-2 detail for [`../../AGENTS.md`](../../AGENTS.md).
The load-bearing vocabulary for **llm-agent-assurance-standard**.

This glossary is a fast index, not the authoritative definition source.
The authoritative definition for any term is the artifact file that introduces it.

## Artifact types

- **`rego-policy`** — the artifact type this repository publishes.
  The primary validator is `opa`.
  The artifact lives under `conformance/`.

## Repository structure terms

- **Tier 1** — the lightweight agent entry point: `AGENTS.md` and `CLAUDE.md`.
  These files are a table of contents. For in-depth detail, follow the pointers to Tier 2.
- **Tier 2** — deep reference files under `docs/agents/`:
  `conventions.md`, `citation.md`, `glossary.md`, `enforcement.md`.
- **Publishable tree** — every file not matched by `.gitignore`.
  The boundary is the source of truth for what ships.
- **Staging file** — any file matched by `.gitignore`.
  Staging files may be edited directly, without a PR.

## Controlled-language terms

- **Controlled language** — a natural language restricted to a fixed set of writing rules
  and a fixed dictionary, so that a sentence admits one reading.
  In this repository it constrains the free-text fields of a decision-trace record.
  See [`../laas/profiles/ste-core.md`](../laas/profiles/ste-core.md).
- **STE profile** — an industry-specific controlled-language module under
  [`../laas/profiles/`](../laas/profiles/), adapted from ASD-STE100 principles.
  A profile is informative: it defines no obligation, no Consequence Tier, and no threshold.
- **Approved term** — a noun or verb listed in a profile's section 3 with exactly one
  meaning and one part of speech. The markdown table is authoritative; the JSON file under
  `docs/laas/profiles/glossary/` is derived from it.
- **Forbidden term** — a word a profile excludes because it is ambiguous in that domain.
  Every forbidden term carries a required replacement.
- **Language conformance level** — how thoroughly a record was checked against its profile:
  `LC-0` unchecked, `LC-1` self-declared, `LC-2` tool-checked, `LC-3` tool-checked plus
  independent review of the free-text fields.

## Contribution terms

- **Conventional Commits** — the commit message convention enforced by `commitlint`.
  Format: `<type>(<scope>): <subject>`.
  See [`conventions.md`](conventions.md).
- **Semver** — Semantic Versioning applied to the artifact.
  `major` = breaking; `minor` = additive; `patch` = editorial.

## Add terms here

As the artifact grows, add load-bearing vocabulary to this file.
Every change that introduces a new term MUST add a glossary entry in the same pull request.
