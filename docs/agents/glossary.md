# Glossary

Tier-2 detail for [`../../AGENTS.md`](../../AGENTS.md).
The load-bearing vocabulary for **llm-agent-assurance-standard**.

This glossary is a fast index, not the authoritative definition source.
The authoritative definition for any term is the artifact file that introduces it.

## Artifact types

This repository publishes two artifact types: `markdown-spec` (normative) and `rego-policy` (enforcing) (`standard/LAAS.md:3`).

- **`markdown-spec`** — the normative artifact type.
  The normative specification lives under `standard/`: [`../../standard/LAAS.md`](../../standard/LAAS.md).
- **`rego-policy`** — the enforcing artifact type, and the `artifact_type` recorded in `.kellerai-oss.json` (`.kellerai-oss.json:2`).
  The primary validator is `opa` (`.kellerai-oss.json:4`).
  The artifact lives under `conformance/` (`.kellerai-oss.json:3`).

## LAAS terms

An index of the specification's core vocabulary.
Each definition quotes or closely paraphrases `standard/LAAS.md`, which is authoritative.
Cites into `conformance/laas/` show where the policy implements a term; they add no meaning.

- **Consequence Tier (CT0–CT4)** — the tier the gate assigns to every action, "computed from the **observed effect surface** — never from the agent's self-report" (`standard/LAAS.md:37-38`).
  CT numbers rise with consequence (`standard/LAAS.md:38-39`).
  The normative minimum regime for each tier is the tier table (`standard/LAAS.md:51-57`).
- **Observed effect surface** — the action's effect as the gate observes it, rated on three axes: reversibility, scope, and consequence (`standard/LAAS.md:42`, `:47-48`).
  An external effect gets `ct = max( reversibility_rank, scope_rank, consequence_rank )`; a read-only or sandboxed action gets `ct = 0`; any undetermined axis gets `ct = 4` (default-to-highest) (`standard/LAAS.md:42-44`).
  Ranks are defined in `data.json → tier_lattice` (`standard/LAAS.md:47`; `conformance/laas/data.json:6-10`).
  The policy reads the surface from `input.action.effect_surface` (`conformance/laas/laas.rego:34`, `:39-43`).
- **Gate** — the component that assigns the Consequence Tier from the observed effect surface, not from the agent (`standard/LAAS.md:37-38`).
  The policy header states: "The gate -- not the agent -- supplies the observed effect surface and the assigned tier" (`conformance/laas/laas.rego:6-7`).
  `LAAS-OBL-ENF-001` requires an out-of-process gate (`standard/LAAS.md:72`).
- **Governing invariant** — Zero-Trust applied to the model's outputs and to the apparatus around them (`standard/LAAS.md:26`).
  "A conforming system MUST NOT trust" the agent's self-classification of its own action, a verifier's soundness or independence without evidence, or the integrity of the enforcement plane (`standard/LAAS.md:26-31`).
  "Any control that lets the constrained party tier, grade, or gate itself is non-conforming" (`standard/LAAS.md:33`).
- **Effective tier / cumulative window** — "The cumulative effect of a sequence MUST be tiered too: if a windowed aggregate crosses a threshold, subsequent actions are re-tiered to the aggregate's tier (anti-structuring)" (`standard/LAAS.md:59-60`).
  The policy rule `effective_ct` takes the higher of the gate-assigned tier and the window aggregate's tier (`conformance/laas/laas.rego:47-48`).
- **Obligation** — an entry in the authoritative, versioned list in `data.json → obligations`, carrying an ID, severity, CT floor, precedence, and a reference to its rationale (`standard/LAAS.md:64-65`).
  `error`-severity violations are blocking; `warning`-severity violations are reported (`standard/LAAS.md:65-66`).
  The 12 obligation IDs are listed under [Obligation IDs](#obligation-ids).
- **Verifier independence** — "A verifier is independent of the actor iff one holds, by tier" (`standard/LAAS.md:85`): a different kind of checker (deterministic/exact), valid at any CT for the deterministic class; a distinct model lineage with measured error-correlation ≤ `max_error_correlation`, valid up to CT3; or a human, required in addition at CT4 (`standard/LAAS.md:87-89`).
  "A verifier sharing the actor's model lineage is presumed non-independent" (`standard/LAAS.md:91`).
  The policy rule is `independence_ok` (`conformance/laas/laas.rego:76-84`).
  At CT4 a separate rule rejects any passed model verifier (`conformance/laas/laas.rego:225-230`).
- **Verifier qualification** — "A verifier gating CT≥3 MUST be qualified: documented coverage of its claim class, a negative-test suite of known-bad inputs it must catch, and a change-controlled version recorded in the trace" (`standard/LAAS.md:95-96`).
- **Escape rate** — the residual undetected-error rate of the open-world ("Bucket B") class (`standard/LAAS.md:100-101`).
  The operator declares a maximum escape rate per CT, estimates it by backtesting on a held-out adversarial set, and re-measures it on any model, prompt, tool, or policy change; conformance requires measured escape rate ≤ tolerance, with evidence referenced in the trace (`standard/LAAS.md:100-103`).
  The tolerances are `escape_rate_tolerance_by_ct` (`conformance/laas/data.json:15`).
- **Bucket B / Bucket A** — Bucket B is the open-world class whose escape rate is bounded (`standard/LAAS.md:100`).
  `standard/LAAS.md` does not define Bucket A.
  The policy treats an action whose deterministic verifier passed as Bucket A (`conformance/laas/laas.rego:243-246`).
  At CT≥2 a non-blocked action that is not Bucket A and has no numeric `residual_error_bound` violates RES-001 (`conformance/laas/laas.rego:255-260`); on a non-blocked CT≥2 action, a numeric bound without non-empty `evidence_refs` also violates it (`conformance/laas/laas.rego:248-253`).
- **Decision trace** — each gated action emits one decision-trace record, written to an append-only, content-addressed store the actor cannot rewrite (`standard/LAAS.md:107-110`).
- **Decision record** — the policy's `input`: one gate-produced decision record, evaluated against the obligation bundle (`conformance/laas/laas.rego:5-6`).
- **Conformance predicate** — "If an obligation's trigger matched, then either the action **passed** an independent, qualified verifier (plus human approval at CT4, plus residual ≤ tolerance) **or** the action was **blocked** and escalated. Nothing else conforms." (`standard/LAAS.md:115-117`).
- **`kellerai.laas.actions`** — the package of the LAAS policy (`conformance/laas/laas.rego:19`).
  Its declared entry points are `violations`, `summary`, `compliant`, and `error_ids` (`conformance/laas/laas.rego:10-14`).
  The in-repo OPA packages are `kellerai.laas.actions` (the LAAS agent-action policy in `conformance/laas/`) and two verdict policies in `conformance/`: `kellerai.oss.trust_dial` (the Dependabot trust-dial verdict policy) and `kellerai.oss.blast_radius` (the blast-radius pulse verdict policy); this repository has no `kellerai.oss.conformance` package, and the repo-structure check is run by the external reusable conformance workflow that `ci.yml` calls.
  Sources: `.github/workflows/ci.yml:37` (the external workflow call) and `.github/workflows/conformance.yml:4-5`.
- **Trust dial** — the "trust-dial Dependabot auto-merge verdict policy" (`conformance/trust_dial.rego:2`), package `kellerai.oss.trust_dial` (`conformance/trust_dial.rego:21`).
  Its tiers are `Observed`, `Assisted`, `Supervised`, and `Trusted` (`conformance/trust_dial_data.json:3`).
- **Blast-radius pulse** — the "blast-radius pulse verdict policy" (`conformance/blast_radius.rego:2`), package `kellerai.oss.blast_radius` (`conformance/blast_radius.rego:15`).
- **Affects manifest** — `conformance/affects.json`, the "Blast-radius pulse affects manifest" (`conformance/affects.json:4`).
  Its entries are under the `affects` key (`conformance/affects.json:13`).

### Obligation IDs

Obligation wording is from `standard/LAAS.md:70-81`; IDs, severities, and CT floors match `conformance/laas/data.json:20-31` row for row.

| ID | Obligation | Severity | CT floor |
|----|------------|----------|----------|
| `LAAS-OBL-TIER-001` | Tier is gate-derived from the observed effect surface | error | 0 |
| `LAAS-OBL-SELF-001` | A self-reported tier may not lower the gate tier | warning | 0 |
| `LAAS-OBL-ENF-001` | Enforcement-plane integrity: signed bundle + out-of-process gate | error | 0 |
| `LAAS-OBL-TRC-001` | Append-only, chained decision trace | error | 0 |
| `LAAS-OBL-AGG-001` | Cumulative blast-radius aggregation / re-tiering | error | 0 |
| `LAAS-OBL-INP-001` | Untrusted input raises the tier or blocks | error | 0 |
| `LAAS-OBL-VEN-001` | Third-party / vendor attribution and scope limits | error | 0 |
| `LAAS-OBL-IRR-001` | Independent pre-commit verification for CT≥3 | error | 3 |
| `LAAS-OBL-IND-001` | Verifier independence + low error-correlation | error | 3 |
| `LAAS-OBL-VQ-001` | Verifier qualification (DO-330 analogue) | error | 3 |
| `LAAS-OBL-RES-001` | Bounded residual escape rate (Bucket B) | error | 2 |
| `LAAS-OBL-HUM-001` | Human approval required at CT4 | error | 4 |

## Repository structure terms

- **Tier 1** — the lightweight agent entry point: `AGENTS.md` and `CLAUDE.md`.
  These files are a table of contents. For in-depth detail, follow the pointers to Tier 2.
- **Tier 2** — deep reference files under `docs/agents/`:
  `conventions.md`, `citation.md`, `glossary.md`, `enforcement.md`.
- **Publishable tree** — every file not matched by `.gitignore`.
  The boundary is the source of truth for what ships.
- **Staging file** — any file matched by `.gitignore`.
  Staging files may be edited directly, without a PR.
- **Tier (disambiguation)** — "tier" has four unrelated meanings in this repository:
  the documentation tiers Tier 1 and Tier 2 above;
  the Consequence Tier CT0–CT4 of an agent action (`standard/LAAS.md:35-37`; see [LAAS terms](#laas-terms));
  the trust-dial tiers `Observed`, `Assisted`, `Supervised`, and `Trusted` (`conformance/trust_dial_data.json:3`);
  and the branch tiers of what `validate-branch-tier.yml` calls the "4-tier merge model" (`.github/workflows/validate-branch-tier.yml:10`); the rules it enforces are under "Branch tiers" in [`conventions.md`](conventions.md).

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

## Interpretability and internal-state terms

Advisory, non-normative terms from the J-space annex, [`../laas/j-space-internal-state-annex.md`](../laas/j-space-internal-state-annex.md).
"The paper" below is Gurnee et al. (Anthropic), "Verbalizable Representations Form a Global Workspace in Language Models," Transformer Circuits, 2026 (`docs/laas/j-space-internal-state-annex.md:198`).
The annex, like the paper, addresses access consciousness only (`docs/laas/j-space-internal-state-annex.md:7-8`).

- **Global workspace** — the paper's account of a workspace shared across the model's residual stream through which verbalizable representations are broadcast for report, reasoning, and behavioral modulation, addressing access consciousness only.
- **J-space** — this repository's shorthand for the global-workspace content identified in the paper: verbalizable internal representations broadcast for report and reasoning, with no claim about phenomenal experience.
- **J-lens** — the paper's interpretability probe that reads J-space content from a model's activations, requiring weights and activation access and functioning as an incomplete, single-token-limited detector.
- **Internal-state (assurance sense)** — model-internal signals (e.g. J-space content) that a white-box probe can surface but that may be absent from a model's verbalized output, relevant to assurance because a model's self-report cannot be assumed to reflect them.
- **Access consciousness** — functional reportability, directed modulation, and a representation's causal role in reasoning, as distinct from and silent on phenomenal consciousness or subjective experience.

## Add terms here

As the artifact grows, add load-bearing vocabulary to this file.
Every change that introduces a new term MUST add a glossary entry in the same pull request.
