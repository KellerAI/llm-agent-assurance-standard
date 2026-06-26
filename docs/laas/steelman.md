# Steelman: LAAS is the ETOPS of autonomous action

- **Prepared by:** KellerAI (Claude Code synthesis)
- **Date:** 2026-06-21
- **Scope:** The strongest affirmative case for the LLM-Agent Assurance Standard (LAAS), built on the convergent practice of three high-consequence industries — aviation, banking, and autonomous driving.
- **Sources:** Four kellerai.blog Engineering-Discipline articles (aviation + banking) and the autonomous-driving safety canon (UL 4600, ISO 21448 SOTIF, ISO 26262, SAE J3016).

---

## Thesis

The strongest case for LAAS is not "AI agents are risky, so add guardrails."
It is that **every mature industry that learned to operate unreliable components in irreversible, high-consequence regimes converged on LAAS's exact architecture.**
Four independent KellerAI analyses, each starting from a different aviation or banking doctrine, all reconstruct the same four mechanisms LAAS already implements.
A third industry — autonomous driving — reaches the same design while running **the same kind of open-world, statistically-behaved machine learning that GenAI is.**
When unrelated lines of reasoning, on different substrates, derive one design, that design is not a preference; it is the attractor.
LAAS is that attractor, written down and made machine-checkable.

## Pillar 1 — *Autonomy Is a Range You Earn*: the binary must become a staircase

Aviation abolished the blunt 60-minute twin-engine rule and replaced it with ETOPS: a graduated, evidence-based, revocable envelope, governed per *(aircraft, engine)* pair rather than per aircraft.
This is LAAS's foundational claim, vindicated by precedent.
LAAS's governance unit is the **(action, consequence-tier)** pair, and the tier is gate-derived, never self-asserted (`LAAS-OBL-TIER-001`; the gate computes CT0–CT4 from the observed effect surface).
The article proves that "is this agent trusted?" is the wrong question — aviation already discarded its equivalent.
The right question is the one LAAS asks: what has this action, on this task-class, earned?
The objection that tiering is bureaucratic overhead dies here: ETOPS' staircase *expanded* twin-engine routes, and the envelope is revocable (`effective_ct = max(gate_ct, cumulative_ct)`), exactly as ETOPS authority contracts when reliability regresses.

## Pillar 2 — *Reliability You Can Bank*: the range is priced in measured failure data

ETOPS range is earned only by demonstrating an In-flight Shutdown rate below progressively tighter thresholds (0.05 → 0.01 per 1,000 hours); banking earns model authority only by backtesting predicted loss bounds against outcomes, with authority auto-contracting when exceptions breach the traffic-light regime.
LAAS is the same instrument for actions.
`LAAS-OBL-RES-001` requires a backtested residual escape rate within a declared per-tier tolerance (2% at CT2, 0.5% at CT3, 0% at CT4) — the IFSD-rate discipline, transposed.
This forecloses the most common objection to LAAS ("99% model accuracy is good enough; your tiers are paranoid"): aviation does not grant range on a good quarter, it grants it on a low and stable measured rate over enough hours to exclude luck.
LAAS's escape-rate-with-tolerance and cumulative blast-radius aggregation (`LAAS-OBL-AGG-001`) are precisely the priced, continuously-monitored, auto-revocable authority both industries already trust.

## Pillar 3 — *Always a Runway*: range is derived from reachable fallbacks, never asserted

ETOPS-180 does not mean "approved for three hours over water" — it means never exceed three single-engine hours from a runway you can actually reach.
Range is derived from always-reachable adequate diversion airports; the NZ7571 failure mode was committing on a *forecast* runway instead of an *observed* one.
This is the deepest vindication of LAAS's abstention-and-rollback design.
LAAS defaults to the strictest tier when the effect surface is undetermined (`default expected_ct := 4`) and blocks rather than guesses — the agent must always have a reachable "runway": an independent pre-commit verifier (`LAAS-OBL-IRR-001` at CT≥3), human approval (`LAAS-OBL-HUM-001` at CT4), or abstention.
The forecast-versus-observed rule is LAAS's untrusted-input doctrine (`LAAS-OBL-INP-001`: untrusted input raises the tier or blocks) and its append-only decision trace (`LAAS-OBL-TRC-001`) — the pre-computed point of safe return for every action.
This refutes "abstention makes agents useless": the always-reachable-runway rule is what *permits* the long route, not what forbids it.

## Pillar 4 — *Aviation & Banking Already Solved Hallucination*: govern integrity, not accuracy

Hallucination is not a model-accuracy problem; it is a system-integrity problem.
Hazardously Misleading Information is being wrong *without warning*.
The fix is structural: deterministic verification of checkable claims, bounded and abstaining probabilistic error, complete traceability, and independent validation (SR 11-7 → SR 26-2) — never "make the model better."
This is the argument that makes LAAS necessary rather than optional.
LAAS attaches assurance to the action, not the model — it does not certify the LLM, it gates each effect.
Its obligations map one-to-one onto the three guarantees: independent, qualified, low-correlation pre-commit verification (`LAAS-OBL-IND-001`, `LAAS-OBL-VQ-001`) is deterministic plus effective-challenge integrity; the residual escape bound is bounded probabilistic error with abstention; the append-only chained trace is complete traceability.
The enforcement plane runs out-of-process and signed (`LAAS-OBL-ENF-001`) — the agent cannot disable its own gate — which is the structural answer to "we already have safety prompts."
A prompt is in-process; an ETOPS monitor and a banking validation team are not.

## The buttress — Autonomous driving: the same surface, the same discipline

Aviation avionics and bank risk models are engineered, parametric systems.
A skeptic's last refuge is therefore: "ETOPS and SR 26-2 governed deterministic engineering — you cannot transpose them to a stochastic neural network."
Autonomous driving demolishes that objection, because an autonomous vehicle's perception and planning stack *is* a deep-learning, open-world, non-deterministic system — the same epistemic surface as GenAI: sensor noise, distribution shift, long-tail edge cases, and confident-but-wrong perception.
It is the one safety-critical industry whose core component fails the way an LLM fails, and it converged on precisely LAAS's architecture.

- **Operational Design Domain (ODD)** (SAE J3016): the system is authorized to act only inside a validated envelope of conditions; outside it, it must not drive. This is LAAS's gate-derived consequence tier and effect-surface bounding — an undetermined or out-of-envelope surface defaults to the strictest tier (`default expected_ct := 4`), exactly as an out-of-ODD condition forbids autonomous operation.
- **Minimal Risk Condition (MRC)**: when perception degrades or the vehicle exits its ODD, it executes a minimal-risk maneuver — a controlled stop or pull-over. This is LAAS's abstention-and-rollback design (`LAAS-OBL-IRR-001`, `LAAS-OBL-HUM-001`) and *Always a Runway*'s reachable diversion: the car always keeps a shoulder; the agent always keeps a block-or-abstain path.
- **SOTIF — Safety Of The Intended Functionality** (ISO 21448): a discipline created specifically because ML perception produces hazards with no component fault — "correct hardware, wrong answer." That is the precise shape of hallucination and Hazardously Misleading Information. SOTIF is the autonomous-driving name for *integrity, not accuracy*, and LAAS is its instrument at the action layer.
- **Graduated automation (J3016 levels) with data-earned ODD expansion**: automation is tiered, and the operating envelope is widened only on demonstrated field performance — disengagement and miles-per-intervention rates, scenario coverage. This is LAAS's CT0–CT4 tiers plus the earned, revocable envelope and the backtested residual escape rate (`LAAS-OBL-RES-001`); the disengagement rate is the road's IFSD rate.
- **UL 4600 — the safety case**: autonomous-driving safety is not a checklist but a structured, auditable *argument* with evidence that residual risk is acceptable, continuously updated from operating data. This is LAAS's append-only decision trace (`LAAS-OBL-TRC-001`) and per-tier residual tolerance — assurance attached to the operation, with evidence, not to the model at enrollment.
- **Operator accountability**: autonomous-driving regimes hold the deploying operator accountable, not the perception-model vendor — echoing SR 26-2's "you cannot outsource the obligation to govern" and LAAS's vendor-attribution rule (`LAAS-OBL-VEN-001`).

The buttress's punchline: autonomous driving is the existence proof on GenAI's own substrate.
Aviation and banking show the discipline works for engineered systems; autonomous driving shows it works for the same unreliable, open-world machine learning that GenAI is — at highway speed, with lives at stake.
The skeptic's final move — "neural nets are too unlike engines and risk models for these standards to transfer" — names the exact case the road already refuted.

## Why the convergence is the argument

Each industry doctrine, followed to its conclusion, reconstructs a face of LAAS.

| Industry doctrine | Source precedent | LAAS mechanism it derives |
|---|---|---|
| Graduated, revocable, evidence-earned envelope per unit/task | ETOPS tiers (Earned Range); SAE J3016 levels + ODD | Gate-derived CT0–CT4 per (action, tier); revocable `effective_ct` |
| Authority priced in measured failure data | ETOPS IFSD rate (Reliability You Can Bank); banking backtesting; AV disengagement rate | Backtested residual escape rate + per-tier tolerance (`OBL-RES-001`, `OBL-AGG-001`) |
| Range derived from an always-reachable fallback | ETOPS diversion runway (Always a Runway); AV Minimal Risk Condition | Abstain/block + independent verify + human approval (`OBL-IRR/HUM/INP/TRC-001`) |
| Govern integrity (undetected error), not accuracy | DO-178C + SR 26-2 (Aviation & Banking); SOTIF / UL 4600 | Out-of-process signed gate + verification + traceability (`OBL-ENF/IND/VQ-001`) |

## The closing case

Three industries — aviation, banking, and autonomous driving — independently learned to operate unreliable components in irreversible, high-consequence regimes.
Each scaled rigor by consequence, earned authority by measured reliability, kept a reachable point of safe return, and governed integrity over accuracy.
Followed to its conclusion, each reconstructs a face of LAAS — and the third does so while running the very class of model in question.
LAAS is therefore not a novel imposition on AI; it is the first faithful port of ETOPS, SR 26-2, and UL 4600 discipline to the agent-action layer.
To reject LAAS is to claim that the only three industries that safely fly twins over oceans, let models move billions, and drive neural networks at highway speed were each wrong to do so — and to inherit the burden of explaining why.
These precedents show that burden cannot be discharged.

## Sources

- Always a Runway — <https://kellerai.blog/always-a-runway>
- Reliability You Can Bank — <https://kellerai.blog/reliability-you-can-bank>
- Autonomy Is a Range You Earn — <https://kellerai.blog/earned-range>
- Aviation & Banking Already Solved Hallucination — <https://kellerai.blog/aviation-and-banking-solved-this>
- Autonomous-driving safety canon: UL 4600 (safety case), ISO 21448 (SOTIF), ISO 26262 (functional safety), SAE J3016 (driving-automation levels and ODD).
- LAAS internals: `standard/LAAS.md`, `docs/laas/proposal-v1.1.md`, `conformance/laas/laas.rego` (package `kellerai.laas.actions`), `conformance/laas/data.json`.
