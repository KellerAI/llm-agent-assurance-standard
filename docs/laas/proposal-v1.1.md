# LLM-Agent Assurance Standard (LAAS) — Proposal v1.1

**Working title:** LAAS — *LLM-Agent Assurance Standard*. **Disambiguation:** unrelated to "Logging/License-as-a-Service." Formal-name shortlist for ratification (finding 1.7): **ALAS** (Agentic LLM Assurance Standard), **A²LS**, **AgentAL**. "LAAS" retained as the working acronym below.
**Supersedes:** v1.0 (`LAAS_first_proposal.md`, 2026-06-18), kept intact for diff.
**Date:** 2026-06-18
**Status of claims:** confidence-flagged inline; ledger at the end. No standards body has endorsed or is known to be considering LAAS; the adoption section describes *options*, not commitments.

---

## Changelog v1.0 → v1.1 (finding → change)

The 5-pass blunder hunt itemized **29** findings (the v1.0-review synthesis mis-tallied "26"; corrected here). All 29 are resolved.

### Pass 1 — surface

- **1.1** Renamed the tier from "AAL" → **Consequence Tier (CT0–CT4)** to avoid collision with NIST SP 800-63 *Authenticator Assurance Level*. §6, throughout.
- **1.2** Renamed the metric "integrity" → **escape rate** (residual undetected-error rate); where a higher-is-better figure is wanted, `integrity = 1 − escape rate`. §1, §5.
- **1.3** "Modified Condition-Decision Coverage" → **Modified Condition/Decision Coverage (MC/DC)**. §2.
- **1.4** "Three lines of defense" no longer attributed *to* SR 11-7; described as a risk-management model **commonly paired with** it. §2.
- **1.5** Added **FAA/EUROCAE overarching properties** (intent, correctness, innocuity) as a distinct landscape entry, separated from EASA's properties. §4.2.
- **1.6** Softened EASA "High-Level Properties" to EASA's actual framing (learning assurance / trustworthy-AI building blocks); flagged. §4.2.
- **1.7** Name-collision acknowledged; formal-name shortlist added (header).

### Pass 2 — consistency

- **2.1** §13 self-check rewritten honestly: machine-actionability now holds for the deterministic path (predicate is evaluable, CT function defined); Bucket-B conformance is gated on a backtest the operator must supply.
- **2.2** Added **standing/pre-authorized envelopes + batched approval** so CT-4 human oversight scales sub-linearly and doesn't contradict supervise-by-exception. §6.3.
- **2.3** Reproducibility claim split: **deterministically reproducible** (Bucket A) vs **tamper-evidently re-inspectable** (Bucket B). §7.4.
- **2.4** Blast-radius pseudo-formula replaced by a **defined tier lattice**; `scope` and `consequence` are now real descriptor fields used by the predicate. §6.1, §7.2.
- **2.5** Added an **`indeterminate`** verdict for deterministic checkers lacking inputs; fixed the example. §5, §7.4.

### Pass 3 — schema

- **3.1** `conformance_predicate` now only references declared fields; **`action_blocked`** and **`escalation_approved`** added to the emitted trace. §7.2, §7.4.
- **3.2** Added an explicit **CT-derivation function** `ct = f(reversibility, scope, consequence)` (a lattice with a worked example) computed by the gate. §6.1.
- **3.3** **Operational definitions** for `reversibility`, `scope`, `consequence`, each with a **default-to-highest** rule when undetermined. §6.2.
- **3.4** Linear hash-chain replaced by **per-actor hash-chains anchored into a periodic Merkle root** written to an append-only sink. §7.4.
- **3.5** **Evidence store** defined: append-only, content-addressed, retention-by-tier. §7.6.

### Pass 4 — omissions (new obligations)

- **4.1** **CT is gate-derived from the observed effect surface**, not the agent's self-report; self-reports may not lower the tier (`LAAS-OBL-TIER-001`, `-SELF-001`). §6.1, §7.3.
- **4.2** **Verifier-qualification obligation** (coverage evidence, negative tests, change-controlled verifier versions in the trace) — the DO-330 analogue (`LAAS-OBL-VQ-001`). §7.5.
- **4.3** **Cumulative blast-radius / aggregation obligation** (closes the structuring loophole) (`LAAS-OBL-AGG-001`). §6.4.
- **4.4** **Third-party/vendor/supply-chain obligation** (`LAAS-OBL-VEN-001`). §8.2.
- **4.5** **Input-provenance + injection-resistance obligation**; untrusted input raises the tier (`LAAS-OBL-INP-001`). §8.3.
- **4.6** **Conformance-attestation artifact** defined for the de-facto model (signed, sampled trace bundle + independent auditor attestation). §11.3.
- **4.7** **Rollback-rehearsal evidence** required wherever rollback substitutes for pre-commit verification (`LAAS-OBL-RBK-001`). §6.3.

### Pass 5 — second-order

- **5.1** Independence redefined: a model verifier must be a **distinct lineage AND show low measured error-correlation** with the actor; otherwise fall back to deterministic/human at CT≥3 (`LAAS-OBL-IND-001`). §7.3.
- **5.2** **Enforcement-plane integrity** obligations: signed/version-pinned bundle, **out-of-process gate** the actor can't disable, append-only trace sink (`LAAS-OBL-ENF-001`). §7.7.
- **5.3** **Zero-Trust-on-classification principle** stated as a first-class invariant so it isn't re-violated. §0.1.
- **5.4** **Obligation lifecycle** (propose→active→deprecated→retired) + **deterministic conflict-resolution/precedence**. §9.6.
- **5.5** **Trace data-governance** (minimize, tokenize/redact PII/MNPI, split index from payload). §7.6.

---

## 0. Variables & the governing invariant

| Variable | Default | Re-opened |
| --- | --- | --- |
| `TARGET_FIRST_VERTICAL` | Financial-services agents (primary); aerospace-adjacent as rigor exemplar | §11 |
| `HOST_BODY_PREFERENCE` | De-facto via reference implementation, architected to graduate into IEEE / ISO-IEC JTC1 SC42 | §11 |
| `EXISTING_PRIMITIVES_TO_REUSE` | Policy-as-code conformance gates, pre-commit stop-hook checks, decision-trace logs (all) | §7 |
| `DEPTH` | Full proposal draft | — |

### 0.1 The governing invariant (finding 5.3)

LAAS applies **Zero-Trust to the model's outputs *and* to the apparatus around them.** Specifically, LAAS never trusts: (a) the actor's **self-classification** of its own action; (b) a verifier's **soundness or independence** absent evidence; (c) the **integrity of the enforcement plane**. Every obligation below is an instance of pushing Zero-Trust inward. If a new obligation would let the constrained party grade, tier, or gate itself, it is malformed.

---

## 1. TL;DR

**Common structural object.** DO-178C, SR 11-7, and UL 4600 run one machine under different vocabularies: (1) **bound undetected error**, (2) **scale rigor to consequence**, (3) **require independent verification** (nothing grades its own work), (4) **trace every decision to evidence**, (5) **abstain/escalate out of scope**. The shared quantity is the **escape rate** — the rate at which a wrong result survives every check and is acted upon.

**Mapping to LLM agents.** Sort each claim/action into **Bucket A — deterministically checkable** (eliminate undetected error with exact verifiers) or **Bucket B — open-world** (bound the escape rate to a declared tolerance, measure it by backtesting on a held-out adversarial set, control it by independent/human review above tolerance and abstention below confidence). Rigor scales by **Consequence Tier (CT0–CT4)**, derived by the gate from the action's observed effect surface (reversibility × scope × consequence) — not by use-case category, model size, or the agent's say-so.

**Why agent-friendly, and what it buys.** A spec agents can't mechanically check is dead on arrival. LAAS ships in **two coupled layers** — a human-readable normative document and a machine-actionable obligation bundle (stable IDs, trigger predicates, named verifiers, abstention paths) that emits a tamper-evident **decision trace** per check, sharing one source of truth so the two can't diverge. The self-test (§8) is literal: a fresh agent, given only the bundle and a task, must derive the tier, locate the applicable obligations, run the verifiers, and emit a pass/fail/abstain/indeterminate verdict — no human explanation.

**The gap (§4).** Horizontal governance (ISO/IEC 42001, NIST AI RMF + GenAI Profile, EU AI Act + GPAI CoP) governs management systems, model providers, and use-case tiers; aerospace AI assurance (ARP6983/ED-324, EASA, overarching properties) is rigorous but scoped to frozen supervised ML in embedded avionics; agent-specific work (Five Eyes *Careful Adoption of Agentic AI Services* (2026), CSA MAESTRO/ATF/STAR-for-AI, OWASP Agentic Top 10/AIVSS, CoSAI, NIST CAISI RFI) is threat taxonomy, identity/authorization, governance, and in-progress control language. **None is a published, two-layer, machine-checkable assurance standard that derives obligations from per-action blast radius, mandates independent pre-commit verification of irreversible actions, requires bounded backtested escape rate on the open-world class, and emits a reconstructable decision trace as the conformance artifact.**

---

## 2. The three mature standards (mechanics, not vocabulary)

*Confidence: structure is training-knowledge on stable standards; specific objective counts not asserted.*

**DO-178C.** Rigor set by **Design Assurance Level (DAL A–E)** from worst-case failure effect (A catastrophic … E none). Higher DAL → more verification objectives, more *with independence* (verifier ≠ author). Spine: requirements-based verification with bidirectional traceability + **structural coverage** — statement, decision, and **MC/DC (Modified Condition/Decision Coverage)**, the coverage type escalating with DAL — to bound undetected code no requirement exercised. Output: a certification data package.

**SR 11-7.** Built on **effective challenge** — credible independent review with authority to change the model. Implemented via a validation lifecycle (conceptual soundness → ongoing monitoring → outcomes analysis/**backtesting**), **risk-tiering by materiality**, and **explicit vendor coverage** (you own the risk of models you buy). The **three-lines-of-defense** model is broader enterprise-risk practice **commonly paired with** SR 11-7, not a creature of its text (finding 1.4).

**UL 4600.** A **standard of care**, not pass/fail: a **safety case** (often in Goal Structuring Notation) bounded by an **Operational Design Domain (ODD)**, residual risk tracked via **Safety Performance Indicators (SPIs)**, with prompt-element checklists. Companion **ISO 21448 (SOTIF)** governs hazards from performance limitations with **no component failure** — works as designed, still unsafe.

---

## 3. The common structural object

| Shared mechanic | DO-178C | SR 11-7 | UL 4600 | LAAS |
| --- | --- | --- | --- | --- |
| Scale rigor to consequence | DAL A–E | Materiality | Risk-based case depth | **CT0–CT4** by blast radius (§6) |
| Bound undetected error | Structural coverage | Backtesting | SPIs | **Escape rate** per bucket (§5) |
| Independent verification | Objectives "with independence" | Effective challenge | Independent assessment | **No self-grading**; lineage + low correlation (§7.3) |
| Trace to evidence | Bidirectional trace + data package | Validation docs | GSN + evidence | **Decision-trace JSONL**, ID-threaded (§7.4) |
| Declared envelope + abstain | Config/operational envelope | Approved use | ODD | **Authorized Operating Envelope** (§6.5) |
| "No failure, still wrong" | (weak) | Conceptual soundness | SOTIF | **Bucket B** bounding + independent review (§5) |

---

## 4. Gap analysis

*Confidence: current state verified via 2025–2026 sources; dates as of mid-2026, confirm before publication.*

### 4.1 Horizontal AI governance — governs org and model maker, not the runtime action

- **ISO/IEC 42001:2023** — AI Management System on the ISO Harmonized Structure, Annex A control catalogue (~38; confirm), Statement of Applicability, third-party certifiable (auditor qual via ISO/IEC 42006:2025). Organizational lifecycle governance; **no GenAI annex, no per-action runtime conformance**.
- **NIST AI RMF (AI 100-1, 2023)** — voluntary, four functions, seven characteristics, ~72-subcategory Playbook; **GenAI Profile (AI 600-1, Jul 2024)** adds 12 risks. Outcomes/methodology, **no formal assessment process**.
- **EU AI Act** — risk-tiered by use-case category; **GPAI model-provider** obligations (in force Aug 2025; enforcement Aug 2026) + voluntary **GPAI CoP** (Transparency/Copyright/Safety & Security); high-risk Annex III deferred to Dec 2027 (May 2026 Digital Omnibus, *provisional*). An agent-builder is typically a **deployer** (transparency/oversight/monitoring); conformity assessment is **system-level and periodic**.

### 4.2 Aerospace AI assurance — rigorous, wrong species of model

- **ARP6983 / ED-324** (SAE G-34 / EUROCAE WG-114; ~Q1 2026, confirm) — W-shaped lifecycle, **explicitly limited to *frozen, supervised* ML** in embedded avionics, ~DAL C; **excludes generative/LLM/online learning**.
- **EASA AI concept paper** — introduces **learning assurance** and a trustworthy-AI building-block framework (auditability, data quality, explainability); guidance for embedded ML, not enterprise agents *(finding 1.6: framing softened to EASA's own terms; exact property labels to be verified against the paper)*.
- **FAA/EUROCAE overarching properties** *(new — finding 1.5)* — a separate line of work defining product-level properties (commonly **intent, correctness, innocuity**) intended to be technology-agnostic acceptance criteria. Relevant as a conceptual ancestor for LAAS's "verify the envelope, not the function," but it is an avionics certification concept, **not** an LLM-agent conformance standard, and is **distinct** from EASA's properties.

### 4.3 Agent-specific work — taxonomy, identity, governance, in-progress control language

- **Five Eyes — *Careful Adoption of Agentic AI Services*** (six agencies, 29 pp, Apr–May 2026): treat agents as **untrusted components**, five risk categories, prompt injection prominent, verified cryptographic agent identity + short-lived credentials, and human sign-off for high-impact actions where **the system designer (not the agent) decides which actions require it**. Operationally authoritative **guidance**, not a machine-checkable conformance standard.
- **CSA MAESTRO** (threat modeling), **ATF** (Zero-Trust governance), **STAR-for-AI / CSAI** (assurance/"auditable control language," Phase 1 Jun–Sep 2026, in progress); **OWASP Agentic Top 10 + AIVSS** (vuln taxonomy); **CoSAI** (OASIS coalition — *Principles for Secure-by-Design Agentic Systems*, *Agentic IAM*); **NIST CAISI RFI** (Jan 2026) + **NCCoE** identity concept paper.

**Net:** the closest neighbor (CSA STAR-for-AI) is mid-flight and security-scoped; nothing published is a two-layer machine-actionable assurance standard with gate-derived blast-radius tiering, mandatory independent pre-commit verification of irreversible actions, bounded backtested escape rate, and a reconstructable decision trace.

---

## 5. Two buckets and the escape-rate metric

**Bucket A — deterministically checkable (eliminate).** An exact oracle exists (compile, schema-validate, ledger nets to zero, allowlist, hash match, invertible round-trip). Run the exact verifier; escape rate → ~0, bounded by **verifier soundness — which is itself an obligation, not an assumption** (§7.5). No probabilistic tolerance is permitted where an exact verifier exists; *whether one exists is determined by the gate's verifier registry, not the actor* (finding 5.3). Deterministic verifiers return **pass / fail / indeterminate** (the last when required inputs are missing) — never "abstain," which is a confidence notion (finding 2.5).

**Bucket B — open-world (bound, measure, control).** No exact oracle. (1) **Bound:** the operator declares a maximum acceptable **escape rate** for the claim class *at the relevant CT*. (2) **Measure:** estimate by **backtesting** on a held-out, representative, adversarially-stressed set with a stated confidence interval; re-measure on any model/prompt/tool/policy change. (3) **Control:** route to independent verification (different *kind* of checker, distinct + de-correlated model lineage, or human) above tolerance; **abstain/escalate** below confidence or out of envelope.

**Escape rate** is the governing metric: the rate at which a wrong output passes every applicable check and is committed. Conformance asserts **measured escape rate ≤ declared tolerance at every CT, with traceable evidence**. (If a higher-is-better figure is wanted, report `integrity = 1 − escape rate`.) LAAS is a **standard of care**, not a correctness guarantee.

---

## 6. Consequence Tiers, derivation, and the envelope

### 6.1 The CT-derivation function (findings 3.2, 4.1, 2.4)

**Direction note:** CT numbers rise with consequence (CT4 worst); DAL letters fall A→E with decreasing consequence. Stated to prevent cross-mapping errors.

The **gate** (not the agent) derives the tier from the **observed effect surface** of the action — the actual tool/API/scope/amount it invokes:

```text
ct = max( rev_ct[reversibility], scope_ct[scope], cons_ct[consequence] )      # if external effect
ct = 0                                                                          # if no external effect (read-only/sandboxed)
ct = 4                                                                          # if ANY input is undetermined  (default-to-highest, §6.2)

rev_ct  = { reversible:1, hard:3, irreversible:4, none:4 }
scope_ct= { single:1,     multi:2, org:3,         public:4 }
cons_ct = { none:0,       low:1,   material:3,    high:4 }
```

**Worked example.** An agent calls `payments.transfer(amount=250000, dest=external)`. Observed surface: reversibility=`irreversible`, scope=`public` (external counterparty), consequence=`high` → `max(4,4,4)=CT4`. The agent's *self-reported* tier is irrelevant; the gate's stands (`LAAS-OBL-TIER-001`). A self-report lower than the gate's tier is flagged (`LAAS-OBL-SELF-001`).

### 6.2 Operational definitions (finding 3.3)

- **reversibility** — `reversible`: a tested, in-window, single-step undo exists; `hard`: undo exists but is costly/multi-step/time-bounded; `irreversible`: no programmatic undo; `none`: unknown. **Unknown → treat as irreversible.**
- **scope** — `single` (one record/user), `multi` (many), `org` (org-wide), `public` (external parties/world). **Unknown → `public`.**
- **consequence** — `none / low / material / high` by worst-case impact (financial, safety, legal, reputational). **Unknown → `high`.**

### 6.3 Regime by tier, with scalable human oversight (findings 2.2, 4.7)

| CT | Examples | Regime |
| --- | --- | --- |
| 0 | Read-only, sandboxed | Trace only |
| 1 | Reversible internal write | Self-check (exact verifier if available) + trace |
| 2 | Reversible/low-value external | Independent automated check **or** rehearsed rollback + trace |
| 3 | Hard-to-reverse / material external | **Mandatory independent pre-commit verification (no self-grading)** + Bucket-B escape ≤ tolerance + rollback plan + trace |
| 4 | Irreversible / high-consequence | Independent verification **+ human approval** + **abstention default** + full evidence + trace |

**Scaling CT-4 oversight (2.2).** Human approval need not be per-action. Operators may register **standing/pre-authorized envelopes** — a human pre-approves a bounded action class with explicit limits (e.g., "external transfers ≤ \$X to allowlisted counterparties"); the gate enforces the bounds and only escalates **out-of-envelope** actions, and supports **batched approval** of queued in-envelope items. Human attention scales with exceptions, not volume.

**Rollback rehearsal (4.7).** Any tier that substitutes a rollback path for pre-commit verification (CT2) must carry **periodic rollback-rehearsal evidence**; an unrehearsed rollback does not satisfy the obligation.

### 6.4 Cumulative blast radius (finding 4.3)

Per-action tiering is necessary but not sufficient: N sub-threshold actions can compose into a high-CT effect (**structuring**). The gate maintains a windowed aggregate per principal/session/effect-class; when the **aggregate effect** crosses a tier threshold, subsequent actions are **re-tiered to the aggregate's tier** (`LAAS-OBL-AGG-001`).

### 6.5 Authorized Operating Envelope (AOE)

The ODD analogue: the operator enumerates **permissions and action classes** (tools, scopes, data domains, action classes, CT ceiling). Out-of-AOE is a **first-class abstention** (`verdict: abstain → escalate`). You bound the authority, not the inputs.

---

## 7. The two coupled layers (worked fragments of both)

The **human-readable normative document** and the **machine-actionable bundle** share one source of truth (`data.json`) so enforcement and prose cannot diverge. The machine layer reuses **policy-as-code gates, pre-commit stop-hooks, decision-trace logs**.

### 7.1 Worked obligation — normative form

> **LAAS-OBL-IRR-001 — Independent pre-commit verification for hard/irreversible external effects**
> *Normative.* An action whose gate-derived tier is **CT3 (hard)** or **CT4 (irreversible)** MUST pass an **independent, qualified pre-commit verifier** before commit. The verifier MUST satisfy independence (§7.3) and qualification (§7.5). At **CT4**, human approval MUST also be present. If the verifier returns `fail`, `abstain`, or `indeterminate`, the action MUST be blocked and escalated. The action, derived tier, verifier, verdict, independence basis, qualification reference, and escalation MUST be recorded in the decision trace and be reconstructable.
> *Rationale.* Instructions do not prevent execution; an out-of-process mechanical gate does. The analogue of DO-178C independence, SR 11-7 effective challenge, and a two-person rule.

### 7.2 Same obligation — machine-actionable form (fixed schema, findings 3.1/3.2/2.4)

```yaml
obligation_id: LAAS-OBL-IRR-001
version: 1.1.0
normative_text_ref: "§7.1"
applies_when:                       # over the GATE-DERIVED ActionDescriptor
  gate_derived_ct: { ">=": 3 }
required_verifier:
  independence_ref: "§7.3"          # MUST hold or the check is void
  qualification_ref: "§7.5"         # verifier MUST be qualified
  require_human_at_ct: 4
residual_error:                     # Bucket-B portion only
  tolerance_by_ct: { "3": 0.005, "4": 0.0 }
  evidence: backtest_report_ref
on_fail_abstain_or_indeterminate:
  action: BLOCK
  escalate_to: queue.human_review.high
emit_decision_trace:                # every field below is DECLARED here
  - obligation_id
  - obligation_version
  - action_ref
  - effect_surface_hash             # gate-observed surface (not self-report)
  - gate_derived_ct
  - self_reported_ct                # informational; may not lower the tier
  - trigger_matched
  - verifier_id
  - verifier_type                   # deterministic | model | human
  - verifier_independent            # bool
  - independence_basis
  - verifier_qualified              # bool
  - verifier_qualification_ref
  - verifier_error_correlation      # vs actor; for model verifiers
  - verifier_input_hash
  - verdict                         # pass | fail | abstain | indeterminate
  - residual_error_bound            # null for pure Bucket A
  - residual_tolerance
  - evidence_refs
  - escalation                      # null | {queue, ticket_id}
  - escalation_approved             # bool  (declared — fixes 3.1)
  - action_blocked                  # bool  (declared — fixes 3.1)
  - actor_id
  - policy_bundle_version
  - bundle_signed                   # bool  (5.2)
  - gate_out_of_process             # bool  (5.2)
  - aggregate_window_ct             # (4.3)
  - input_trusted                   # bool  (4.5)
  - timestamp
  - actor_chain_prev_hash           # per-actor chain (3.4)
  - merkle_anchor                   # periodic shared root (3.4)
conformance_predicate: >
  trigger_matched == true IMPLIES
    ( verdict == "pass"
      AND verifier_independent == true
      AND verifier_qualified == true
      AND (gate_derived_ct < 4 OR escalation_approved == true)
      AND (residual_error_bound == null OR residual_error_bound <= residual_tolerance) )
    OR ( verdict in ["fail","abstain","indeterminate"] AND action_blocked == true )
```

Every identifier in `conformance_predicate` now appears in `emit_decision_trace` — the predicate is mechanically evaluable.

### 7.3 Independence — defined, with error-correlation (finding 5.1)

A verifier is **independent** of the actor iff one holds, chosen by CT:

- **Deterministic/exact** (a different *kind* of checker). Independent at any CT for Bucket A.
- **Distinct model lineage AND measured error-correlation ≤ threshold** (e.g., ≤ 0.2 on the eval set). A different model that fails the same way is **not** a check. Permitted up to CT3.
- **Human.** Required *in addition* at CT4.

Shared-substrate verifiers (same base model/finetune family) are presumed **non-independent**. Where correlation cannot be bounded, CT≥3 falls back to deterministic or human.

### 7.4 Decision-trace record + integrity model (findings 2.3/3.4)

```json
{"action_ref":"act_7c31","effect_surface_hash":"sha256:1b9e…","gate_derived_ct":4,
 "self_reported_ct":4,"trigger_matched":true,"verifier_id":"VRF-LEDGER-DIFF",
 "verifier_type":"deterministic","verifier_independent":true,"independence_basis":"deterministic",
 "verifier_qualified":true,"verifier_qualification_ref":"VQ-2026-014","verifier_error_correlation":null,
 "verifier_input_hash":"sha256:44af…","verdict":"pass","residual_error_bound":null,"residual_tolerance":0.0,
 "evidence_refs":["ev_ledger_diff_001"],"escalation":{"queue":"human_review.high","ticket_id":"HR-2048"},
 "escalation_approved":true,"action_blocked":false,"actor_id":"agent.fundbot.v3",
 "policy_bundle_version":"laas-fin-1.1.0","bundle_signed":true,"gate_out_of_process":true,
 "aggregate_window_ct":4,"input_trusted":true,"timestamp":"2026-06-18T14:22:09Z",
 "actor_chain_prev_hash":"sha256:0c7d…","merkle_anchor":"sha256:9af1…"}
```

**Integrity & concurrency (3.4):** each actor appends to its **own** hash-chain (`actor_chain_prev_hash`); chains are periodically anchored into a shared **Merkle root** (`merkle_anchor`) written to an append-only sink the actor cannot rewrite (§7.7). This composes with concurrent multi-agent swarms (no single linear-chain appender). **Reproducibility (2.3):** Bucket-A verdicts are **deterministically reproducible** against the recorded input hash; Bucket-B verdicts are **tamper-evidently re-inspectable** (you re-read the recorded verdict and its evidence; you cannot necessarily re-derive a non-deterministic model verdict).

### 7.5 Verifier qualification (finding 4.2 — the DO-330 analogue)

A verifier that gates CT≥3 must be **qualified**: documented coverage of its claim class, a **negative-test suite** (known-bad inputs it must catch), and a change-controlled version recorded in the trace (`verifier_qualification_ref`). An unqualified verifier does not satisfy `LAAS-OBL-IRR-001`. Qualification depth scales with CT (`LAAS-OBL-VQ-001`).

### 7.6 Evidence store + trace governance (findings 3.5/5.5)

Traces and evidence live in an **append-only, content-addressed store** with **retention by CT** (higher tiers retained longer; regulated verticals meet their statutory minimums). **Data governance:** minimize payloads, **tokenize/redact PII/MNPI**, and separate the searchable **index** from sensitive payloads so audit access does not require exposing regulated data.

### 7.7 Enforcement-plane integrity (finding 5.2 — bootstrapping trust)

Mechanical enforcement only holds if the mechanism is outside the actor's reach. LAAS requires: a **signed, version-pinned policy bundle** (`bundle_signed`); an **out-of-process gate** (`gate_out_of_process`) the actor cannot disable — even when the actor runs with elevated permissions (e.g., `--dangerously-skip-permissions`-style modes); and an **append-only trace sink** the actor cannot rewrite (`LAAS-OBL-ENF-001`). A trace asserting an in-process or unsigned gate is non-conformant regardless of verdict.

### 7.8 Traceability (bidirectional)

A stable action/task ID threads the obligation, verifier run, evidence, escalation, and commit. Every committed CT≥3 action MUST have a passing/blocked trace; every obligation MUST be exercised by ≥1 trace in conformance evidence or marked not-applicable with reason — the DO-178C bidirectional-trace analogue.

---

## 8. Cross-cutting obligations

### 8.1 No self-grading / self-classification (invariant, §0.1)

The gate derives the tier and selects the verifier; the actor proposes. Any path where the actor sets its own tier, declares "no exact verifier available," or verifies its own output is non-conformant.

### 8.2 Third-party / vendor / supply chain (finding 4.4)

When the agent uses a vendor model or calls a third-party tool/API, the trace MUST carry **provenance and scope limits**, the residual error MUST be **attributed** (vendor-model error counts against the deploying operator's escape-rate budget), and untrusted dependencies **fail closed** (`LAAS-OBL-VEN-001`).

### 8.3 Input provenance + injection resistance (finding 4.5)

Untrusted input (web content, inbound email, third-party data) is a tier-raising signal: an action driven by untrusted input is gated at **≥ CT3** or blocked, and the trace records `input_trusted` (`LAAS-OBL-INP-001`). This is the control that protects tier-derivation and verifier trust from prompt injection.

---

## 9. Disanalogies, addressed (+ obligation lifecycle)

1. **No fixed spec.** LAAS specifies obligations on actions and verification of outputs (the *envelope*), not behavior (the *function*). Per-action conformance against a stable obligation set; a local fixed spec exists per task.
2. **Open operational domain.** AOE enumerates permissions/action classes; out-of-envelope → abstain. SOTIF's "no-failure-still-wrong" → Bucket-B bounding + independent review.
3. **Monolithic model.** Assure the *harness*, not the model. Unit of assurance = `(gate-derived action, qualified independent verifier, tamper-evident trace)`. The model is an untrusted component whose outputs are gated.
4. **Non-determinism.** Conformance is over the trace and verdicts (Bucket A reproducible; Bucket B re-inspectable, §7.4).
5. **Continuous change.** Version everything in the trace; re-backtest escape rate on any change (SR 11-7 ongoing monitoring).

### 9.6 Obligation lifecycle + conflict resolution (finding 5.4)

The bundle is versioned, not merely accretive. Obligations move **propose → active → deprecated → retired**; retired obligations leave the active set. When two obligations fire with incompatible outcomes, **precedence is deterministic**: highest CT wins; ties resolve to the most restrictive (block). Every obligation carries a `precedence` field; the gate's resolution order is itself recorded.

---

## 10. Rated design choices

Scoring 1–5: **Rigor / Agent-checkability / Adoption / Open-world fit.** ★ recommended; ⚖ answers the strongest counterargument.

### 10.1 Governing metric

| Option | R | A | Ad | O | Verdict |
| --- | --- | --- | --- | --- | --- |
| ★ Escape rate (residual undetected-error, bucketed) | 5 | 4 | 3 | 5 | The quantity all three mature standards bound; honest about Bucket B. |
| Calibration/Brier scoring | 4 | 4 | 3 | 4 | Good for confidence quality; doesn't bound consequential error alone. |
| Task success rate | 2 | 5 | 5 | 2 | Misleads — high success with rare catastrophic misses is the failure mode. |
| Capability threshold (FLOP) | 2 | 3 | 4 | 1 | Gates models, not actions. |
| ⚖ Escape rate + mandatory independent audit of the eval set | 5 | 4 | 2 | 5 | Answers "can't measure undetected error": the estimate is adversarially audited. |

### 10.2 Conformance model

| Option | R | A | Ad | O | Verdict |
| --- | --- | --- | --- | --- | --- |
| ★ Per-action runtime gating + decision traces | 5 | 5 | 3 | 4 | Catches the wrong action before commit. |
| Periodic system audit (ISO/EU) | 2 | 2 | 5 | 2 | Blind between audits. |
| Pre-deployment cert only (DO-178C) | 4 | 3 | 2 | 2 | Mismatched to weekly change + non-determinism. |
| Continuous monitoring/SPI only (UL 4600) | 3 | 3 | 4 | 4 | Reactive, not preventive at CT4. |
| ⚖ Hybrid: runtime gating (CT≥2) + periodic audit | 5 | 5 | 4 | 4 | Answers "runtime overhead too costly": tier it — CT0/1 log only. |

### 10.3 Tiering basis

| Option | R | A | Ad | O | Verdict |
| --- | --- | --- | --- | --- | --- |
| ★ Blast radius, **gate-derived** from effect surface | 5 | 4 | 3 | 4 | Tracks what matters at runtime; un-gameable by the actor. |
| Use-case category (EU Annex III) | 3 | 3 | 5 | 2 | Too coarse; one app spans many blast radii. |
| Model capability (FLOP) | 2 | 3 | 4 | 1 | Gates the model. |
| Data sensitivity only | 3 | 4 | 4 | 2 | Misses irreversible non-data actions. |
| ⚖ Gate-derived blast radius + regulatory-category overlay | 5 | 4 | 4 | 4 | Answers "regulators think in categories": keep blast-radius engine, publish a crosswalk. |

---

## 11. Adoption

### 11.1 Candidate host bodies

| Body | Speed | Teeth | Fit for machine-actionable runtime standard | Note |
| --- | --- | --- | --- | --- |
| IEEE SA | Med | High | Med-high | Faster than ISO; 7000-series precedent. |
| ISO/IEC JTC1 SC42 | Slow | Very high | Low initially | Management-system house style = the gap; the **graduation** target. |
| NIST (CAISI/NCCoE) | Med | High influence, no cert | Med | Home for a profile/overlay (RFI + identity paper in flight). |
| UL Solutions | Med | High, certifies | High | Safety-case/standard-of-care culture fits Bucket B. |
| EUROCAE/SAE | Slow | Very high (aero) | High but out of charter | ARP6983 is frozen-supervised-ML scoped. |
| CSA / CoSAI / OWASP | Fast | Practitioner; CSA STAR certifies | High | Early co-sponsors; align vocab so LAAS is additive. |

### 11.2 Path (rated)

Axes: **Speed / Durability / Proves machine-actionability / First-mover.**

| Path | S | D | P | F | Verdict |
| --- | --- | --- | --- | --- | --- |
| SDO-first (IEEE/SC42) | 2 | 5 | 2 | 2 | Max legitimacy; risks dilution into a management-system doc. |
| Consortium (CoSAI/CSA) | 3 | 3 | 3 | 3 | Good adopters; fragmentation/capture risk. |
| ★ De-facto via reference implementation + timestamped publication | 5 | 3→5 | 5 | 5 | The reference impl **is** the proof of machine-actionability. |
| ⚖ De-facto, architected to graduate (map to SC42/EU + NIST functions) + SR 11-7 anchor | 5 | 5 | 5 | 5 | Answers "de-facto lacks authority": built to be lifted into a formal standard, with regulatory pull from day one. |

### 11.3 Conformance attestation for the de-facto model (finding 4.6)

Absent a certifying body, a deployer demonstrates conformance via a **signed, sampled trace bundle** (a representative, integrity-verified slice of decision traces over a period) plus an **independent auditor attestation** that the bundle's verdicts satisfy the obligation set. This is the artifact a bank examiner or enterprise customer reviews; it graduates cleanly into a third-party certificate when an SDO adopts LAAS.

**Recommended play.** Ship the de-facto reference implementation (⚖), lead in financial services (SR 11-7 pull), recruit CSA/CoSAI/OWASP as co-sponsors (align trace/control vocabulary with MAESTRO/ATF/STAR-for-AI), graduate the stabilized core into IEEE/SC42 with a NIST profile. Establish primacy via timestamped, verifiable publication — no claimed endorsements.

---

## 12. Steelman + answer

**Objection.** *"General-purpose agents are unspecifiable, so a DO-178C analogue is a category mistake"* — no fixed spec to trace to, no structural coverage of a trillion-parameter model, so any such standard is either vacuous theater or a straitjacket on the generality that makes agents useful.

**Answer.** The category mistake is in the objection. LAAS specifies the **envelope, not the function**: it bounds the **escape rate** at which an undetected error reaches a consequential action, scaled to blast radius, with independent verification and a reconstructable trace. That is what the mature standards do stripped of vocabulary — **SR 11-7** never specifies what a model computes (it challenges independently and backtests); **UL 4600** never enumerates every road scene (safety case + ODD + abstention); **SOTIF** explicitly governs hazard with no failure and no complete spec. For the open-world bucket LAAS is the SR 11-7/UL 4600 branch; for the deterministic bucket, the DO-178C branch. The model's unspecifiability is precisely why assurance moves to the **harness**. Generality is preserved: the agent may *attempt* anything; it may not *commit* a high-blast-radius action without an independent, qualified check, gated out-of-process. The objection proves too much — by its logic SR 11-7 and UL 4600 are also category mistakes, yet they bound risk in unspecifiable open-world systems daily.

**Conceded residue.** A standard of care, not a guarantee. A bad eval set, a missed action class in the AOE, or a verifier whose qualification is shallow can still let errors through — which is why the eval set is independently audited (10.1 ⚖), the AOE edge defaults to abstain, verifiers are qualified (§7.5), and the bundle is lifecycle-managed (§9.6).

---

## 13. Success-criteria self-check (honest — finding 2.1)

- **One-pass grasp** → §1 + §3. ✔
- **Machine-actionable, not prose** → §7.2's `conformance_predicate` references only declared trace fields and is mechanically evaluable; §6.1 gives a computable CT function. **Holds for the deterministic path now.** Bucket-B conformance additionally requires the operator's backtested escape-rate evidence — verifiable, but supplied per deployment, not by the spec. *(No longer a bare ✔: the spec is checkable; full conformance depends on operator-supplied eval evidence.)*
- **Gap defeats "X already does this"** → §4. ✔
- **Defensible first-mover path** → §11 + attestation artifact (§11.3). ✔

---

## 14. Confidence ledger

| Area | Confidence | Basis / caveat |
| --- | --- | --- |
| Emanuel framework (beads, flywheel, DCG/stop-hook, human-token scarcity, compounding) | High | Primary source read; paraphrased. |
| DO-178C / SR 11-7 / UL 4600 mechanics | High (structure); numbers not asserted | Stable standards; specific objective counts intentionally omitted. |
| ARP6983 (frozen supervised ML, ~Q1 2026) | High | 2025–26 sources; date has slipped — confirm. |
| EASA concept paper | Med-High | Framing softened to EASA's own terms; **exact property labels to verify against the paper** (1.6). |
| FAA/EUROCAE overarching properties (intent/correctness/innocuity) | Med | Added per 1.5; property names as commonly cited — confirm exact set. |
| ISO 42001 / NIST AI RMF + GenAI Profile | High | Verified; Annex A "~38" to confirm. |
| EU AI Act phasing + GPAI CoP | High, one flag | Digital Omnibus deferral **provisional** as of mid-2026 — confirm. |
| Agent landscape incl. Five Eyes *Careful Adoption of Agentic AI Services*; CSA MAESTRO/ATF/STAR; OWASP; CoSAI; NIST CAISI | High | Five Eyes doc verified against the primary PDF (29 pp, Apr–May 2026). |
| **LAAS design (CT, escape rate, schema, obligations, lifecycle, attestation)** | Original synthesis | Not an existing standard; ratings are reasoned judgments. No body has endorsed it. |
