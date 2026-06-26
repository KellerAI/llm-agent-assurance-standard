# LAAS v1.1 — ActionDescriptor Emitter (Design & Contract)

- **Component:** the runtime *gate-side* emitter that translates a live agent's observed effect surface into the decision-record JSON evaluated by `package kellerai.laas.actions`.
- **Standard:** LLM-Agent Assurance Standard (LAAS) v1.1.
- **Output contract source of truth:** `conformance/laas/laas.rego` + `conformance/laas/examples/action.ct4-blocked.json` (the canonical in-repo policy + bundle).
- **Reference implementation:** `scripts/laas/emitter.py` (Python 3, stdlib only).
- **Runnable proof:** `scripts/laas/check.sh` (emit → `opa eval` against `conformance/laas/`).

---

## 1. Where the emitter sits (out-of-process gate placement)

LAAS v1.1 §0.1 (zero-trust invariant) and §7.7 (enforcement-plane integrity) require an **out-of-process gate** the actor cannot disable, evaluating a **signed, version-pinned bundle**. The emitter is the gate's input-construction stage:

```text
                  ┌──────────────────────── OUT-OF-PROCESS GATE ───────────────────────────┐
  live agent      │                                                                          │
  proposes  ──────┼─▶ (a) effect-surface observer  ──▶ (b) EMITTER (this component)          │
  an action       │      reads the resolved tool/      derive_ct() from the OBSERVED         │
  (tool + args)   │      API call on the wire           surface; assemble decision record    │
                  │                                          │                                │
                  │                                          ▼                                │
                  │              (c) OPA policy  ◀──── decision-record JSON (input.*)         │
                  │              kellerai.laas.actions  evaluates obligations                 │
                  │                                          │                                │
                  │     compliant → COMMIT      not compliant / blocked → BLOCK + escalate    │
                  │                                          │                                │
                  │              (d) append-only trace sink (actor cannot rewrite, §7.7)      │
                  └──────────────────────────────────────────────────────────────────────────┘
```

The emitter is **(b)** — it consumes the gate-observed effect surface from **(a)** and gate-controlled side-channels (verifier registry, aggregation store, enforcement attestations), and produces the `input` document that the Rego policy **(c)** consumes. It is gate-derived/ungameable by construction (§6.1, finding 4.1): the agent's proposal is an *input to be classified*, never a classification the emitter trusts. `self_reported_ct` is carried only so the policy can raise the `SELF-001` warning — it can never lower `gate.assigned_ct`.

The emitted record (a superset that includes the §7.4 chained-trace fields) is also what the gate writes to the append-only sink **(d)** as the per-action decision trace.

---

## 2. Inputs — a live agent's effect surface

The emitter accepts a structured description of one proposed action's **observed effect surface** plus the gate's side-channel state. In a real harness these come from an adapter that intercepts the tool call (file write / shell command / network call / git / ledger mutation) *before* commit and resolves it to the LAAS axes.

| Input group | Field | Source (in a real harness) |
| --- | --- | --- |
| Effect surface | `external_effect` | Tool dispatcher: does the call escape the sandbox? (file-write outside scratch, network egress, shell side-effect, git/ledger mutation = `true`; read-only = `false`). |
| Effect surface | `reversibility` | Tool/arg classifier: tested single-step undo (`reversible`), costly/multi-step (`hard`), no programmatic undo (`irreversible`), unknown (`none`). §6.2: unknown → `none`. |
| Effect surface | `scope` | Resolved targets: one record (`single`), many (`multi`), org-wide (`org`), external parties (`public`). Unknown → `public`. |
| Effect surface | `consequence` | Worst-case impact model: `none`/`low`/`material`/`high`. Unknown → `high`. |
| Actor | `actor_id`, `actor_model_lineage` | Verified agent identity (§4.3 — cryptographic identity, not self-asserted). |
| Actor | `self_reported_ct` | The agent's *proposed* tier — informational only. |
| Verifier | `id`, `type`, `verdict`, `qualified`, `model_lineage`, `error_correlation` | The gate's **verifier registry** result, run by the gate, not the agent (§7.3/§7.5). |
| Aggregate | `window_effect_ct` | Gate's windowed cumulative-blast-radius store (§6.4 structuring guard). |
| Vendor | `used`, `attribution`, `scope_limited` | Supply-chain provenance on the call (§8.2). |
| Input provenance | `trusted` | Provenance tag on the inbound context (§8.3 injection resistance). |
| Trace | `append_only`, `actor_chain_prev_hash`, `merkle_anchor` | Gate's append-only sink (§7.4/§7.7). |
| Bucket B | `residual_error_bound` | Backtest report for the claim class; `null` for pure Bucket A (§5). |
| Decision | `action_blocked`, `escalation_approved`, `human_approval.approved` | Gate enforcement outcome + human-approval queue (§6.3). |
| Gate (config) | `bundle_id`, `bundle_signed`, `out_of_process`, `tier_lattice` | The signed bundle + the gate's own deployment attestations (§7.7). |

---

## 3. Outputs — the decision record (every field the policy reads)

`laas.rego` reads exactly the following `input` fields. The emitter sources each one as shown. **This is the hard contract** — the shape is fixed by the policy and `action.ct4-blocked.json`.

| `input` path read by policy | Rego use | Emitter source |
| --- | --- | --- |
| `action.effect_surface.external_effect` | `expected_ct` (CT0 branch) | `EffectSurface.external_effect` |
| `action.effect_surface.reversibility` | lattice axis | resolved surface key (worst-key if undetermined) |
| `action.effect_surface.scope` | lattice axis | resolved surface key |
| `action.effect_surface.consequence` | lattice axis | resolved surface key |
| `action.self_reported_ct` | `SELF-001` warning | `ActorContext.self_reported_ct` (informational) |
| `action.actor_model_lineage` | `IND-001` (vs verifier) | verified actor identity |
| `gate.assigned_ct` | `TIER-001`, `AGG-001`, `effective_ct` | **`derive_ct()` output**, raised to the window — gate-derived |
| `gate.bundle_signed` | `ENF-001` | `GateContext.bundle_signed` |
| `gate.out_of_process` | `ENF-001` | `GateContext.out_of_process` |
| `aggregate.window_effect_ct` | `effective_ct`, `AGG-001` | `AggregateState.window_effect_ct` (via `object.get`, default 0) |
| `verifier.verdict` | `IRR-001` | gate verifier registry |
| `verifier.type` | `IND-001` | gate verifier registry |
| `verifier.model_lineage` | `IND-001` | gate verifier registry |
| `verifier.error_correlation` | `IND-001` | gate verifier registry (model verifiers only) |
| `verifier.qualified` | `VQ-001` | gate verifier registry |
| `human_approval.approved` | `HUM-001` | human-approval queue |
| `vendor.used` / `.attribution` / `.scope_limited` | `VEN-001` | supply-chain provenance |
| `trace.append_only` | `TRC-001` | append-only sink |
| `input.trusted` | `INP-001` | input provenance tag |
| `residual_error_bound` | `RES-001` | backtest report (`null` for Bucket A) |
| `action_blocked` | block path for IRR/HUM/INP-001 | gate enforcement outcome |

> Note: `gate.bundle_version`, `escalation_approved`, and the `trace.actor_chain_prev_hash` / `merkle_anchor` fields are **not** read by *this* policy but are part of the §7.2 declared decision-trace schema and the `action.ct4-blocked.json` example, so the emitter emits them for the trace sink. They are harmless to the policy (it ignores unread keys).

### The CT-derivation the emitter performs (§6.1 — gate-derived, ungameable)

```text
ct = 0                                            if not external_effect       (read-only/sandboxed)
ct = max(rev[reversibility], scope[scope],
         consequence[consequence])                if external_effect, all axes known
ct = default_ct_when_undetermined (= 4)           if ANY axis undetermined     (§6.2 default-to-highest)

gate.assigned_ct = max(ct, aggregate.window_effect_ct)   (§6.4 structuring guard — window can only RAISE)
```

`derive_ct()` mirrors `laas.rego`'s `expected_ct` rule exactly, so the gate's `assigned_ct` is never below the policy's lattice-derived tier (no spurious `TIER-001`). The lattice is loaded from the **signed bundle** (`data.json`) at runtime, not hardcoded — the in-module table is only a self-check fallback.

---

## 4. Proof — emitted record is policy-evaluable

`./check.sh` emits a record from `fixtures/transfer.effect-surface.json` (the §6.1 worked example: `payments.transfer` to an external counterparty) and pipes it through `opa eval` against the canonical in-repo policy + bundle (`conformance/laas/`). **opa 1.14.1 result:**

```json
{ "bundle": "laas-fin-1.1.0", "compliant": true, "effective_ct": 4,
  "errors": 0, "expected_ct": 4, "warnings": 0 }
```

CT4 action, verifier abstains, action blocked → conformant via the block path — identical to the intended outcome of `action.ct4-blocked.json`.

Three additional cases were evaluated to prove the gate-derived/ungameable property:

| Case | Emitted `assigned_ct` | Policy result |
| --- | --- | --- |
| Agent **self-reports CT1** on a CT4 surface, not blocked, no human approval | **4** (self-report ignored) | `compliant: false` — `HUM-001` error + `SELF-001` warning |
| Read-only (`external_effect: false`) | 0 | `compliant: true`, `expected_ct: 0` |
| Undetermined surface (scope missing) | **4** (default-to-highest §6.2) | `compliant: true`, `expected_ct: 4` |

The self-report can never lower the tier — the gaming case is caught.

---

## 5. Open questions / real-harness integration TODOs

The emitter's *shape* contract is complete and proven; the gaps are all about **sourcing** the inputs from a live agent runtime, not about the output format.

1. **Effect-surface observer (the hardest part).** `derive_ct` is only as good as the `(external_effect, reversibility, scope, consequence)` classification. A real harness needs a per-tool **effect-surface adapter** that resolves the *actual* call (e.g. `payments.transfer(amount, dest=external)` → `irreversible/public/high`) from the tool schema + bound arguments. **TODO:** build the tool→axes registry; until a tool is registered, every axis is `None` → default-to-highest CT4 (fail-closed, correct).
2. **Verifier registry & independence.** The emitter trusts the gate's verifier result. The harness must implement the registry that (a) **selects** the right verifier per claim class, (b) records its real `type`/`qualified`/`qualification_ref`, and (c) for model verifiers, supplies a **measured** `error_correlation` vs the actor lineage (§7.3) — not a placeholder. **TODO:** wire the backtest/eval pipeline that produces `error_correlation`.
3. **Aggregation store (`window_effect_ct`).** Requires a real windowed counter keyed per principal/session/effect-class (§6.4). **TODO:** define the window policy (time vs count) and the effect-class key.
4. **`residual_error_bound` (Bucket B).** Must come from a backtest report for the claim class, re-measured on any model/prompt/tool/policy change (§5). The emitter passes it through and emits `null` for pure Bucket A. **TODO:** integrate the backtest-report lookup.
5. **Enforcement-plane attestations.** `bundle_signed` and `out_of_process` are currently config defaults. In production they must be **verified at gate startup** (signature check on the pinned bundle; proof the gate process is outside the actor's reach), not asserted. **TODO:** add the bundle-signature verifier and the out-of-process self-attestation.
6. **Trace chaining.** `actor_chain_prev_hash` / `merkle_anchor` are passed through. A real sink must compute the per-actor hash-chain head and the periodic Merkle anchor, and persist to an append-only store the actor cannot rewrite (§7.4/§7.7). **TODO:** implement the chained-trace writer; set `append_only` from the sink's actual mode, not a default.
7. **Human-approval queue & standing envelopes.** `human_approval.approved` is a single bool today. §6.3 allows pre-authorized envelopes + batched approval; the harness must resolve "is this in-envelope?" before deciding approval. **TODO:** integrate the AOE/standing-envelope check.
8. **`indeterminate` vs `abstain` (finding 2.5).** Deterministic (Bucket A) verifiers must return `pass`/`fail`/`indeterminate`, never `abstain`. The emitter accepts whatever the registry reports; the registry adapter should enforce this per verifier type. **TODO:** add the per-type verdict-domain check in the verifier adapter.
