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
| Effect surface | `external_effect` | Tool dispatcher: does the call escape the sandbox? (file-write outside scratch, network egress, shell side-effect, git/ledger mutation = `true`; read-only = `false`). Must be a JSON boolean: any other value is undetermined and gets CT4 (`scripts/laas/emitter.py:319-322`). |
| Effect surface | `reversibility` | Tool/arg classifier: tested single-step undo (`reversible`), costly/multi-step (`hard`), no programmatic undo (`irreversible`), unknown (`none`). §6.2: unknown → `none`. |
| Effect surface | `scope` | Resolved targets: one record (`single`), many (`multi`), org-wide (`org`), external parties (`public`). Unknown → `public`. |
| Effect surface | `consequence` | Worst-case impact model: `none`/`low`/`material`/`high`. Unknown → `high`. |
| Actor | `actor_id`, `actor_model_lineage` | Verified agent identity (§4.3 — cryptographic identity, not self-asserted). |
| Actor | `self_reported_ct` | The agent's *proposed* tier — informational only. |
| Verifier | `id`, `type`, `verdict`, `qualified`, `model_lineage`, `error_correlation` | The gate's **verifier registry** result, run by the gate, not the agent (§7.3/§7.5). The CLI also accepts `qualification_ref` (`scripts/laas/emitter.py:658`) but does not emit it: the verifier block holds only the five keys at `scripts/laas/emitter.py:477-483`, plus `error_correlation` when supplied. |
| Aggregate | `window_effect_ct` | Gate's windowed cumulative-blast-radius store (§6.4 structuring guard). |
| Vendor | `used`, `attribution`, `scope_limited` | Supply-chain provenance on the call (§8.2). |
| Input provenance | `trusted` | Provenance tag on the inbound context (§8.3 injection resistance). |
| Trace | `append_only`, `actor_chain_prev_hash`, `merkle_anchor` | Gate's append-only sink (§7.4/§7.7). |
| Bucket B | `residual_error_bound` | Backtest report for the claim class; `null` for pure Bucket A (§5). Must be a number >= 0 (`null` = absent); any other value fires `RES-001` (`conformance/laas/laas.rego:297-301`). At a zero tolerance (CT4 by default), a bound of exactly 0 on a non-blocked, non-Bucket-A action also fires `RES-001` (`conformance/laas/laas.rego:348-356`). The emitter does not validate it (`scripts/laas/emitter.py:387`). |
| Bucket B | `evidence_refs` | References to the backtest report or other evidence for the bound, such as the backtest harness's `evidence_id` (`docs/laas/backtest.md:156`). Must be a JSON array of strings; any other type, or an element that is not a string, is an input error (exit 2, `scripts/laas/emitter.py:618-628`). `null` or an absent key means none supplied: the emitter then writes no `evidence_refs` key and never invents one. `[]` and `[""]` are passed through unchanged, because the policy, not the emitter, decides whether the refs satisfy `RES-001` (`conformance/laas/laas.rego:235-242`). |
| Decision | `action_blocked`, `escalation_approved` | Gate enforcement outcome (§6.3). |
| Decision | `human_approval` (`approved`, `approver_id`, `attestation_ref`, `basis`) | The deployment's human-approval queue, never the actor (§6.3). Must be a JSON object; each of the four members, when present, must be a JSON scalar, else exit 2 with `human_approval.<k> must be a JSON scalar` (`scripts/laas/emitter.py:596-599`). `approved` defaults to `false` and is always emitted; each attribution field is emitted only when supplied, never fabricated (`scripts/laas/emitter.py:420-425`, `:667-678`). The emitter does not check the `basis` enum or the attribution; HUM-001 does (§3). In the Python API, `emit_decision_record` takes `human_approval: Optional[HumanApproval]` (`scripts/laas/emitter.py:221-235`, `:382`) in place of the former `human_approved: bool`. |
| Gate (config) | `bundle_id`, `bundle_signed`, `out_of_process`, `tier_lattice` | The signed bundle + the gate's own deployment attestations (§7.7). The emitter writes `bundle_id` as `gate.bundle_version` (`scripts/laas/emitter.py:182`, `:443`). The CLI never reads these from the spec JSON: `bundle_id` and `tier_lattice` come from `-b` or, without it, from the in-module defaults (`scripts/laas/emitter.py:181-183`, `:721`), and `bundle_signed` / `out_of_process` keep their `GateContext` defaults of `true` (`scripts/laas/emitter.py:149-150`). |

### 2.1 Command-line interface

`scripts/laas/emitter.py` reads one effect-surface spec (JSON) and writes one decision record (JSON, 2-space indent):

```bash
python3 scripts/laas/emitter.py [-i INPUT] [-b BUNDLE] [-o OUTPUT]
```

| Flag | Default | Effect |
| --- | --- | --- |
| `-i`, `--input` | stdin | Effect-surface spec JSON to read (`scripts/laas/emitter.py:714`, `:552-556`). |
| `-b`, `--bundle` | none | `data.json` bundle; loads `bundle_id`, `tier_lattice` and `default_ct_when_undetermined` (`scripts/laas/emitter.py:715`, `:156-190`). Only the top level, `laas` and the presence of `laas.tier_lattice` are checked at load (`_check_bundle`, `scripts/laas/emitter.py:105-111`); the lattice shape and values and `default_ct_when_undetermined` are checked in `derive_ct` only when reached (`scripts/laas/emitter.py:281-288`, `:324-328`, `:338`, `:343-346`, `:354-358`). Without it the in-module defaults apply (`scripts/laas/emitter.py:721`). |
| `-o`, `--output` | stdout | File to write the record to (`scripts/laas/emitter.py:716`, `:734`, `:744-748`). |

Exit codes:

| Code | When |
| --- | --- |
| `0` | Record written. |
| `2` | Pre-flight validation failed: `verifier.verdict` not in `pass`/`fail`/`abstain`/`indeterminate`, `verifier.type` not in `deterministic`/`model`/`human`, or `gate.assigned_ct` not an integer in 0..4; the policy's domain differs in two cases: the emitter rejects `2.0` but the policy accepts and normalizes it to `2`, and the emitter accepts `true` (Python `bool` is an `int`) but the policy rejects it and fails closed to the lattice CT with `TIER-001` (`scripts/laas/emitter.py:514`; `conformance/laas/laas.rego:266-271`, `:277-284`, `:306`) (`scripts/laas/emitter.py:50-51`, `:499-516`). The emitter prints `EMITTER VALIDATION FAILED:` and the problems to stderr and writes no record (`scripts/laas/emitter.py:727-732`). |
| `2` | Bad input, reported as one stderr line `EMITTER INPUT ERROR: ...` with nothing on stdout. Most of these inputs crashed the original emitter with a traceback. Not all did: a non-numeric `aggregate.window_effect_ct` made the original print `EMITTER VALIDATION FAILED:` instead, and Jonathan accepted the change to this line. Two handlers write this line. The main one covers spec and bundle errors, which `_read_spec`, `_check_spec`, `GateContext.from_bundle` and `derive_ct` raise as `EmitterInputError` (cited below) and `main` handles at `scripts/laas/emitter.py:724-726`. The second covers a spec value so deeply nested that serialising the record fails (`RecursionError` in `json.dumps`), reported as `spec <src>: too deeply nested to serialise the record` (`:733-743`). Spec (`-i` or stdin): unreadable or missing file, not UTF-8, invalid or too deeply nested JSON, or an integer literal over 4300 digits, which `_int_digit_error` reports as invalid JSON (`:552-566`, helper `:61-69`); a top level that is not an object, a missing or non-object `effect_surface`, a missing `external_effect`, an axis that is an array or object when the effect is truthy, a non-object `actor`/`aggregate`/`vendor`/`input`/`trace`/`human_approval`/`action`, a truthy `verifier` that is not an object, lacks `id`/`type`/`verdict` or has a non-scalar `type`/`verdict`, a non-numeric `aggregate.window_effect_ct`, or an `evidence_refs` that is neither `null` nor an array of strings (`_check_spec`, `:569-629`). Bundle (`-b`): unreadable, not UTF-8, invalid or too deeply nested JSON, or an integer literal over 4300 digits (`:164-177`); a top level that is not an object, or a missing or non-object `laas`, or a missing `laas.tier_lattice` (`_check_bundle`, `:105-111`). At point of use in `derive_ct`, only when reached: a lattice or axis that is not an object, an absent axis or §6.2 worst key, a non-numeric `default_ct_when_undetermined` on an undetermined return (an undetermined axis or a non-boolean `external_effect`), or a non-numeric lattice value (`:281-288`, `:324-328`, `:338`, `:343-346`, `:354-358`). The one-line `EMITTER INPUT ERROR:` contract covers these input errors only. Argparse usage errors did not crash the original emitter and keep argparse's own unprefixed two-line stderr output (usage line plus error line); they also exit 2. |
| `1` | Uncaught Python exception. The only remaining input is an unwritable `-o` path (`OSError` from `open` at `scripts/laas/emitter.py:745`; a directory path fails the same way); the output side is outside the input checks. A missing `effect_surface` and an unreadable `-i` file now exit 2. |

The spec's top-level keys are `id`, `actor`, `effect_surface`, `verifier`, `aggregate`, `vendor`, `input`, `trace`, `residual_error_bound`, `evidence_refs`, `human_approval`, `action_blocked` and `escalation_approved` (`scripts/laas/emitter.py:632-696`); `scripts/laas/fixtures/transfer.effect-surface.json` is a complete example. The required keys are the `effect_surface` object, `effect_surface.external_effect` (`scripts/laas/emitter.py:583-587`, read at `:637`) and, when a truthy `verifier` is given, its `id`, `type` and `verdict` (`scripts/laas/emitter.py:613-615`, read at `:652-654`). When an optional key is omitted the emitter fills a default:

- `actor.actor_id` → `agent.unknown`, `actor.actor_model_lineage` → `unknown-lineage` (`scripts/laas/emitter.py:645-646`).
- `actor.self_reported_ct` → the emitted `gate.assigned_ct`, so no `SELF-001` warning fires (`scripts/laas/emitter.py:434-438`).
- `verifier` → a placeholder `{"id": "none", "type": "deterministic", "model_lineage": "n/a", "qualified": false, "verdict": "indeterminate"}` (`scripts/laas/emitter.py:488-494`).
- `id` (or `action.id`) → `act_unknown` (`scripts/laas/emitter.py:695`, `:430`).
- `evidence_refs` → no default: the record has no `evidence_refs` key (`scripts/laas/emitter.py:467-471`).

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
| `gate.assigned_ct` | `TIER-001`, `AGG-001`, `effective_ct`; must be an integer 0..4, absent or invalid fires `TIER-001` and the lattice CT is enforced (`conformance/laas/laas.rego:266-284`) | **`derive_ct()` output**, raised to the window — gate-derived |
| `gate.bundle_signed` | `ENF-001` | `GateContext.bundle_signed` |
| `gate.out_of_process` | `ENF-001` | `GateContext.out_of_process` |
| `aggregate.window_effect_ct` | `effective_ct`, `AGG-001` | `AggregateState.window_effect_ct` (via `object.get`, default 0) |
| `verifier.verdict` | `IRR-001` | gate verifier registry |
| `verifier.type` | `IND-001` (incl. the CT4 model-verifier rule, `conformance/laas/laas.rego:230`), `RES-001` Bucket-A test (`:245`); `human` with a passing verdict and an attributed human approval (`human_approved`, `conformance/laas/laas.rego:67`) also feeds the zero-tolerance human-gated skip (`:325-339`) | gate verifier registry |
| `verifier.model_lineage` | `IND-001` | gate verifier registry |
| `verifier.error_correlation` | `IND-001` | gate verifier registry (model verifiers only); emitted only when the spec supplies it (`scripts/laas/emitter.py:484-485`) |
| `verifier.qualified` | `VQ-001` | gate verifier registry |
| `human_approval.approved` / `.approver_id` / `.attestation_ref` / `.basis` | `HUM-001`: a bare `approved: true` does not satisfy it. The approval must have `approved` boolean `true`, non-empty string `approver_id` and `attestation_ref`, and a `basis` in `data.laas.human_approval_bases` (only `per_action`, `conformance/laas/data.json:33`); `approver_id` must differ from a non-empty `action.actor_id` and, for a `human` verifier, from a non-empty `verifier.id` (`conformance/laas/laas.rego:67`, `:178-182`, `:396-416`) | human-approval queue; attribution fields emitted only when supplied |
| `vendor.used` / `.attribution` / `.scope_limited` | `VEN-001` | supply-chain provenance |
| `trace.append_only` | `TRC-001` | append-only sink |
| `input.trusted` | `INP-001` | input provenance tag |
| `residual_error_bound` | `RES-001` | must be a number >= 0 (`null` = absent), else `RES-001` fires at any CT, blocked or not (`conformance/laas/laas.rego:297-301`); an absent bound (`null`) raises no `RES-001` violation for Bucket A (passed deterministic verifier, `conformance/laas/laas.rego:244-247`), a blocked action, or a non-numeric `residual_tolerance`; otherwise `RES-001` fires for a non-blocked action whose `residual_tolerance` is numeric and whose bound is absent (`_bound_present` is `is_number(input.residual_error_bound)`, `conformance/laas/laas.rego:233`; rule at `conformance/laas/laas.rego:256-261`). At a zero tolerance the over-tolerance comparison is skipped for Bucket A and for human-gated actions (passed human verifier plus `human_approval.approved`), and a bound of exactly 0 on a non-blocked, non-Bucket-A action fires `RES-001` (`conformance/laas/laas.rego:318-356`) |
| `evidence_refs` | `RES-001` (present means a non-empty array of non-empty strings, `conformance/laas/laas.rego:235-242`; required, for a non-blocked action whose `residual_tolerance` is numeric, when the bound is numeric (`conformance/laas/laas.rego:233`), `:249-254`) | the spec's `evidence_refs`, copied unchanged and emitted at the top level only when the spec supplies an array (`scripts/laas/emitter.py:467-471`); never invented |
| `action_blocked` | block path for IRR/IND/VQ/HUM/INP-001 and the RES-001 spec-alignment rules, including the CT4 model-verifier IND-001 rule (`blocked`, `conformance/laas/laas.rego:61`; `not blocked` at `:228`, `:251`, `:258`, `:353`) | gate enforcement outcome |

> Note: `action.actor_id` and `verifier.id` are read only by HUM-001, which compares them with `human_approval.approver_id` (`verifier.id` only for a `human` verifier; `conformance/laas/laas.rego:403-404`, `:408-416`). `action.id`, `action.effect_surface.tool`, `gate.bundle_version`, `escalation_approved`, and the `trace.actor_chain_prev_hash` / `merkle_anchor` fields are **not** read by *this* policy (compare `rg -o 'input(\.[a-z_]+)+' conformance/laas/laas.rego | sort -u`). All of these appear in the `action.ct4-blocked.json` example, and all but `action.effect_surface.tool` have a counterpart in the §7.2 declared decision-trace schema (`action_ref`, `actor_id`, `verifier_id`, `policy_bundle_version`, `escalation_approved`, `actor_chain_prev_hash`, `merkle_anchor`; `docs/laas/proposal-v1.1.md:229-257`), so the emitter emits them for the trace sink. They are harmless to the policy (it ignores unread keys).

The record also carries a top-level `effect_surface_hash`, the §7.2 declared trace field (`docs/laas/proposal-v1.1.md:230`), placed at the top level as in the §7.4 example record (`docs/laas/proposal-v1.1.md:285`). The policy does not read it (it does not appear in the `rg` output above). The emitter always writes it as `sha256:` plus the hex SHA-256 of the canonical JSON (sorted keys, no whitespace) of the keys `derive_ct` resolved: `external_effect` and, only when it is boolean `true`, the resolved `reversibility`, `scope` and `consequence` (`_surface_hash`, `scripts/laas/emitter.py:362-370`; emitted at `:465`). That is the record's `action.effect_surface` without `tool`, so a trace reader can recompute the hash from the record alone. `tool` is provenance only and is not hashed.

### The CT-derivation the emitter performs (§6.1 — gate-derived, ungameable)

```text
ct = 0                                            if external_effect is false  (read-only/sandboxed)
ct = default_ct_when_undetermined (= 4)           if external_effect is not a boolean (null, "false", 0, 1, ...)
ct = max(rev[reversibility], scope[scope],
         consequence[consequence])                if external_effect is true, all axes known
ct = default_ct_when_undetermined (= 4)           if true and ANY axis undetermined (§6.2 default-to-highest)

gate.assigned_ct = max(ct, aggregate.window_effect_ct)   (§6.4 structuring guard — window can only RAISE)
```

This is what the emitter's `derive_ct()` does, not the policy. It mirrors `laas.rego`'s `expected_ct` rule (`conformance/laas/laas.rego:30-35`), which gives CT0 only for boolean `false` and the lattice only for `true`. The emitter gives CT0 only when `external_effect` is boolean `false` (`scripts/laas/emitter.py:315-316`). Any other value, such as null, the string `"false"`, `0` or `1`, fails closed to `default_ct_when_undetermined` without reading the axes (`scripts/laas/emitter.py:319-322`, helper `:281-288`). The record carries the raw value, and only boolean `true` adds the resolved axes (`scripts/laas/emitter.py:415-418`). An absent `external_effect` never reaches `derive_ct()`: the CLI rejects the spec with exit 2 (`scripts/laas/emitter.py:584-587`). When `-b` names the **signed bundle** (`data.json`), the lattice is loaded from it at runtime; without `-b` the emitter uses the in-module `_DEFAULT_LATTICE` fallback (`scripts/laas/emitter.py:38-42`, `:721`). `scripts/laas/check.sh:18` passes `-b`.

---

## 4. Proof — emitted record is policy-evaluable

`bash scripts/laas/check.sh`, run from the repository root, emits a record from `scripts/laas/fixtures/transfer.effect-surface.json` (the §6.1 worked example: `payments.transfer` to an external counterparty) with `-b conformance/laas/data.json`, then evaluates it with `opa eval` against the canonical in-repo policy + bundle (`conformance/laas/`) for `summary`, `error_ids` and `compliant` (`scripts/laas/check.sh:18`, `:31-40`). If `opa` is not on `PATH`, the script prints the emitted record, skips the evaluation, and exits 0 (`scripts/laas/check.sh:23-26`). **Result under opa 1.18.2:**

```json
{ "bundle": "laas-fin-2.0.0", "compliant": true, "effective_ct": 4,
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

The verifier verdict and the window matter. With the fixture's abstaining verifier, case A also fires `IRR-001`: `error_ids` is `["LAAS-OBL-HUM-001", "LAAS-OBL-IRR-001"]`. With the fixture's `aggregate.window_effect_ct` of 4, case B emits `assigned_ct` 4, not 0, because the window can only raise the tier (`scripts/laas/emitter.py:410`).

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
4. **`residual_error_bound` (Bucket B).** Must come from a backtest report for the claim class, re-measured on any model/prompt/tool/policy change (§5). A numeric bound (`conformance/laas/laas.rego:233`) without evidence fires `RES-001` for a non-blocked action whose `residual_tolerance` is numeric (rule at `conformance/laas/laas.rego:249-254`). The emitter writes the spec's `evidence_refs` (§2), so the harness must supply the backtest artifact's `evidence_id`. **TODO:** source `evidence_refs` from the backtest pipeline rather than the spec.
5. **Enforcement-plane attestations.** `bundle_signed` and `out_of_process` are currently config defaults. In production they must be **verified at gate startup** (signature check on the pinned bundle; proof the gate process is outside the actor's reach), not asserted. **TODO:** add the bundle-signature verifier and the out-of-process self-attestation.
6. **Trace chaining.** `actor_chain_prev_hash` / `merkle_anchor` are passed through. A real sink must compute the per-actor hash-chain head and the periodic Merkle anchor, and persist to an append-only store the actor cannot rewrite (§7.4/§7.7). **TODO:** implement the chained-trace writer; set `append_only` from the sink's actual mode, not a default.
7. **Human-approval queue.** Only `per_action` approval is supported (ADR-003 D4, SD-12): `human_approval_bases` holds only `per_action` (`conformance/laas/data.json:33`), so standing envelopes and batched approval do not satisfy HUM-001. The harness must supply the approver's identity and an attestation reference for each CT4 action. **TODO:** source `approver_id` and `attestation_ref` from the approval system's signed record.
8. **`indeterminate` vs `abstain` (finding 2.5).** Deterministic (Bucket A) verifiers must return `pass`/`fail`/`indeterminate`, never `abstain`. The emitter accepts whatever the registry reports; the registry adapter should enforce this per verifier type. **TODO:** add the per-type verdict-domain check in the verifier adapter.
