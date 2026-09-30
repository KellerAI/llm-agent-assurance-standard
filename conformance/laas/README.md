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
| `laas_test.rego` | `opa test` suite (19 cases: 12 obligation-specific, 3 pass/block/read-only, 4 OSI-adapter golden) |
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
# Syntax check + test suite (expect all green — currently 19/19 PASS)
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
| `action.effect_surface.external_effect` | `LAAS-OBL-TIER-001` | `false` → CT0 (no external effect); `true` → tier lattice fires |
| `action.effect_surface.reversibility` | `LAAS-OBL-TIER-001` | First axis of the lattice; `"irreversible"` maps to 4 |
| `action.effect_surface.scope` | `LAAS-OBL-TIER-001` | Second axis; `"public"` maps to 4 |
| `action.effect_surface.consequence` | `LAAS-OBL-TIER-001` | Third axis; `"high"` maps to 4 |
| `action.self_reported_ct` | `LAAS-OBL-SELF-001` (warning) | Self-reported tier must not be below the gate-assigned tier; the gate always prevails |
| `gate.assigned_ct` | `LAAS-OBL-TIER-001`, `LAAS-OBL-AGG-001` | Must be ≥ lattice-derived CT (TIER-001) and ≥ `aggregate.window_effect_ct` (AGG-001) |
| `gate.bundle_signed` | `LAAS-OBL-ENF-001` | Bundle signature — enforcement-plane integrity (v1.1 §7.7) |
| `gate.out_of_process` | `LAAS-OBL-ENF-001` | Gate isolation — enforcement-plane integrity (v1.1 §7.7) |
| `verifier.verdict` | `LAAS-OBL-IRR-001` | Must be `"pass"` for any CT≥3 action that is not blocked |
| `verifier.type` | `LAAS-OBL-IND-001` | Independence test: `"deterministic"` or `"human"` satisfies; `"model"` must differ in lineage and correlation |
| `verifier.qualified` | `LAAS-OBL-VQ-001` | Verifier must be qualified (DO-330 analogue, v1.1 §7.5) |
| `trace.append_only` | `LAAS-OBL-TRC-001` | Append-only chained decision trace (v1.1 §7.4) |
| `human_approval.approved` | `LAAS-OBL-HUM-001` | Human approval required at CT4 when not blocked |
| `aggregate.window_effect_ct` | `LAAS-OBL-AGG-001` | Cumulative blast-radius — `effective_ct` is the max of `assigned_ct` and this value |
| `input.trusted` | `LAAS-OBL-INP-001` | Untrusted input must raise the effective CT to ≥3 or the action must be blocked |
| `vendor.used` / `vendor.attribution` / `vendor.scope_limited` | `LAAS-OBL-VEN-001` | Third-party dependencies require attribution and a scope limit |
| `residual_error_bound` | `LAAS-OBL-RES-001` | Bucket-B residual escape rate; `null` means pure Bucket-A — the violation does not fire |
| `action_blocked` | bypass condition for `IRR-001`, `IND-001`, `VQ-001`, `HUM-001`, `INP-001` | Gate block signal (`blocked`, `laas.rego:61`); each of these rules requires `not blocked` (`laas.rego:157`, `:164`, `:172`, `:180`, `:145`), so a blocked action satisfies them via the block path |

`action.actor_model_lineage` and `verifier.model_lineage` feed `LAAS-OBL-IND-001` only when
`verifier.type == "model"`: `independence_ok` requires the two lineages to differ
(`laas.rego:82`), and the IND-001 rule fires on `not independence_ok` (`laas.rego:162-167`).

**Fields present in the example that `laas.rego` does not reference** (informational only):
`action.id`, `action.actor_id`, `action.effect_surface.tool`, `gate.bundle_version`,
`verifier.id`, `trace.actor_chain_prev_hash`, `trace.merkle_anchor`, and `escalation_approved`.
These fields are part of the record schema, but no rule in `laas.rego` reads them.

## CI wiring (proposed)

Not implemented: no workflow in this repository evaluates this policy. A future reusable
workflow could run `opa test` on this directory and `opa eval` against a stream or sample of
decision records, blocking on `error`-severity violations and reporting `warning`-severity ones.
Pin such a workflow to a commit SHA, not a branch.

In CI, this repository's workflows run the sanitization gate (`bash scripts/check-sanitization.sh`, in `ci.yml`) and invoke OPA only as `opa eval` (in the trust-dial gate workflow, and in the blast-radius pulse workflow via `scripts/pulse.sh`); `opa check`, `opa test`, the Python unit tests, `scripts/laas/check.sh`, and `scripts/laas/osi_check.sh` are local gates that no workflow in this repository's `.github/workflows/` runs, and what the external reusable conformance workflow called from `ci.yml` runs cannot be inspected from this repository.

Supporting lines: `.github/workflows/ci.yml:33-34` (sanitization gate),
`.github/workflows/ci.yml:37` (external conformance workflow),
`.github/workflows/trust-dial-gate.yml:113` (`opa eval`), and
`.github/workflows/blast-radius-pulse.yml:60` (`bash scripts/pulse.sh`, which runs `opa eval` at
`scripts/pulse.sh:242`).

> Re-verified on OPA 1.18.2 (2026-09-29): `opa check` and `opa test` (19/19 PASS). The
> conformance predicate references only declared trace fields, so it is mechanically evaluable —
> see `standard/LAAS.md` §5.
