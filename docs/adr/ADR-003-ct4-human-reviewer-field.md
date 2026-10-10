---
title: "ADR-003 — An attributable human at CT4: explicit human-reviewer evidence in the decision record"
status: Accepted
date: 2026-10-10
---

> Bead `laas-69c` (follow-up F5 from the `laas-yju` design). Status: Accepted (2026-10-10)
> for D1, D2, D3, and D5; D4, D6, and D7 remain open. This ADR changes no policy, test,
> script, or prose; implementation is follow-up work. Line cites are against `dev` at `eea2f44`.

## Context

**What the standard says.** §4.1 defines verifier independence by tier. A deterministic
checker is valid at any CT, a distinct and de-correlated model lineage is valid up to CT3,
and a human is "required *in addition* at CT4" (`standard/LAAS.md:85-89`). The CT4 regime
row and the obligation table separately require "human approval" (`standard/LAAS.md:57`,
`:81`). The governing invariant forbids trusting "a verifier's **soundness or independence**
without evidence" (`standard/LAAS.md:30`).

**What the policy checks.** Three rules carry the CT4 human today:

- `independence_ok` accepts any `input.verifier.type == "human"` (`conformance/laas/laas.rego:78`).
- HUM-001 fires at `human_approval_floor_ct` (4, `conformance/laas/data.json:13`) when the
  action is not blocked and `human_approved` is false (`conformance/laas/laas.rego:177-182`).
  `human_approved` reads one boolean, `input.human_approval.approved` (`laas.rego:67`).
- The SD-2 rule fires IND-001 for a passed model verifier at CT4 (`laas.rego:226-231`). The
  SD-2 ruling recorded that "the HUM-001 approval is the human in addition" (`CHANGELOG.md:23`).

The zero-tolerance gate also treats a passed human verifier plus that boolean as the human
gate (`_human_gated`, `laas.rego:325-329`; `standard/LAAS.md:110-112`).

**The gap.** The record never says *who* the human was:

1. `human_approval` is `{"approved": <bool>}` and nothing else (`scripts/laas/emitter.py:409`).
   The policy never reads `action.actor_id`; it appears only in two OSI test fixtures
   (`conformance/laas/laas_test.rego:260`, `:316`). So the policy cannot tell the approver
   from the actor.
2. `verifier.type == "human"` is a bare string with no identity or attestation
   (`laas.rego:78`). This is the unevidenced independence that `standard/LAAS.md:30` forbids.
3. With a human verifier, one unnamed person can act as both verifier and approver and
   still satisfy `_human_gated` (`laas.rego:325-329`). The design rationale cites "a two-person
   rule" (`docs/laas/proposal-v1.1.md:206`).

So `standard/LAAS.md:89` can be asserted in a record, but no rule can check it.

**Constraints.**

- Human approval "need not be per-action": standing pre-authorized envelopes and batched
  approval are part of the design (`docs/laas/proposal-v1.1.md:184`). The emitter already
  flags this as an open TODO (`docs/laas/emitter.md:194`). A per-action identity mandate
  without an envelope path would contradict §6.3.
- The decision record is flat. `verifier`, `human_approval`, and `trace` are top-level keys
  (`scripts/laas/emitter.py:389-448`); there is no `verification` container.
- The OSI `custom_extension` schema carries per-object governance axes only and sets
  `additionalProperties: false` (`scripts/laas/osi/kellerai_laas_extension.schema.json:7-30`).
  Per-action approval data does not belong there. What would break is the OSI proof, which
  patches in `{"approved": True}` (`scripts/laas/osi_check.sh:38`), and its policy test
  (`laas_test.rego:284-293`).
- Semver: a breaking contract change is major (`CONTRIBUTING.md:56`). `[Unreleased]` already
  carries an unreleased major, bundle `laas-fin-2.0.0` (`CHANGELOG.md:9-16`;
  `conformance/laas/data.json:3-4`); the only release is `0.1.0` (`CHANGELOG.md:63`).

## Considered options

| Option | Reading of LAAS.md:89 | Semver | Records that fail after |
| ------ | --------------------- | ------ | ----------------------- |
| A. New `human_review` object + new obligation | Second (human) verifier at CT4 | major | Every non-blocked compliant CT4 record |
| B. Attributed `human_approval` | The HUM-001 approver | major (minor if optional) | CT4 records with a bare boolean |
| C. Status quo + prose | The HUM-001 approver | patch | None |

A fourth option, a mandatory `human` verifier at CT4, was rejected. It would contradict
"valid at any CT for the deterministic class" (`standard/LAAS.md:87`) and the Bucket-A path
of the zero-tolerance rule (`standard/LAAS.md:111`).

### Option A — new top-level `human_review` object and obligation

```jsonc
"human_review": {
  "reviewer_id": "hr:jdoe",            // stable principal id, never the actor's
  "verdict": "pass",                   // pass | fail | abstain
  "reviewed_input_hash": "sha256:…",   // what the human saw
  "attestation_ref": "sig:…",          // gate-verified signature or ticket id
  "basis": "per_action"                // per_action | standing_envelope | batch
}
```

New `LAAS-OBL-HRV-001` (error, `ct_floor` 4): on a non-blocked CT4 action, require a
`human_review` with verdict `pass`, a non-empty `reviewer_id` different from
`action.actor_id`, and a non-empty `attestation_ref`. HUM-001 stays as it is.

- **Affected:** `laas.rego` (new rule; `_human_gated` re-keyed); `data.json` (new obligation
  in `obligations`, `data.json:19-32`, a `human_review_floor_ct` key, bundle id); tests
  (`_base_ct4`, `laas_test.rego:62-75`, referenced on 48 lines; the OSI fixtures; the expected counts
  `PASS: 96/96` and `PASS: 167/167`, `AGENTS.md:81-82`); emitter (new dataclass, `_check_spec`
  at `emitter.py:523`, `test_emitter.py`, `scripts/laas/fixtures/transfer.effect-surface.json`);
  `osi_check.sh:38` and `docs/laas/osi-adapter.md:296`; `standard/LAAS.md` (§3 row `:57`,
  §4 table `:68-81`, §4.1 `:89`, §5 predicate `:126-129`); the glossary's twelve-ID list,
  the four renderings, and `CHANGELOG.md`.
- **Pros:** most literal reading of the §4.1 placement; separates review from authorization.
- **Cons:** CT4 needs three human-facing artefacts (verifier, review, approval), and a
  per-action review defeats the §6.3 envelopes (`proposal-v1.1.md:184`) unless `basis` exempts
  it, which leaves review and approval nearly the same thing. Largest blast radius.
- **Impact/effort:** high impact, high effort.

### Option B — attribute the existing `human_approval` record (recommended)

```jsonc
"human_approval": {
  "approved": true,
  "approver_id": "hr:jdoe",            // required at CT4 when not blocked
  "attestation_ref": "sig:…",          // required: signature, ticket, or envelope grant id
  "basis": "per_action",               // per_action | standing_envelope | batch
  "envelope_id": null                  // required when basis = standing_envelope
}
```

HUM-001 gains checks on a non-blocked CT4 action: `approved == true`; a non-empty string
`approver_id` that differs from `action.actor_id`; a non-empty `attestation_ref`; a `basis` in
the enum; and `envelope_id` when the basis is an envelope. When `verifier.type == "human"`,
`approver_id` must also differ from `verifier.id`, which gives the two-person rule. Whether a
signature is valid is checked by the gate and asserted in the record, the same way
`gate.bundle_signed` is (`laas.rego:115-118`).

- **Affected:** `laas.rego` (`human_approved` at `:67`, HUM-001 at `:177-182`, and
  `_human_gated` at `:325-329` if it should require the attributed form); `data.json`
  (bundle id; optionally an `approval_basis` enum; no new obligation id); tests
  (`_base_ct4` and the OSI fixtures gain the fields; new negative tests; counts in
  `AGENTS.md:81-82`); emitter (`human_approved: bool` at `emitter.py:352` and `:608` becomes
  a structured value; `:409`; `_check_spec`; `test_emitter.py`; the fixture
  `transfer.effect-surface.json:24`; the blocked example `conformance/laas/examples/action.ct4-blocked.json:29`
  stays valid because blocked actions skip HUM-001); `osi_check.sh:38` and `osi-adapter.md:296`;
  `standard/LAAS.md:57`, `:81`, `:89`; `conformance/laas/README.md:75`, `docs/laas/emitter.md:112`,
  `docs/agents/glossary.md:44`, and the renderings; `CHANGELOG.md`.
- **Pros:** makes `standard/LAAS.md:89` checkable without a new concept. Keeps the SD-2 ruling
  (`CHANGELOG.md:23`) and the §6.3 envelopes. No new obligation id, so the obligation tables
  keep their shape. Closes the same-person loophole in `_human_gated`.
- **Cons:** still breaking for every compliant CT4 record. The policy checks *attribution*,
  not humanity: a record field cannot prove a human acted. It makes the claim auditable under
  the §6 attestation (`standard/LAAS.md:133-135`).
- **Impact/effort:** high impact, medium effort.

### Option C — status quo plus prose

Amend `standard/LAAS.md:89` to read that the CT4 human is the `LAAS-OBL-HUM-001` approver,
recorded as `human_approval.approved`. Document in `conformance/laas/README.md:75` that the
policy does not check approver identity.

- **Affected:** `standard/LAAS.md:89`, `docs/agents/glossary.md:44`, `conformance/laas/README.md`,
  `CHANGELOG.md`. No policy, test, emitter, or OSI change.
- **Pros:** zero migration; codifies the SD-2 reading.
- **Cons:** accepts that §4.1's CT4 clause is unevidenced, in tension with `standard/LAAS.md:30`;
  leaves the same-person path in `_human_gated` open.
- **Impact/effort:** low impact, low effort.

## Decision

**Accepted: Option B**, the maintainer's ruling of 2026-10-10 (Jonathan). It turns the
existing SD-2 reading into a checkable rule at the lowest cost that still honours
`standard/LAAS.md:30`. A mixes review with authorization and breaks §6.3 envelopes; C leaves
the invariant gap open.

Rulings recorded:

- **D1 (reading): Option B.** Attribute the existing `LAAS-OBL-HUM-001` `human_approval`
  record with `approver_id`, `attestation_ref`, `basis`, and `envelope_id`. No new obligation id.
- **D2 (two-person rule): yes.** HUM-001 fails when `approver_id` equals `action.actor_id`, or
  equals `verifier.id` when the verifier is human.
- **D3 (required fields): required at CT4.** A non-blocked CT4 record that is missing
  `approver_id` fails closed.
- **D5 (release): fold into the unreleased `laas-fin-2.0.0` major.** No separate version bump.

Still open (no ruling; see "Decision questions for the maintainer"): D4, D6, D7.

## Consequences

**Easier.** An auditor can check from the record alone that a named principal, distinct from
the actor (and from a human verifier), approved each CT4 action or its envelope. The emitter
TODO at `docs/laas/emitter.md:194` gets a schema to target.

**Harder.** Every deployer emitting `{"approved": true}` at CT4 must migrate. Gates must
maintain a principal directory and verify attestations out of band. Risks: (1) placeholder
`approver_id` values defeat the check, so the gate must issue them; (2) an envelope basis
could become a blanket bypass unless envelope grants carry their own trace record; (3) if
`action.actor_id` is absent (it is absent from `_base_ct4`, `laas_test.rego:62-75`), the
distinctness test must fail closed, or it will pass vacuously.

**Follow-up for whoever implements.** One bead per mechanism: policy and tests; emitter; OSI
proof; prose and renderings. Each needs a semver-classified `CHANGELOG.md` entry, because
`conformance/**` and `docs/**` are frozen without one (`CLAUDE.md:26-27`).

### Decision questions for the maintainer

- **D1 (reading) — RULED 2026-10-10: Option B.** The CT4 human of `standard/LAAS.md:89` is the
  HUM-001 approver.
- **D2 (two-person rule) — RULED 2026-10-10: yes.** The approver must differ from the actor and
  from a human verifier. (Which field identifies the human verifier was not separately ruled;
  the ruling names `verifier.id`.)
- **D3 (required fields) — RULED 2026-10-10: required at CT4.** A non-blocked CT4 record
  missing `approver_id` fails closed. The ruling names `approver_id` only; whether
  `attestation_ref`, `basis`, and `envelope_id` are likewise required, and whether a missing
  `action.actor_id` fails closed, was not separately ruled.
- **D4 (envelopes) — OPEN.** Are `standing_envelope` and `batch` valid bases at CT4, and must an
  envelope grant be traced as its own record? Context: SD-12 interacts with this question.
  The operating-envelope text was removed from the standards by bead `laas-0mu`, so the
  `standing_envelope` and `envelope_id` basis values need re-examination before any ruling.
  This ADR does not decide D4.
- **D5 (release) — RULED 2026-10-10: unreleased `laas-fin-2.0.0` major.** No separate bump.
- **D6 (zero tolerance) — OPEN.** Must `_human_gated` (`laas.rego:325-329`) require the
  attributed approval, or only HUM-001?
- **D7 (OSI proof) — OPEN.** Should `osi_check.sh` add the attributed approval to its existing
  deterministic verifier (`scripts/laas/osi_to_surface.py:300-306`), or also exercise a human
  verifier?
