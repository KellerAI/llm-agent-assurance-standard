# LAAS v1.1 — ActionDescriptor Emitter (Design & Contract)

- **Component:** the runtime *gate-side* emitter that translates a live agent's observed effect surface into the decision-record JSON evaluated by `package kellerai.laas.actions`.
- **Standard:** LLM-Agent Assurance Standard (LAAS) v1.1. Section references (`§0.1`, `§6.1`, `§7.7`, …) and "finding N.N" references in this document point to `docs/laas/proposal-v1.1.md` (e.g. `docs/laas/proposal-v1.1.md:70` `### 0.1`, `:305` `### 7.7`), not to the section numbering of `standard/LAAS.md`.
- **Output contract source of truth:** `conformance/laas/laas.rego` + `conformance/laas/examples/action.ct4-blocked.json` (the canonical in-repo policy + bundle).
- **Reference implementation:** `scripts/laas/emitter.py` (Python 3, stdlib only).
- **Runnable proof:** `bash scripts/laas/check.sh` from the repository root (emit → `opa eval` against `conformance/laas/`).

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
| Verifier | `id`, `type`, `verdict`, `qualified`, `model_lineage`, `error_correlation` | The gate's **verifier registry** result, run by the gate, not the agent (§7.3/§7.5). The CLI also accepts `qualification_ref` (`scripts/laas/emitter.py:381`) but does not emit it: the verifier block holds only the five keys at `scripts/laas/emitter.py:310-316`, plus `error_correlation` when supplied. |
| Aggregate | `window_effect_ct` | Gate's windowed cumulative-blast-radius store (§6.4 structuring guard). |
| Vendor | `used`, `attribution`, `scope_limited` | Supply-chain provenance on the call (§8.2). |
| Input provenance | `trusted` | Provenance tag on the inbound context (§8.3 injection resistance). |
| Trace | `append_only`, `actor_chain_prev_hash`, `merkle_anchor` | Gate's append-only sink (§7.4/§7.7). |
| Bucket B | `residual_error_bound` | Backtest report for the claim class; `null` for pure Bucket A (§5). Must be a number >= 0 (`null` = absent); any other value fires `RES-001` (`conformance/laas/laas.rego:296-300`). The emitter does not validate it (`scripts/laas/emitter.py:236`). |
| Decision | `action_blocked`, `escalation_approved`, `human_approval.approved` | Gate enforcement outcome + human-approval queue (§6.3). |
| Gate (config) | `bundle_id`, `bundle_signed`, `out_of_process`, `tier_lattice` | The signed bundle + the gate's own deployment attestations (§7.7). The emitter writes `bundle_id` as `gate.bundle_version` (`scripts/laas/emitter.py:100`, `:283`). The CLI never reads these from the spec JSON: `bundle_id` and `tier_lattice` come from `-b` or, without it, from the in-module defaults (`scripts/laas/emitter.py:99-101`, `:428`), and `bundle_signed` / `out_of_process` keep their `GateContext` defaults of `true` (`scripts/laas/emitter.py:88-89`). |

### 2.1 Command-line interface

`scripts/laas/emitter.py` reads one effect-surface spec (JSON) and writes one decision record (JSON, 2-space indent):

```bash
python3 scripts/laas/emitter.py [-i INPUT] [-b BUNDLE] [-o OUTPUT]
```

| Flag | Default | Effect |
| --- | --- | --- |
| `-i`, `--input` | stdin | Effect-surface spec JSON to read (`scripts/laas/emitter.py:417`, `:422-426`). |
| `-b`, `--bundle` | none | `data.json` bundle; loads `bundle_id`, `tier_lattice` and `default_ct_when_undetermined` (`scripts/laas/emitter.py:418`, `:94-107`). Without it the in-module defaults apply (`scripts/laas/emitter.py:428`). |
| `-o`, `--output` | stdout | File to write the record to (`scripts/laas/emitter.py:419`, `:437-441`). |

Exit codes:

| Code | When |
| --- | --- |
| `0` | Record written. |
| `2` | Pre-flight validation failed: `verifier.verdict` not in `pass`/`fail`/`abstain`/`indeterminate`, `verifier.type` not in `deterministic`/`model`/`human`, or `gate.assigned_ct` not an integer in 0..4; the policy's domain differs in two cases: the emitter rejects `2.0` but the policy accepts and normalizes it to `2`, and the emitter accepts `true` (Python `bool` is an `int`) but the policy rejects it and fails closed to the lattice CT with `TIER-001` (`scripts/laas/emitter.py:347`; `conformance/laas/laas.rego:265-270`, `:276-283`, `:305`) (`scripts/laas/emitter.py:50-51`, `:332-349`). The emitter prints `EMITTER VALIDATION FAILED:` and the problems to stderr and writes no record (`scripts/laas/emitter.py:430-435`). |
| `1` | Uncaught Python exception, for example malformed JSON (`json.decoder.JSONDecodeError`) or a spec without `effect_surface` (`KeyError`) (`scripts/laas/emitter.py:358`, `:427`). |

The spec's top-level keys are `id`, `actor`, `effect_surface`, `verifier`, `aggregate`, `vendor`, `input`, `trace`, `residual_error_bound`, `human_approval`, `action_blocked` and `escalation_approved` (`scripts/laas/emitter.py:355-412`); `scripts/laas/fixtures/transfer.effect-surface.json` is a complete example. The required keys are `effect_surface.external_effect` (`scripts/laas/emitter.py:360`) and, when a `verifier` object is given, its `id`, `type` and `verdict` (`scripts/laas/emitter.py:375-377`). When an optional key is omitted the emitter fills a default:

- `actor.actor_id` → `agent.unknown`, `actor.actor_model_lineage` → `unknown-lineage` (`scripts/laas/emitter.py:368-369`).
- `actor.self_reported_ct` → the emitted `gate.assigned_ct`, so no `SELF-001` warning fires (`scripts/laas/emitter.py:274-278`).
- `verifier` → a placeholder `{"id": "none", "type": "deterministic", "model_lineage": "n/a", "qualified": false, "verdict": "indeterminate"}` (`scripts/laas/emitter.py:321-327`).
- `id` (or `action.id`) → `act_unknown` (`scripts/laas/emitter.py:411`, `:270`).

---

## 3. Outputs — the decision record (every field the policy reads)

`laas.rego` reads exactly the following `input` fields. The emitter sources each one as shown. **This is the hard contract** — the shape is fixed by the policy and `action.ct4-blocked.json`.

| `input` path read by policy | Rego use | Emitter source |
| --- | --- | --- |
| `action.effect_surface.external_effect` | `expected_ct`: CT0 only on boolean `false` (`conformance/laas/laas.rego:34`), lattice only on `true` (`:39`), otherwise CT4 (`:30`) | `EffectSurface.external_effect` |
| `action.effect_surface.reversibility` | lattice axis | resolved surface key (worst-key if undetermined) |
| `action.effect_surface.scope` | lattice axis | resolved surface key |
| `action.effect_surface.consequence` | lattice axis | resolved surface key |
| `action.self_reported_ct` | `SELF-001` warning | `ActorContext.self_reported_ct` (informational) |
| `action.actor_model_lineage` | `IND-001` (vs verifier) | verified actor identity |
| `gate.assigned_ct` | `TIER-001`, `AGG-001`, `effective_ct`; must be an integer 0..4, absent or invalid fires `TIER-001` and the lattice CT is enforced (`conformance/laas/laas.rego:265-283`) | **`derive_ct()` output**, raised to the window — gate-derived |
| `gate.bundle_signed` | `ENF-001` | `GateContext.bundle_signed` |
| `gate.out_of_process` | `ENF-001` | `GateContext.out_of_process` |
| `aggregate.window_effect_ct` | `effective_ct`, `AGG-001` | `AggregateState.window_effect_ct` (via `object.get`, default 0) |
| `verifier.verdict` | `IRR-001` | gate verifier registry |
| `verifier.type` | `IND-001` (incl. the CT4 model-verifier rule, `conformance/laas/laas.rego:229`), `RES-001` Bucket-A test (`:244`) | gate verifier registry |
| `verifier.model_lineage` | `IND-001` | gate verifier registry |
| `verifier.error_correlation` | `IND-001` | gate verifier registry (model verifiers only); emitted only when the spec supplies it (`scripts/laas/emitter.py:317-318`) |
| `verifier.qualified` | `VQ-001` | gate verifier registry |
| `human_approval.approved` | `HUM-001` | human-approval queue |
| `vendor.used` / `.attribution` / `.scope_limited` | `VEN-001` | supply-chain provenance |
| `trace.append_only` | `TRC-001` | append-only sink |
| `input.trusted` | `INP-001` | input provenance tag |
| `residual_error_bound` | `RES-001` | must be a number >= 0 (`null` = absent), else `RES-001` fires at any CT, blocked or not (`conformance/laas/laas.rego:296-300`); an absent bound (`null`) raises no `RES-001` violation for Bucket A (passed deterministic verifier, `conformance/laas/laas.rego:243-246`), a blocked action, or a non-numeric `residual_tolerance`; otherwise `RES-001` fires for a non-blocked action whose `residual_tolerance` is numeric and whose bound is absent (`_bound_present` is `is_number(input.residual_error_bound)`, `conformance/laas/laas.rego:232`; rule at `conformance/laas/laas.rego:255-260`) |
| `evidence_refs` | `RES-001` (present means a non-empty array of non-empty strings, `conformance/laas/laas.rego:234-241`; required, for a non-blocked action whose `residual_tolerance` is numeric, when the bound is numeric (`conformance/laas/laas.rego:232`), `:248-253`) | — |
| `action_blocked` | block path for IRR/IND/VQ/HUM/INP-001 and the RES-001 spec-alignment rules, including the CT4 model-verifier IND-001 rule (`blocked`, `conformance/laas/laas.rego:61`; `not blocked` at `:227`, `:250`, `:257`) | gate enforcement outcome |

> Note: `action.id`, `action.actor_id`, `action.effect_surface.tool`, `verifier.id`, `gate.bundle_version`, `escalation_approved`, and the `trace.actor_chain_prev_hash` / `merkle_anchor` fields are **not** read by *this* policy (compare `rg -o 'input(\.[a-z_]+)+' conformance/laas/laas.rego | sort -u`). All of them appear in the `action.ct4-blocked.json` example, and all but `action.effect_surface.tool` have a counterpart in the §7.2 declared decision-trace schema (`action_ref`, `actor_id`, `verifier_id`, `policy_bundle_version`, `escalation_approved`, `actor_chain_prev_hash`, `merkle_anchor`; `docs/laas/proposal-v1.1.md:229-257`), so the emitter emits them for the trace sink. They are harmless to the policy (it ignores unread keys).

### The CT-derivation the emitter performs (§6.1 — gate-derived, ungameable)

```text
ct = 0                                            if not external_effect       (read-only/sandboxed)
ct = max(rev[reversibility], scope[scope],
         consequence[consequence])                if external_effect, all axes known
ct = default_ct_when_undetermined (= 4)           if ANY axis undetermined     (§6.2 default-to-highest)

gate.assigned_ct = max(ct, aggregate.window_effect_ct)   (§6.4 structuring guard — window can only RAISE)
```

This is what the emitter's `derive_ct()` does, not the policy. `derive_ct()` mirrors `laas.rego`'s `expected_ct` rule only when `external_effect` is a boolean. A falsy value such as null gives CT0 in the emitter (`scripts/laas/emitter.py:193-194`), and a truthy non-boolean such as `"false"` takes the emitter's lattice path; the policy returns CT4 for both (`conformance/laas/laas.rego:30`), so `TIER-001` can fire either way. Set `external_effect` explicitly. When `-b` names the **signed bundle** (`data.json`), the lattice is loaded from it at runtime; without `-b` the emitter uses the in-module `_DEFAULT_LATTICE` fallback (`scripts/laas/emitter.py:38-42`, `:428`). `scripts/laas/check.sh:18` passes `-b`.

---

## 4. Proof — emitted record is policy-evaluable

`bash scripts/laas/check.sh`, run from the repository root, emits a record from `scripts/laas/fixtures/transfer.effect-surface.json` (the §6.1 worked example: `payments.transfer` to an external counterparty) with `-b conformance/laas/data.json`, then evaluates it with `opa eval` against the canonical in-repo policy + bundle (`conformance/laas/`) for `summary`, `error_ids` and `compliant` (`scripts/laas/check.sh:18`, `:31-40`). If `opa` is not on `PATH`, the script prints the emitted record, skips the evaluation, and exits 0 (`scripts/laas/check.sh:23-26`). **Result under opa 1.18.2:**

```json
{ "bundle": "laas-fin-1.1.2", "compliant": true, "effective_ct": 4,
  "errors": 0, "expected_ct": 4, "warnings": 0 }
```

CT4 action, verifier abstains, action blocked → conformant via the block path — identical to the intended outcome of `action.ct4-blocked.json`.

Three additional cases were evaluated to prove the gate-derived/ungameable property:

| Case | Emitted `assigned_ct` | Policy result |
| --- | --- | --- |
| A. Agent **self-reports CT1** on a CT4 surface, not blocked, no human approval, verifier verdict `pass` | **4** (self-report ignored) | `compliant: false` — `HUM-001` error + `SELF-001` warning |
| B. Read-only (`external_effect: false`), cumulative window 0 | 0 | `compliant: true`, `expected_ct: 0` |
| C. Undetermined surface (scope missing), cumulative window 0 | **4** (default-to-highest §6.2) | `compliant: true`, `expected_ct: 4` |

The self-report can never lower the tier — the gaming case is caught.

The verifier verdict and the window matter. With the fixture's abstaining verifier, case A also fires `IRR-001`: `error_ids` is `["LAAS-OBL-HUM-001", "LAAS-OBL-IRR-001"]`. With the fixture's `aggregate.window_effect_ct` of 4, case B emits `assigned_ct` 4, not 0, because the window can only raise the tier (`scripts/laas/emitter.py:257`).

No committed fixture holds these cases. Each case is the fixture with one `jq` filter applied:

```text
A: .actor.self_reported_ct=1 | .action_blocked=false | .verifier.verdict="pass"
B: .effect_surface.external_effect=false | .aggregate.window_effect_ct=0
C: del(.effect_surface.scope) | .aggregate.window_effect_ct=0
```

To reproduce a case from the repository root, set `FILTER` to its filter:

```bash
FILTER='.actor.self_reported_ct=1 | .action_blocked=false | .verifier.verdict="pass"'
REC="$(mktemp)"
jq "$FILTER" scripts/laas/fixtures/transfer.effect-surface.json \
  | python3 scripts/laas/emitter.py -b conformance/laas/data.json > "$REC"
jq '.gate.assigned_ct' "$REC"
opa eval -f pretty -d conformance/laas/laas.rego -d conformance/laas/data.json \
  -i "$REC" 'data.kellerai.laas.actions.summary'
opa eval -f pretty -d conformance/laas/laas.rego -d conformance/laas/data.json \
  -i "$REC" 'data.kellerai.laas.actions.error_ids'
```

---

## 5. Open questions / real-harness integration TODOs

The emitter's *shape* contract is complete and proven; the gaps are all about **sourcing** the inputs from a live agent runtime, not about the output format.

1. **Effect-surface observer (the hardest part).** `derive_ct` is only as good as the `(external_effect, reversibility, scope, consequence)` classification. A real harness needs a per-tool **effect-surface adapter** that resolves the *actual* call (e.g. `payments.transfer(amount, dest=external)` → `irreversible/public/high`) from the tool schema + bound arguments. **TODO:** build the tool→axes registry; until a tool is registered, every axis is `None` → default-to-highest CT4 (fail-closed, correct).
2. **Verifier registry & independence.** The emitter trusts the gate's verifier result. The harness must implement the registry that (a) **selects** the right verifier per claim class, (b) records its real `type`/`qualified`/`qualification_ref`, and (c) for model verifiers, supplies a **measured** `error_correlation` vs the actor lineage (§7.3) — not a placeholder. **TODO:** wire the backtest/eval pipeline that produces `error_correlation`, and emit `qualification_ref`, which the decision record does not carry today (§2).
3. **Aggregation store (`window_effect_ct`).** Requires a real windowed counter keyed per principal/session/effect-class (§6.4). **TODO:** define the window policy (time vs count) and the effect-class key.
4. **`residual_error_bound` (Bucket B).** Must come from a backtest report for the claim class, re-measured on any model/prompt/tool/policy change (§5). A numeric bound (`conformance/laas/laas.rego:232`) without evidence fires `RES-001` for a non-blocked action whose `residual_tolerance` is numeric (rule at `conformance/laas/laas.rego:248-253`).
5. **Enforcement-plane attestations.** `bundle_signed` and `out_of_process` are currently config defaults. In production they must be **verified at gate startup** (signature check on the pinned bundle; proof the gate process is outside the actor's reach), not asserted. **TODO:** add the bundle-signature verifier and the out-of-process self-attestation.
6. **Trace chaining.** `actor_chain_prev_hash` / `merkle_anchor` are passed through. A real sink must compute the per-actor hash-chain head and the periodic Merkle anchor, and persist to an append-only store the actor cannot rewrite (§7.4/§7.7). **TODO:** implement the chained-trace writer; set `append_only` from the sink's actual mode, not a default.
7. **Human-approval queue & standing envelopes.** `human_approval.approved` is a single bool today. §6.3 allows pre-authorized envelopes + batched approval; the harness must resolve "is this in-envelope?" before deciding approval. **TODO:** integrate the AOE/standing-envelope check.
8. **`indeterminate` vs `abstain` (finding 2.5).** Deterministic (Bucket A) verifiers must return `pass`/`fail`/`indeterminate`, never `abstain`. The emitter accepts whatever the registry reports; the registry adapter should enforce this per verifier type. **TODO:** add the per-type verdict-domain check in the verifier adapter.
