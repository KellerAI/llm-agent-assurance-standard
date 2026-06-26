# LLM-Agent Assurance Standard (LAAS)

**Status:** Draft v1.1 · **Artifact type:** `markdown-spec` (normative) + `rego-policy` (enforcing)
**Machine source of truth:** [`conformance/laas/data.json`](../conformance/laas/data.json)
**Enforcing policy:** [`conformance/laas/laas.rego`](../conformance/laas/laas.rego) — package `kellerai.laas.actions`
**Rationale / design record:** `docs/laas/proposal-v1.1.md`

> Like `OSS-PUBLICATION-STANDARD.md`, this prose is the canonical reference and `data.json`
> is derived from it. Where this document and `data.json` disagree, that is a bug: open a
> `policy-bug` issue. Prose cannot block a bad action — the Rego policy does.

---

## 1. Scope

LAAS is a conformance standard for **individual actions taken by LLM-based agents**. It does
not certify a model; it gates what an agent is allowed to *commit*. It applies wherever an
agent can take an action with an effect outside its own sandbox (call a tool, write a record,
move money, change access).

LAAS is a **standard of care**, not a correctness guarantee. Conformance asserts that the
*right checks ran, by the right party, with evidence* — not that no error can occur.

## 2. The governing invariant (normative)

LAAS applies Zero-Trust to the model's outputs **and** to the apparatus around them. A
conforming system MUST NOT trust:

1. the agent's **self-classification** of its own action;
2. a verifier's **soundness or independence** without evidence;
3. the **integrity of the enforcement plane**.

Any control that lets the constrained party tier, grade, or gate itself is non-conforming.

## 3. Consequence Tiers (normative)

Every action is assigned a **Consequence Tier (CT0–CT4)** by the **gate**, computed from the
**observed effect surface** — never from the agent's self-report. (CT numbers rise with
consequence; note this is the inverse of DO-178C DAL letters.)

```text
ct = max( reversibility_rank, scope_rank, consequence_rank )   # external effect
ct = 0                                                          # read-only / sandboxed
ct = 4                                                          # any axis undetermined  (default-to-highest)
```

Ranks are defined in `data.json → tier_lattice`. Operational definitions of `reversibility`,
`scope`, and `consequence`, each with an explicit *unknown → highest* rule, are in proposal
v1.1 §6.2.

| CT | Regime (normative minimum) |
|----|----------------------------|
| 0  | Trace only |
| 1  | Self-check (exact verifier if one exists) + trace |
| 2  | Independent automated check **or** rehearsed rollback + bounded residual + trace |
| 3  | **Mandatory independent, qualified pre-commit verification** + residual ≤ tolerance + rollback plan + trace |
| 4  | CT3 controls **+ human approval** + abstention default + full evidence |

The cumulative effect of a sequence MUST be tiered too: if a windowed aggregate crosses a
threshold, subsequent actions are re-tiered to the aggregate's tier (anti-structuring).

## 4. Obligations (normative)

The authoritative, versioned list lives in `data.json → obligations`. Each carries an ID,
severity, CT floor, precedence, and a reference to the rationale section. `error`-severity
violations are blocking; `warning`-severity are reported.

| ID | Obligation | Sev | CT floor |
|----|------------|-----|----------|
| `LAAS-OBL-TIER-001` | Tier is gate-derived from the observed effect surface | error | 0 |
| `LAAS-OBL-SELF-001` | A self-reported tier may not lower the gate tier | warning | 0 |
| `LAAS-OBL-ENF-001` | Enforcement-plane integrity: signed bundle + out-of-process gate | error | 0 |
| `LAAS-OBL-TRC-001` | Append-only, chained decision trace | error | 0 |
| `LAAS-OBL-AGG-001` | Cumulative blast-radius aggregation / re-tiering | error | 0 |
| `LAAS-OBL-INP-001` | Untrusted input raises the tier or blocks | error | 0 |
| `LAAS-OBL-VEN-001` | Third-party / vendor attribution and scope limits | error | 0 |
| `LAAS-OBL-IRR-001` | Independent pre-commit verification for CT≥3 | error | 3 |
| `LAAS-OBL-IND-001` | Verifier independence + low error-correlation | error | 3 |
| `LAAS-OBL-VQ-001`  | Verifier qualification (DO-330 analogue) | error | 3 |
| `LAAS-OBL-RES-001` | Bounded residual escape rate (Bucket B) | error | 2 |
| `LAAS-OBL-HUM-001` | Human approval required at CT4 | error | 4 |

### 4.1 Verifier independence (normative)

A verifier is independent of the actor iff one holds, by tier:

- it is a **different kind of checker** (deterministic/exact) — valid at any CT for the deterministic class;
- it is a **distinct model lineage AND** shows **measured error-correlation ≤ `max_error_correlation`** — valid up to CT3;
- it is a **human** — required *in addition* at CT4.

A verifier sharing the actor's model lineage is presumed non-independent.

### 4.2 Verifier qualification (normative)

A verifier gating CT≥3 MUST be qualified: documented coverage of its claim class, a negative-test
suite of known-bad inputs it must catch, and a change-controlled version recorded in the trace.

### 4.3 Escape rate (normative)

For the open-world ("Bucket B") class, the operator declares a maximum **escape rate** (residual
undetected-error rate) per CT (`data.json → escape_rate_tolerance_by_ct`), estimates it by
backtesting on a held-out adversarial set, and re-measures on any model/prompt/tool/policy change.
Conformance requires measured escape rate ≤ tolerance, with evidence referenced in the trace.

## 5. Decision trace (normative)

Each gated action emits one decision-trace record carrying, at minimum, the fields enumerated
in proposal v1.1 §7.2 (`emit_decision_trace`). Records are written to an **append-only,
content-addressed** store the actor cannot rewrite; each actor maintains its own hash-chain,
periodically anchored into a shared Merkle root (multi-agent safe). PII/MNPI is minimized and
tokenized; the searchable index is separable from sensitive payloads.

The **conformance predicate** (encoded in `laas.rego`) is, in plain terms:

> If an obligation's trigger matched, then either the action **passed** an independent, qualified
> verifier (plus human approval at CT4, plus residual ≤ tolerance) **or** the action was
> **blocked** and escalated. Nothing else conforms.

## 6. Conformance & attestation

A deployer demonstrates conformance with a **signed, sampled bundle** of decision traces over a
period, plus an **independent auditor attestation** that the bundle's verdicts satisfy the
obligation set. This artifact graduates into a third-party certificate if an SDO adopts LAAS.

## 7. Lifecycle & precedence

Obligations move `propose → active → deprecated → retired`; retired obligations leave the active
set. When two obligations fire incompatibly, precedence is deterministic: highest CT wins; ties
resolve to the most restrictive outcome (block). Each obligation's `precedence` is recorded in
`data.json`, and the resolution order is itself written to the trace.

## 8. Conformance of *this* artifact

A fresh agent, given only `data.json` and a candidate decision record, can derive the tier, locate
the applicable obligations, evaluate the predicate, and emit `pass | fail | abstain | indeterminate`
— with no human explanation. See [`conformance/laas/README.md`](../conformance/laas/README.md).
