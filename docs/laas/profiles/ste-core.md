# LAAS Controlled-Language Core (STE-Core)

**Designation:** LAAS-STE-CORE-DRAFT-1.0
**Document type:** Base controlled-language profile (informative to LAAS, normative to profiles that adopt it)
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts the *principles* of ASD-STE100 Simplified Technical English to LLM-agent
> decision traces. It does not reproduce the ASD rule text and it does not reproduce the
> ASD controlled dictionary. The domain dictionaries in the profiles that adopt this core
> are original work. Users who need ASD-STE100 itself must obtain it from ASD.

---

## 1. Purpose

LAAS gates an action on a Consequence Tier that the gate derives from the observed effect
surface (`standard/LAAS.md:35-45`).
That part of the record is machine-derived and hard to argue with.
The rest of the record is prose.

`effect_surface_hash`, `gate_derived_ct`, and `verdict` are structured fields.
`independence_basis`, `evidence_refs`, the rationale, the residual-risk statement, and the
human-approval package are free text (`docs/laas/proposal-v1.1.md:225-256`).
Free text is where an agent can keep control of what its own record means.

An agent that writes "the change should be safe to roll back" has made no claim.
A verifier cannot refute it. A human approver can read agreement into it.
The record satisfies `LAAS-OBL-IND-001` and `LAAS-OBL-HUM-001` on paper while the actual
assurance question stays unanswered.
This is self-grading through vocabulary, and `standard/LAAS.md:33` already forbids the
substance of it:

> Any control that lets the constrained party tier, grade, or gate itself is non-conforming.

A controlled language closes that channel.
It does not add an obligation.
It removes the interpretive slack that lets an existing obligation be satisfied in form and
missed in fact.

## 2. Relationship to LAAS

This document defines no obligation, no tier, and no threshold.
It defines a writing discipline for the free-text fields of a decision-trace record, and a
recommended gate response when that discipline is not met.

**Precedence.**
This core profile does not modify LAAS normative text.
Where this profile and `standard/LAAS.md` conflict, the standard takes precedence.
Where this profile and `conformance/laas/data.json` conflict on a threshold value,
`data.json` is the machine source of truth.
Where an industry profile and this core profile conflict, the industry profile takes
precedence within its domain, and it must state the deviation explicitly.

## 3. The core rule base

Twelve rules apply in every domain.
An industry profile adopts all twelve and adds its own domain rules on top.
Each rule has a stable ID so that a language finding can name the rule it failed.

| ID | Rule | Why it matters to a decision record |
|----|------|-------------------------------------|
| `STE-C-01` | Write in the active voice. Name the actor in the subject position. | "The limit was raised" hides which party acted. `actor_id` records who ran the action; the prose must not contradict or blur it. |
| `STE-C-02` | Write one idea in one sentence. Write one instruction in one sentence. | A verifier grades claims. Two claims in one sentence can be half-true, and a `pass` verdict then covers a claim nobody checked. |
| `STE-C-03` | Keep procedural sentences to 20 words or fewer. Keep descriptive sentences to 25 words or fewer. | Length is where qualifications hide. A human approver at CT4 reads under time pressure. |
| `STE-C-04` | Give each approved term exactly one meaning and one part of speech. | The same word meaning two things across two records makes the trace unsearchable and makes claim-class coverage unprovable. |
| `STE-C-05` | Do not use a synonym for an approved term. Repeat the approved term. | Elegant variation is ambiguity. Repetition is the point, not a defect. |
| `STE-C-06` | Do not use a pronoun whose antecedent is more than one clause back. Repeat the noun. | "It was reverted" — the action, the record, or the config? |
| `STE-C-07` | Do not build a noun cluster longer than three words. | "customer payment limit override approval record" has no readable structure. Break it with prepositions. |
| `STE-C-08` | Use simple present, simple past, or the imperative. Do not use future, conditional, or subjunctive forms in a normative field. | "Would have rolled back" is not a rollback plan. `LAAS-OBL-IRR-001` needs a stated plan, not a hypothetical. |
| `STE-C-09` | Do not omit articles, auxiliaries, or relative pronouns. | Telegraphic style reads faster and audits worse. The saved words are the ones carrying the qualification. |
| `STE-C-10` | State a quantity, a unit, and a measurement basis. Do not hedge. | `LAAS-OBL-RES-001` compares a measured residual bound against a tolerance. A hedge is not a number, and it cannot be compared. |
| `STE-C-11` | Do not put a qualification in a parenthesis, a footnote, or an aside in a normative field. State it as its own sentence. | A qualification the reader can skip is a qualification the approver did not approve. |
| `STE-C-12` | Do not use metaphor, analogy, or idiom in a normative field. | "Blast radius" is a defined LAAS term. "Nuke the index" is not. |

### 3.1 The `undetermined` token

`standard/LAAS.md:44` makes any undetermined effect-surface axis default to CT4, and
`conformance/laas/data.json:11` carries that default as `default_ct_when_undetermined: 4`.

That rule only fires if the writer can say "undetermined" plainly.
A hedge is what an author writes when the honest answer is "undetermined" and the honest
answer is expensive.
Every profile that adopts this core therefore makes `undetermined` an approved term and
makes hedging a forbidden construction.
Writing `undetermined` is a conforming statement.
Writing "probably reversible" is a language non-conformance *and* an attempt to route
around the default-to-highest rule.

### 3.2 Cross-domain forbidden constructions

These are forbidden in every profile.
Each row gives the required replacement.

| Forbidden | Why | Write instead |
|-----------|-----|---------------|
| *should be fine*, *should be safe* | States a hope, not a property | The measured property, or `undetermined` |
| *mostly*, *generally*, *typically*, *usually* | Quantifier with no quantity | The count, the rate, and the denominator |
| *appears to*, *seems to*, *looks like* | Attributes the claim to an impression | The observation, and the tool that made it |
| *probably*, *likely*, *unlikely* | Unstated probability | The measured rate and its basis, or `undetermined` |
| *minor*, *routine*, *low impact*, *trivial* | Self-assessed consequence | The `consequence` lattice value from `data.json:9` |
| *reverted*, *undone* (without a target) | Implies reversibility without naming what was restored | The named artifact and the restored state |
| *etc.*, *and so on*, *among others* | Unbounded scope | The complete list, or the count and the selection rule |
| *we*, *the team*, *the system* (as actor) | Unattributed actor | The `actor_id`, or the named component |

## 4. Language-conformance levels

A profile is checked at one of four levels.
The level is a property of the *record*, not of the agent.

| Level | Meaning |
|-------|---------|
| `LC-0` | Not checked. No claim is made about the language of the record. |
| `LC-1` | Self-declared. The actor asserts the record follows the profile. No independent check. |
| `LC-2` | Tool-checked. A checker outside the actor's process validates the record against the profile glossary and rule base. |
| `LC-3` | Tool-checked, plus review of the free-text fields by the independent verifier or the human approver. |

`LC-1` is deliberately weak.
An actor asserting that its own prose is conformant is the constrained party grading
itself, which is the failure mode `standard/LAAS.md:33` names.
`LC-1` is acceptable only where the tier makes the record low-stakes.

## 5. Recommended gate policy

Controlled-language conformance is a **precondition on the record**, not a new obligation.
The gate already distinguishes blocking findings from reported ones:
`conformance/laas/laas.rego:199` collects `error_violations` and
`conformance/laas/laas.rego:204` collects `warning_violations`.
A language finding is recommended to enter that same structure.

| Effective CT | Required level | Gate response to non-conformance |
|--------------|----------------|----------------------------------|
| CT0–CT1 | `LC-1` | Advisory. Record the finding. Do not surface it. |
| CT2 | `LC-2` | **Warning.** Record the finding in the trace. The action proceeds. |
| CT3 | `LC-2`, and the verifier report must also conform | **Block.** The record must be rewritten and re-checked before the action commits. |
| CT4 | `LC-3` | **Block.** The approval package must conform before it reaches a human approver. |

Three notes on the thresholds.

**Why warn at CT2 and not block.**
CT2 permits a rehearsed rollback in place of an independent check
(`standard/LAAS.md:55`).
The record still matters, but a language defect at CT2 does not by itself defeat a control.
Blocking here would buy little and would train operators to disable the checker.

**Why block at CT3.**
CT3 is the tier at which independent, qualified pre-commit verification becomes mandatory
(`standard/LAAS.md:56`, `data.json:12`).
`LAAS-OBL-VQ-001` requires the verifier to have documented coverage of its **claim class**
(`standard/LAAS.md:95-96`).
A claim whose wording is unstable has no stable class, so coverage cannot be documented and
qualification cannot be demonstrated.
At CT3 the language defect is not cosmetic — it makes an obligation unprovable.

**Why block at CT4 before the human sees it.**
`LAAS-OBL-HUM-001` requires human approval at CT4 (`data.json:13`).
Approval is only meaningful if the approver and the record agree on what was approved.
An ambiguous package converts a human control into a signature.
The block therefore lands *upstream* of the human, not on the human's decision.

**The gate must not be the author.**
A checker that rewrites the record to make it conform has taken over authorship, and the
resulting record no longer describes what the actor claimed.
A conforming checker reports findings and blocks. It does not edit.

## 6. How controlled language strengthens the existing obligations

No obligation below is new.
Each row states what the controlled language adds to an obligation that already exists at
`standard/LAAS.md:68-81`.

| Obligation | What controlled language adds |
|------------|-------------------------------|
| `LAAS-OBL-TIER-001` | Keeps `undetermined` writable as a plain token, so the default-to-CT4 rule at `standard/LAAS.md:44` fires instead of being absorbed by a hedge. |
| `LAAS-OBL-SELF-001` | Hedged effect-surface prose is de facto self-classification. Pinning the prose to the `data.json:7-9` enum values removes the second, softer channel through which the actor describes its own blast radius. |
| `LAAS-OBL-ENF-001` | Nothing directly. Enforcement-plane integrity is structural. |
| `LAAS-OBL-TRC-001` | An append-only store fixes the *bytes*. It does not fix the *meaning*. If a term drifts between records, the content of the earlier record changes without an append. One meaning per term is what makes append-only durable. |
| `LAAS-OBL-AGG-001` | Aggregation needs comparable records. Two records describing the same effect in different words do not aggregate, and the anti-structuring rule at `standard/LAAS.md:59-60` silently under-counts. |
| `LAAS-OBL-INP-001` | Requires the record to state the provenance of input in fixed terms, so `input_trusted` cannot be asserted by an adjective. |
| `LAAS-OBL-VEN-001` | Vendor attribution and scope limits are prose claims. Fixed terms make the scope limit a statement rather than an impression. |
| `LAAS-OBL-IRR-001` | A rollback plan written in the conditional (`STE-C-08`) is not a plan. The rule makes the absence visible. |
| `LAAS-OBL-IND-001` | `independence_basis` is a free-text field carrying a load-bearing claim. Controlled terms make it checkable against the three bases at `standard/LAAS.md:87-89`. |
| `LAAS-OBL-VQ-001` | Claim-class coverage requires a stable claim class. This is the strongest dependency in the table. |
| `LAAS-OBL-RES-001` | `STE-C-10` forces a quantity with a unit and a basis, which is the only form a residual bound can be compared against `escape_rate_tolerance_by_ct` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | An ambiguous approval package makes CT4 human approval uninformed. See §5. |

## 7. Profile document format

An industry profile that adopts this core uses this section order.
The order is fixed so the profiles are interchangeable modules.

| Section | Content |
|---------|---------|
| 1 | Domain purpose and risk context: why the domain needs this, and its high-consequence actions with their effect-surface characteristics |
| 2 | Adapted STE writing rules: the twelve core rules plus 8–12 domain rules, each with a domain justification |
| 3 | Approved technical nouns and technical verbs, plus a forbidden-terms table |
| 4 | Decision-trace field templates for action description, effect surface, rationale and residual risk, and verifier finding |
| 5 | Mapping to LAAS obligations and tiers, including the domain's gate policy |
| 6 | A worked example: one realistic action, the ambiguous record, the corrected record, the tier, and the required independent checks |
| Annex A | Bibliography |

Each profile ships a derived machine-readable glossary under
[`glossary/`](glossary/).
The markdown table in section 3 is authoritative; the JSON is derived from it, in the same
relationship that `conformance/laas/data.json` holds to `standard/LAAS.md`.

## 8. Adopted profiles

| Profile | Designation | Document | Glossary |
|---------|-------------|----------|----------|
| Banking and financial services | `LAAS-STE-BANK-DRAFT-1.0` | [`banking.md`](banking.md) | [`glossary/banking.json`](glossary/banking.json) |
| Healthcare and clinical systems | `LAAS-STE-HLTH-DRAFT-1.0` | [`healthcare.md`](healthcare.md) | [`glossary/healthcare.json`](glossary/healthcare.json) |
| SEO, AdSense, and digital advertising | `LAAS-STE-ADV-DRAFT-1.0` | [`seo-adsense.md`](seo-adsense.md) | [`glossary/seo-adsense.json`](glossary/seo-adsense.json) |
| Real estate | `LAAS-STE-RE-DRAFT-1.0` | [`real-estate.md`](real-estate.md) | [`glossary/real-estate.json`](glossary/real-estate.json) |
| Building contracting, HVAC, and solar | `LAAS-STE-CON-DRAFT-1.0` | [`contracting.md`](contracting.md) | [`glossary/contracting.json`](glossary/contracting.json) |

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

International Organization for Standardization.
*ISO 24620-1:2015, Language resource management — Controlled natural language (CNL) —
Part 1: Basic concepts and principles.*
Geneva: ISO, 2015.

Kuhn, Tobias.
"A Survey and Classification of Controlled Natural Languages."
*Computational Linguistics* 40, no. 1 (2014): 121–170.

O'Brien, Sharon.
"Controlled Language and Readability."
*Translation and Cognition*, edited by Gregory M. Shreve and Erik Angelone, 143–165.
Amsterdam: John Benjamins, 2010.
