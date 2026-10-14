# LAAS conformance policy — quick reference

Machine-checkable conformance for **LLM-agent actions**: this policy checks agent *actions* at
runtime. It is distinct from the two verdict policies in [`conformance/`](../README.md), which
govern this repository's own automation. Normative prose: [`standard/LAAS.md`](../../standard/LAAS.md).

The in-repo OPA packages are `kellerai.laas.actions` (the LAAS agent-action policy in `conformance/laas/`) and two verdict policies in `conformance/`: `kellerai.oss.trust_dial` (the Dependabot trust-dial verdict policy) and `kellerai.oss.blast_radius` (the blast-radius pulse verdict policy); this repository has no `kellerai.oss.conformance` package, and the repo-structure check is run by the external reusable conformance workflow that `ci.yml` calls.

Package declarations: `conformance/laas/laas.rego:19`, `conformance/trust_dial.rego:21`,
`conformance/blast_radius.rego:15`. The external workflow call is `.github/workflows/ci.yml:37`
(see `.github/workflows/conformance.yml:4-5`).

## Files

| File | Role |
|------|------|
| `data.json` | Single source of truth — obligation bundle, tier lattice, tolerances, floors |
| `laas.rego` | Policy — package `kellerai.laas.actions` |
| `laas_test.rego` | `opa test` suite (123 cases: 12 obligation-specific, 3 pass/block/read-only, 4 OSI-adapter golden, 25 spec-alignment for SD-1 to SD-3, 18 for gate-tier validity (R1/R2), 9 for residual-bound validity (R3/R3a), 9 for integral-float gate tier and any-CT bound validity (R2a/R3c), 4 for integral-float window ct (R2b), 12 zero-tolerance (`test_zt_*` in the laas-o4c section), 5 for the undetermined-tier default (laas-ddo: `test_ddo_*`), 22 attributed human approval (laas-69c: 19 `test_hum_*`, plus `test_zt_same_person_bound_compared`, `test_zt_bare_approval_bound_compared`, `test_osi_ct4_bare_approval_noncompliant`)) |
| `examples/action.ct4-blocked.json` | Sample decision record for `opa eval` |

## Input

The policy evaluates **one gate-produced decision record** — the agent's observed effect
surface, the gate's assigned tier, the verifier and its verdict, the enforcement-plane flags,
and the trace fields. The **gate** supplies the effect surface and tier; the agent's
`self_reported_ct` is informational and can never lower the tier. See
`examples/action.ct4-blocked.json` for the shape.

## Entry points

```text
data.kellerai.laas.actions.summary     # {bundle, expected_ct, effective_ct, errors, warnings, compliant}
data.kellerai.laas.actions.violations  # set of {obligation, severity, msg}
data.kellerai.laas.actions.error_ids   # set of error-severity obligation IDs
data.kellerai.laas.actions.compliant   # bool — true iff zero error-severity violations
```

## Run it

```bash
# Syntax check + test suite (expect all green — currently 123/123 PASS)
opa check laas.rego laas_test.rego
opa test . -v

# Evaluate a decision record against the bundle
opa eval -d laas.rego -d data.json \
  -i examples/action.ct4-blocked.json \
  'data.kellerai.laas.actions.summary' --format pretty
```

The bundled example is a **CT4 external transfer the gate blocked** (verifier abstained) — it is
conformant via the block path (`compliant: true`). Flip `"bundle_signed": true` to `false` in the
input and re-run to see `LAAS-OBL-ENF-001` fire and `compliant` drop to `false`.

## Anatomy of a decision record

The table below maps every key field in `examples/action.ct4-blocked.json` to the
obligation or rule in `laas.rego` that consumes it.

| Field path | Obligation ID | What the policy checks |
|---|---|---|
| `action.effect_surface.external_effect` | `LAAS-OBL-TIER-001` | Boolean `false` → CT0 (`laas.rego:34`); `true` → tier lattice (`laas.rego:39`); absent, `null`, or non-boolean (e.g. `"false"`) → `default_ct_when_undetermined` (CT4, `data.json:11`; absent or not an integer in 0..4 → CT4 fail-closed; `laas.rego:30`, `laas.rego:366-374`) |
| `action.effect_surface.reversibility` | `LAAS-OBL-TIER-001` | First axis of the lattice; `"irreversible"` maps to 4 |
| `action.effect_surface.scope` | `LAAS-OBL-TIER-001` | Second axis; `"public"` maps to 4 |
| `action.effect_surface.consequence` | `LAAS-OBL-TIER-001` | Third axis; `"high"` maps to 4 |
| `action.self_reported_ct` | `LAAS-OBL-SELF-001` (warning) | Self-reported tier must not be below the gate tier (`gate.assigned_ct`, or the lattice CT when that is absent or invalid); the gate always prevails (`laas.rego:109-111`) |
| `gate.assigned_ct` | `LAAS-OBL-TIER-001`, `LAAS-OBL-AGG-001`, `effective_ct` | Must be an integer 0..4; absent or invalid raises TIER-001 and the lattice CT is enforced (`laas.rego:263-284`). A valid value must be ≥ lattice-derived CT (TIER-001, `laas.rego:103`) and ≥ `aggregate.window_effect_ct` (AGG-001, `laas.rego:135`) |
| `gate.bundle_signed` | `LAAS-OBL-ENF-001` | Bundle signature — enforcement-plane integrity (v1.1 §7.7) |
| `gate.out_of_process` | `LAAS-OBL-ENF-001` | Gate isolation — enforcement-plane integrity (v1.1 §7.7) |
| `verifier.verdict` | `LAAS-OBL-IRR-001` | Must be `"pass"` for any CT≥3 action that is not blocked |
| `verifier.type` | `LAAS-OBL-IND-001` | Independence test: `"deterministic"` or `"human"` satisfies; `"model"` must differ in lineage and correlation. A passed `"model"` verifier is never independent at CT4: on a non-blocked CT4 action it fires IND-001 (`laas.rego:226-231`) |
| `verifier.qualified` | `LAAS-OBL-VQ-001` | Verifier must be qualified (DO-330 analogue, v1.1 §7.5) |
| `trace.append_only` | `LAAS-OBL-TRC-001` | Append-only chained decision trace (v1.1 §7.4) |
| `human_approval` (`approved`, `approver_id`, `attestation_ref`, `basis`), `action.actor_id`, `verifier.id` | `LAAS-OBL-HUM-001` | An attributed approval is required at CT4 when not blocked (`laas.rego:67`, `:178`). All four fields are required: `approved` is boolean `true`; `approver_id` and `attestation_ref` are non-empty strings; `basis` is a member of `human_approval_bases` (currently `["per_action"]`, `data.json:33`) (`laas.rego:396-402`). Two-person rule: `approver_id` must differ from `action.actor_id` (`laas.rego:404`), and, only when `verifier.type == "human"`, from `verifier.id` (`laas.rego:408-416`). Comparison is exact string equality. Fails closed: a missing or empty `action.actor_id` (`laas.rego:403`), a human verifier with a missing or empty `id` (`laas.rego:414`), or a missing or non-array `human_approval_bases` (`laas.rego:401`) denies the approval. A bare `{"approved": true}` no longer satisfies HUM-001 |
| `aggregate.window_effect_ct` | `LAAS-OBL-AGG-001` | Cumulative blast-radius — `effective_ct` is the max of the gate tier (`assigned_ct`, or the lattice CT if absent or invalid) and this value (`laas.rego:48`) |
| `input.trusted` | `LAAS-OBL-INP-001` | Untrusted input must raise the effective CT to ≥3 or the action must be blocked |
| `vendor.used` / `vendor.attribution` / `vendor.scope_limited` | `LAAS-OBL-VEN-001` | Third-party dependencies require attribution and a scope limit |
| `residual_error_bound` | `LAAS-OBL-RES-001` | Fires if the bound is present, not `null`, and not a number ≥ 0 (`null` = absent); this fires at any CT, blocked or not, and an invalid bound is never compared to tolerance (`laas.rego:286-301`). Otherwise fires if above the tier's tolerance (`laas.rego:185-194`), except that at a zero tolerance (CT4 by default) the comparison is skipped for Bucket-A or human-gated actions (`laas.rego:331-346`). At a zero tolerance it also fires on a non-blocked, non-Bucket-A action whose bound is exactly 0, because a finite-sample bound is greater than 0 (`laas.rego:318-356`). At CT≥2 on a non-blocked action it also fires if the bound is numeric without non-empty `evidence_refs` (`laas.rego:249-254`), or if it is absent or `null` and the action is not Bucket A, i.e. has no passed deterministic verifier (`laas.rego:256-261`) |
| `evidence_refs` (not in the blocked example) | `LAAS-OBL-RES-001` | Non-empty array of non-empty strings; required at CT≥2 on a non-blocked action when `residual_error_bound` is numeric (`laas.rego:235-242`, `:249-254`) |
| `action_blocked` | bypass condition for `IRR-001`, `IND-001`, `VQ-001`, `HUM-001`, `INP-001`, `RES-001` (spec-alignment rules) | Gate block signal (`blocked`, `laas.rego:61`); each of these rules requires `not blocked` (`laas.rego:157`, `:164`, `:172`, `:180`, `:145`, `:228`, `:251`, `:258`, `:353`), so a blocked action satisfies them via the block path |

`action.actor_model_lineage` and `verifier.model_lineage` feed `LAAS-OBL-IND-001` only when
`verifier.type == "model"`: `independence_ok` requires the two lineages to differ
(`laas.rego:82`), and the IND-001 rule fires only when the effective CT is at or above the
independent-verification floor, the action is not blocked, the verifier passed, and
`independence_ok` does not hold (`laas.rego:63`, `:65`, `:162-167`).
At CT4 a second IND-001 rule fires for any non-blocked action with a passed model verifier,
regardless of lineage or correlation (`laas.rego:226-231`).

**Fields present in the example that `laas.rego` does not reference** (informational only):
`action.id`, `action.effect_surface.tool`, `gate.bundle_version`,
`trace.actor_chain_prev_hash`, `trace.merkle_anchor`, and `escalation_approved`.
These fields are part of the record schema, but no rule in `laas.rego` reads them.

## CI wiring

CI runs `opa check` and `opa test` on this directory, and evaluates two sample decision
records with `opa eval` through `scripts/laas/check.sh` and `scripts/laas/osi_check.sh`
(`.github/workflows/ci.yml:49-144`).

Not implemented: no workflow evaluates a stream or sample of real decision records from a
deployed gate. A future reusable workflow could do that, blocking on `error`-severity
violations and reporting `warning`-severity ones. Pin such a workflow to a commit SHA, not a
branch. The full list of CI gates, with sources, is in `docs/agents/conventions.md`
("Local gates").

> Re-verified on OPA 1.18.2 (2026-10-12): `opa check` and `opa test` (123/123 PASS). The
> conformance predicate references only declared trace fields, so it is mechanically evaluable —
> see `standard/LAAS.md` §5.
