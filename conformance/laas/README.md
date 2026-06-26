# LAAS conformance policy — quick reference

Machine-checkable conformance for **LLM-agent actions**. Companion to the repo's
`conformance/` policy (which checks repo *structure*); this one checks agent *actions* at
runtime. Normative prose: [`standard/LAAS.md`](../../standard/LAAS.md).

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
| `action_blocked` | bypass condition for `IRR-001`, `HUM-001` | Gate block signal; satisfies verification and human-approval obligations via the block path |

**Fields present in the example that are not evaluated by any violation rule** (informational
only): `action.id`, `action.actor_id`, `action.actor_model_lineage` (used for IND-001 lineage
comparison only when `verifier.type == "model"`), `gate.bundle_version`, `verifier.id`,
`verifier.model_lineage` (same conditional use), `trace.actor_chain_prev_hash`,
`trace.merkle_anchor`, and `escalation_approved`. These fields are part of the record schema
but `laas.rego` does not reference them in any `violations` rule.

## CI wiring (proposed)

A reusable workflow mirroring `.github/workflows/conformance.yml` runs `opa test` on this
directory and `opa eval` against a stream/sample of decision records. `error`-severity
violations block; `warning`-severity are reported. Pin to a commit SHA, not a branch.

> Verified on OPA 1.17.1. The conformance predicate references only declared trace fields, so it
> is mechanically evaluable — see `standard/LAAS.md` §5.
