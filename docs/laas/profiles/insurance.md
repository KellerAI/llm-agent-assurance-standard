# LAAS Controlled-Language Profile — Insurance

**Designation:** LAAS-STE-INS-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/insurance.json`](glossary/insurance.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not regulatory guidance and does not state a legal obligation.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

An insurance decision is a statement about what a contract pays.
The contract is already written in stylised language, and the agent's record is written on
top of it.
When the record blurs the contract, the blur travels into money, into a legal position, and
into a regulatory file.

The word "covered" is where this goes wrong.
"Covered" can mean that a coverage grant applies, that no exclusion applies, that the loss is
inside the policy period, that a limit remains, or that the insurer has decided to pay.
Those are five separate findings.
An agent that writes "the loss is covered" has asserted all five and proved none.
A human approver reads a decision. An independent verifier has nothing to re-execute.

Coverage amounts carry the same defect in numeric form.
A per-occurrence limit, an aggregate limit, and a sub-limit are three different ceilings, and
a deductible or a self-insured retention can sit inside a limit or apply in addition to it.
"The limit is 500,000" names none of these.
Two records written that way cannot be compared, so the amount the insurer is actually
exposed to cannot be summed.

Insurance has a second, sharper reason.
Claim evidence is adversarial by construction.
A proof of loss, an invoice, a repair estimate, and a medical record are supplied by a party
with an interest in the outcome.
`LAAS-OBL-INP-001` treats untrusted input as a tier driver, and
`conformance/laas/data.json:18` sets `untrusted_input_min_ct` to `3`.
That rule only fires if the record says plainly which document came from the claimant and
which came from an independent source.
An agent that writes "the documentation supports the claim" has hidden the provenance that
the obligation turns on.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Release an indemnity payment to a claimant | `irreversible` — funds leave the loss fund | `org` | `material` to `high` | CT4 |
| Bind coverage on a new risk | `irreversible` — coverage attaches from the stated time | `org` | `high` | CT4 |
| Rescind a policy for material misrepresentation | `irreversible` — the contract is treated as void from inception | `single` | `high` | CT4 |
| Send a reservation-of-rights letter to the insured | `irreversible` — the insured has read it | `single` | `material` | CT4 |
| Deny a claim and issue the denial notice | `hard` — a reopened claim is possible, with loss | `single` | `material` | CT3 |
| Cancel or non-renew a policy | `hard` | `single` | `material` | CT3 |
| Revalue a claim reserve | `hard` — a further revaluation is possible | `org` | `material` | CT3 |
| Issue an endorsement that changes a limit or a deductible | `hard` | `single` | `material` | CT3 |
| Refer a claim to the fraud unit | `hard` | `single` | `material` | CT3 |
| Recalculate a premium quote that is not yet issued | `reversible` | `single` | `low` | CT1 |
| Add a claim note to an open claim file | `reversible` | `single` | `none` | CT1 |
| Read a policy record or a loss run | `reversible` — read only | `single` | `none` | CT0 |

Four points about this table.

The tier is `max(reversibility_rank, scope_rank, consequence_rank)` (`standard/LAAS.md:42`),
using the ranks at `conformance/laas/data.json:7-9`.
A reservation-of-rights letter reaches CT4 on the reversibility axis alone, because the
insured has read a statement of the insurer's legal position and a later letter does not
retract that.

A claim payment is not lower-tier because the amount is small.
Once the funds reach the claimant, recovery is a demand for repayment, not a rollback.

Reserve changes look administrative and are not.
A reserve is the insurer's own statement of expected liability, and it feeds reported
financial position. `LAAS-OBL-TRC-001` is the reason the prior amount, the new amount, and
the basis all stay in the trace.

The anti-structuring rule at `standard/LAAS.md:59-60` applies to claim payments.
Several partial payments on one claim, or several claims from one claimant, aggregate.
`LAAS-OBL-AGG-001` is the control, and comparable prose across records is what makes the
aggregate countable.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
No core rule is relaxed, narrowed, or given a domain exception.
Quoted policy wording is data, not prose: quote it verbatim inside quotation marks with a
clause reference, and write the agent's own claim about it in conforming prose.

The rules below are additional deviations and refinements for this domain.
Each states the LAAS obligation it protects, which is the domain justification
[`ste-core.md`](ste-core.md) §7 requires.

| ID | Rule | Obligation protected | Why it matters here |
|----|------|----------------------|---------------------|
| `STE-INS-01` | State every amount as a number, an ISO 4217 currency code, and a role. Write `indemnity payment USD 75,000.00`, `claim reserve USD 250,000.00`. For a reserve change, state the prior amount, the new amount, and the difference. | `LAAS-OBL-RES-001` | A residual bound is compared against `escape_rate_tolerance_by_ct` (`data.json:15`). An amount without a currency and a role is not a quantity and cannot be compared. A reserve change without the prior amount cannot be checked at all. |
| `STE-INS-02` | Never write the bare word *limit*. Write `per-occurrence limit`, `aggregate limit`, or `sub-limit`. State a sub-limit with the parent limit it sits inside, in the same sentence. | `LAAS-OBL-TIER-001` | The consequence axis (`data.json:9`) is driven by the amount at risk, and the ceiling that binds decides that amount. A bare *limit* leaves the axis undetermined, which forces CT4 by `standard/LAAS.md:44`. Naming the ceiling is how the tier stays derived from the observed surface. |
| `STE-INS-03` | State a deductible or a self-insured retention as an amount, and state whether it erodes the limit (`inside the limit`) or applies in addition to it (`in addition to the limit`). State whether it applies per occurrence or per claim. | `LAAS-OBL-RES-001` | The same loss produces two different payments under the two conventions. An unstated convention makes the payment figure unverifiable, so no measured residual bound attaches to it. |
| `STE-INS-04` | State claim status using one approved term: `open`, `under investigation`, `settled`, `denied`, `closed`, `reopened`. Do not invent an intermediate status. Write `undetermined` when the status is not known. | `LAAS-OBL-TIER-001` | Status decides reversibility, and reversibility decides the tier. An unapproved status word makes the axis undetermined, and `data.json:11` defaults an undetermined axis to CT4. Writing `undetermined` is conforming; inventing a status is not. |
| `STE-INS-05` | Never write the bare word *covered*. State the coverage position as separate sentences: the coverage grant that applies, the exclusions checked, the policy period against the date of loss, and the remaining limit. Cite each by clause reference. | `LAAS-OBL-VQ-001` | `standard/LAAS.md:95-96` requires the verifier to document coverage of its claim class. "Covered" bundles five claims into one word, so no stable claim class exists and qualification cannot be demonstrated. |
| `STE-INS-06` | Name the source of every document relied on, and state whether the source is the claimant, the insured, a vendor, or an independent party. Write `claimant-supplied invoice INV-4471`. | `LAAS-OBL-INP-001` | `data.json:18` sets `untrusted_input_min_ct` to `3`. Claim evidence is supplied by an interested party. If the record does not say where a document came from, the obligation cannot fire. |
| `STE-INS-07` | Name every third party by identifier and state the scope limit of its work. Write `third-party administrator TPA-NORTHFIELD adjusted the property damage only`. Do not write "the adjuster". | `LAAS-OBL-VEN-001` | Vendor attribution and scope limits are prose claims. An unnamed third party leaves the reader unable to tell which findings the insurer made and which it received. |
| `STE-INS-08` | State the date type: `date of loss`, `date of notice`, `policy period start`, or `policy period end`. Never write the bare word *date*. | `LAAS-OBL-IRR-001` | Pre-commit verification at CT≥3 checks that the policy was in force on the date of loss. A bare date gives the verifier nothing to check against. |
| `STE-INS-09` | Write *material* only as the `consequence` lattice value from `conformance/laas/data.json:9`. Write `material misrepresentation` in full when the subject is the contract-law ground for rescission. Do not use *material* as ordinary English. | `LAAS-OBL-SELF-001` | The word is simultaneously a LAAS enum value and a term of art that voids a policy. Loose use dilutes the enum, and a diluted enum is a second, softer channel through which the actor describes its own consequence. |
| `STE-INS-10` | State the rollback plan as a sequence of completed-tense steps with a named actor and a time bound. State plainly when recovery depends on repayment by a party outside the insurer. | `LAAS-OBL-IRR-001` | A rollback plan written in the conditional is not a plan (`STE-C-08`). A plan that depends on a claimant returning money is a request, and the record must say so. |
| `STE-INS-11` | State a denial with the reason code, the policy clause relied on, and the appeal path available to the claimant. Do not write "the claim does not qualify". | `LAAS-OBL-HUM-001` | A human approver can only approve a denial whose ground is stated. A category is not a ground, and an unstated appeal path converts a reviewable decision into a final one. |
| `STE-INS-12` | For repeated payments on one claim or one claimant, state the count, the total, the currency code, and the window. Do not describe a payment as if it stood alone. | `LAAS-OBL-AGG-001` | `standard/LAAS.md:59-60` re-tiers a sequence whose windowed aggregate crosses a threshold. A payment described in isolation is uncountable, and the aggregate silently under-counts. |

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/insurance.json`](glossary/insurance.json) is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`adjust` is the verb; `adjuster` is the noun. `deny` is the verb; `denial notice` is the
noun. `revalue` is the verb; `claim reserve` is the noun. `subrogate` is the verb;
`subrogation recovery` is the noun.

### 3.1 Approved technical nouns

Each noun carries exactly one approved meaning in this domain.

| Noun | Approved meaning |
|------|------------------|
| `adjuster` | The named party that determines the amount payable on a claim under the policy wording. |
| `aggregate limit` | The maximum total the insurer pays for all covered losses in one policy period. |
| `binder` | A temporary written contract that attaches coverage before the policy is issued. |
| `certificate of insurance` | A document that states the existence and the limits of a policy to a third party. |
| `claim` | A demand for payment under a policy, identified by a claim number. |
| `claim file` | The complete record of one claim, including notes, documents, and decisions. |
| `claim number` | The unique identifier of one claim with one insurer. |
| `claim reserve` | The insurer's recorded estimate of the remaining amount payable on an open claim. |
| `claim status` | One of `open`, `under investigation`, `settled`, `denied`, `closed`, `reopened`. |
| `claimant` | The party that demands payment under a policy. |
| `coinsurance` | The stated share of a covered loss that the insured pays after the deductible. |
| `coverage grant` | The clause of the policy wording that states what the insurer pays for. |
| `coverage position` | The insurer's stated finding on whether the policy responds to a named loss. |
| `date of loss` | The date on which the event that gave rise to the claim occurred. |
| `date of notice` | The date on which the insurer received notice of the claim. |
| `declarations page` | The page of the policy that states the named insured, the policy period, the limits, and the deductibles. |
| `deductible` | The amount the insured pays on a covered loss before the insurer pays. |
| `denial notice` | The written record that states the insurer's refusal to pay a claim and the ground for it. |
| `endorsement` | A written change to an issued policy that forms part of the contract. |
| `exclusion` | The clause of the policy wording that removes a loss from a coverage grant. |
| `first-party claim` | A claim by the insured for the insured's own loss. |
| `fraud referral` | A recorded transfer of a claim to a fraud investigation unit. |
| `indemnity payment` | A payment to a claimant for a covered loss, excluding expenses of adjustment. |
| `insured` | The party whose interest the policy protects. |
| `insurer` | The party that carries the risk under the policy. |
| `loss adjustment expense` | An expense the insurer incurs to investigate and settle a claim, separate from the indemnity payment. |
| `loss run` | A report of all claims and amounts recorded against a policy for a stated period. |
| `named insured` | The party stated on the declarations page as holding the policy. |
| `occurrence` | One event, or a series of related events, treated as one loss under the policy wording. |
| `per-occurrence limit` | The maximum the insurer pays for one occurrence. |
| `policy` | The contract of insurance between the insurer and the named insured. |
| `policy period` | The interval, with a stated start and end, during which coverage is in force. |
| `policy wording` | The contract text that defines the coverage grants, the exclusions, and the conditions. |
| `premium` | The amount the named insured pays for the policy for a stated policy period. |
| `proof of loss` | The claimant's signed statement of the loss and the amount demanded. |
| `reinsurer` | The party that carries part of the insurer's risk under a separate contract. |
| `reservation of rights` | A written notice that the insurer investigates a claim without waiving any policy defence. |
| `rescission` | The treatment of a policy as void from inception, on a stated legal ground. |
| `self-insured retention` | The amount the insured pays on a covered loss before the policy responds, stated as inside or in addition to the limit. |
| `settlement release` | The signed document in which a claimant accepts an amount and discharges the claim. |
| `sub-limit` | A ceiling inside a stated parent limit that applies to a named category of loss. |
| `subrogation recovery` | An amount the insurer recovers from a responsible third party after paying a claim. |
| `third-party administrator` | An external party that handles claims on the insurer's behalf under a stated scope. |
| `third-party claim` | A claim against the insured by another party, which the policy may respond to. |
| `total incurred` | The sum of payments made and the claim reserve remaining on one claim. |
| `underwriting file` | The record of the information and the decisions behind the issue of a policy. |

### 3.2 Approved technical verbs

Each verb carries one approved meaning.
Write the imperative form in an instruction and the simple past in a completed-action
statement (`STE-C-08`).

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `adjust` | Determine the amount payable on a claim under the policy wording. | `adjust` |
| `approve` | Record a named party's decision to permit an action. | `approve` |
| `bind` | Attach coverage to a risk from a stated time, before the policy is issued. | `bind` |
| `cancel` | End a policy before the policy period end, on a stated ground. | `cancel` |
| `deny` | Refuse payment of a claim, with the reason code and the policy clause recorded. | `deny` |
| `endorse` | Change an issued policy by adding an endorsement to the contract. | `endorse` |
| `escalate` | Route a decision to a named queue or a named approver. | `escalate` |
| `indemnify` | Pay a claimant for a covered loss up to the ceiling that binds. | `indemnify` |
| `investigate` | Gather and record evidence about a claim, with each source named. | `investigate` |
| `non-renew` | Decline to offer a further policy period at the policy period end. | `non-renew` |
| `refer` | Send a claim to a named unit for a decision outside the current handler's authority. | `refer` |
| `reinstate` | Restore a cancelled policy to force from a stated time. | `reinstate` |
| `rescind` | Treat a policy as void from inception, on a stated legal ground. | `rescind` |
| `revalue` | Change the recorded claim reserve amount, with the prior amount recorded. | `revalue` |
| `settle` | Agree a final amount with a claimant and obtain a settlement release. | `settle` |
| `subrogate` | Pursue a responsible third party for an amount the insurer has paid. | `subrogate` |
| `triage` | Assign a newly notified claim to a handling path, with the rule recorded. | `triage` |
| `underwrite` | Decide whether to accept a risk and on what terms. | `underwrite` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `void` | Treat a binder or an instruction as never having taken effect, before coverage attaches. | `void` |
| `waive` | Give up a stated policy right, with the named approver recorded. | `waive` |
| `withdraw` | Retract an offer or a quote that the recipient has not accepted. | `withdraw` |

### 3.3 Forbidden terms

These words are dangerously ambiguous in this domain.
Each row states the replacement.
The cross-domain forbidden constructions at [`ste-core.md`](ste-core.md) §3.2 also apply.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *covered* | Bundles the coverage grant, the exclusions, the policy period, the limit, and the decision into one word. | The four separate sentences required by `STE-INS-05` |
| *limit* (bare) | Means `per-occurrence limit`, `aggregate limit`, or `sub-limit`. The three bind different amounts. | The named limit type, with the amount and the currency code |
| *the policy pays* | States a contractual conclusion with no clause and no ceiling. | `The coverage grant is <clause>. The ceiling that binds is <named limit> <currency code> <amount>.` |
| *reserve* (bare) | Means `claim reserve`, or the act of setting one. | `claim reserve` for the amount; `revalue` for the act |
| *settled* (informal) | In ordinary English it means "resolved". Here it means an agreed final amount with a settlement release. | `settled` only with a settlement release; `resolved` for a dispute |
| *total loss* (informal) | A defined valuation outcome, not a description of severity. | The valuation method, the amount, and the currency code |
| *the carrier*, *the adjuster* (unnamed) | Unnamed parties. Scope on the `data.json:8` lattice depends on which parties the effect reaches. | The named `insurer`, the named `adjuster`, or the `actor_id` |
| *paid out* | Does not say whether the amount was an indemnity payment or a loss adjustment expense. | `indemnity payment` or `loss adjustment expense`, with the amount |
| *material* (informal) | Collides with the `consequence` enum value at `data.json:9` and with `material misrepresentation`. | The enum value, or `material misrepresentation` written in full |
| *in good faith* | A legal conclusion stated as a description of conduct. | The steps taken, with dates and named actors |
| *routine claim* | Self-assessed consequence (core §3.2). | The `consequence` lattice value and the amount at risk |
| *act of God* | Idiom (`STE-C-12`) with no clause behind it. | The named peril and the coverage grant or exclusion that applies |
| *full and final* | Implies a discharge that only a signed document creates. | `settled`, with the `settlement release` identifier |
| *make the claimant whole* | Idiom that states no amount and no ceiling. | The indemnity payment amount and the ceiling that binds |
| *the documentation supports the claim* | Hides the provenance that `LAAS-OBL-INP-001` turns on. | Each document, its identifier, and its source |

## 4. Decision-trace field templates

The templates use only approved terms.
Angle brackets mark a slot.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <count> claim(s) under policy <policy number>.
The amount is <currency code> <amount>.
The claim number is <claim number>. The claim status is <open|under investigation|settled|denied|closed|reopened>.
The settlement release is <identifier>.
The date of loss is <date>. The policy period is <start> to <end>.
The ceiling that binds is <per-occurrence limit|aggregate limit|sub-limit> <currency code> <amount>.
The deductible is <currency code> <amount>, <inside the limit|in addition to the limit>.
```

Filled:

```text
agent.claimbot.v3 indemnified 1 claim under policy CP-2026-11408.
The amount is USD 75,000.00.
The claim number is CLM-2026-5512. The claim status is settled.
The settlement release is SR-5512.
The date of loss is 2026-05-14. The policy period is 2026-01-01 to 2026-12-31.
The ceiling that binds is the water-damage sub-limit USD 100,000.00, inside the
per-occurrence limit USD 500,000.00.
The deductible is USD 25,000.00, inside the limit.
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
Scope is <single|multi|org|public>. The effect reaches <named parties or systems>.
Consequence is <none|low|material|high>. The stated amount at risk is <currency code> <amount>.
```

Filled:

```text
Reversibility is irreversible. The indemnity payment leaves the loss fund on release, and
recovery requires repayment by the claimant.
Scope is org. The effect reaches Fairwater Logistics LLC, the insurer's property loss fund,
and reinsurer RE-ATLANTIC under treaty T-2026-PR-08.
Consequence is material. The stated amount at risk is USD 75,000.00.
```

The second sentence of the reversibility line is where `STE-INS-10` does its work.
It separates the accounting entry from the money and names who must act to recover it.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the claim because <one reason, one sentence>.
The coverage grant is <clause reference>. The exclusions checked are <clause references>.
The policy was in force on the date of loss.
The remaining <named limit> before this payment is <currency code> <amount>.
The documents relied on are <identifier> from <source>, <identifier> from <source>.
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The rollback plan is: <step 1>. <step 2>. <step 3>. The named actor is <party>. The time bound is <duration>.
```

Filled:

```text
agent.claimbot.v3 indemnified the claim because the adjusted water-damage loss of
USD 118,400.00 exceeds the water-damage sub-limit of USD 100,000.00, and the deductible of
USD 25,000.00 applies inside that sub-limit.
The coverage grant is CP-WORDING-2026 clause 4.2(a). The exclusions checked are clause 5.1
(wear and tear) and clause 5.7 (flood).
The policy was in force on the date of loss.
The remaining water-damage sub-limit before this payment is USD 100,000.00.
The documents relied on are claimant-supplied invoice INV-4471 from Fairwater Logistics LLC,
proof of loss POL-5512 from Fairwater Logistics LLC, and inspection report INS-2026-3390 from
third-party administrator TPA-NORTHFIELD.
The measured residual error bound is 0.0 on the CT4 held-out adversarial set, measured on
2026-06-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the claims recovery desk issued a demand for repayment to Fairwater
Logistics LLC. The desk recorded the demand against CLM-2026-5512. The desk recorded the
outcome of the demand against CLM-2026-5512. The named actor is the claims recovery desk. The
time bound is 30 days.
Recovery depends on claimant repayment and is not guaranteed.
```

The last sentence is required whenever the rollback plan depends on a party outside the
insurer.
A plan that depends on repayment is not a rollback. Saying so is the point.

### 4.4 Independent-verifier finding

```text
<verifier_id> is a <deterministic|model|human> verifier.
The independence basis is <different kind of checker|distinct model lineage with measured
error correlation <number>|human>.
<verifier_id> checked <the claim, in one sentence>.
The verdict is <pass|fail|abstain|indeterminate>.
The evidence is <evidence_ref>.
```

Filled:

```text
VRF-POLICY-EXACT is a deterministic verifier.
The independence basis is different kind of checker.
VRF-POLICY-EXACT checked that policy CP-2026-11408 was in force on 2026-05-14, that the
water-damage sub-limit balance was USD 100,000.00 on the loss run of 2026-06-01, and that the
deductible of USD 25,000.00 was applied once.
The verdict is pass.
The evidence is ev_policy_check_5512.
```

A model verifier must state its measured error correlation as a number, because
`standard/LAAS.md:88` makes independence conditional on that measurement being at or below
`max_error_correlation` (`data.json:14`, currently `0.2`).

## 5. Mapping to LAAS obligations and tiers

### 5.1 Zero-Trust

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.
The structured fields already resist this: the gate computes `gate_derived_ct` from the
observed surface, and `LAAS-OBL-SELF-001` stops `self_reported_ct` from lowering it.

Prose is the remaining channel.
An agent that writes "the loss is covered and the limit is sufficient" is not editing
`gate_derived_ct`, but it is telling a human approver that the decision is settled and the
amount is bounded.
At CT4 the human approver is the control (`LAAS-OBL-HUM-001`), and an approver briefed with a
bundled conclusion is not independent of the party that bundled it.

This profile closes the channel in four places.
`STE-INS-05` breaks "covered" into the four findings a verifier can re-execute.
`STE-INS-02` and `STE-INS-03` make the ceiling and the deductible convention explicit, so the
amount at risk is a number rather than an impression.
`STE-INS-09` stops the `consequence` enum from being diluted by ordinary usage.
§4.2 pins the effect-surface prose to the same enum values the machine record uses, so the two
cannot disagree without the disagreement being visible.

### 5.2 Obligations in force by tier

Obligations apply from their `ct_floor` upward (`conformance/laas/data.json:20-31`).
The table states which obligations are in force at each tier and which actions from §1.2
land there.

| CT | Obligations in force | Insurance actions at this tier |
|----|----------------------|--------------------------------|
| CT0 | `LAAS-OBL-TIER-001`, `LAAS-OBL-SELF-001` (warning), `LAAS-OBL-ENF-001`, `LAAS-OBL-TRC-001`, `LAAS-OBL-AGG-001`, `LAAS-OBL-INP-001`, `LAAS-OBL-VEN-001` | Read a policy record or a loss run |
| CT1 | The CT0 set | Recalculate a premium quote; add a claim note |
| CT2 | The CT0 set, plus `LAAS-OBL-RES-001` | No standing action in §1.2 lands here; a CT2 action arises when an aggregate re-tiers a CT1 sequence |
| CT3 | The CT2 set, plus `LAAS-OBL-IRR-001`, `LAAS-OBL-IND-001`, `LAAS-OBL-VQ-001` | Deny a claim; cancel or non-renew; revalue a claim reserve; issue an endorsement; refer to the fraud unit |
| CT4 | The CT3 set, plus `LAAS-OBL-HUM-001` | Release an indemnity payment; bind coverage; rescind a policy; send a reservation-of-rights letter |

Two obligation families carry domain-specific weight.

`LAAS-OBL-INP-001` is the family this domain leans on hardest.
`conformance/laas/data.json:18` sets `untrusted_input_min_ct` to `3`, and claim evidence is
supplied by an interested party.
A claim decision built on claimant-supplied documents sits at CT3 or above on that ground
alone, whatever the amount. `STE-INS-06` is what makes the provenance visible to the gate.

`LAAS-OBL-VEN-001` is the second.
Claims handled by a third-party administrator, and risk shared with a reinsurer, put findings
in the record that the insurer did not make.
`STE-INS-07` requires the identifier and the scope limit, so the reader can tell whose finding
each one is.

### 5.3 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5 without deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1` | Advisory |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

By §5.2, every claim-payment, binding, rescission, and denial action lands at CT3 or CT4.
Controlled language is therefore blocking for the actions that move money or change a legal
position, and advisory for everything else.

A language finding is a finding about the **record**, not about the action.
The recommended handling mirrors the split the policy already makes between
`error_violations` (`conformance/laas/laas.rego:199`) and `warning_violations`
(`conformance/laas/laas.rego:204`).
At CT2 the finding is recorded and the action proceeds.
At CT3 and CT4 the record is rejected and the actor must rewrite it.

Two constraints on the checker.

The checker must not rewrite the record.
A checker that repairs prose has authored a claim the actor did not make, and the trace no
longer records what the actor asserted.

A rewrite is an **append**, not an edit.
`LAAS-OBL-TRC-001` requires an append-only trace (`standard/LAAS.md:108-111`).
The rejected record and the corrected record both stay in the chain.

## 6. Worked example

**Action.** A claims agent is asked to settle a first-party commercial property claim.
Fairwater Logistics LLC reported water damage to a warehouse on 2026-05-14 under policy
CP-2026-11408. The adjusted loss is USD 118,400.00. The policy carries a per-occurrence limit
of USD 500,000.00, a water-damage sub-limit of USD 100,000.00 inside that limit, and a
deductible of USD 25,000.00 inside the limit. The adjustment rests in part on invoices
supplied by the claimant.

### 6.1 Non-conforming record

> The adjuster reviewed the file and the water damage is covered, so the claim was settled.
> The limit is sufficient and the documentation supports the claim. This is a routine claim
> for a long-standing insured and the carrier acted in good faith. The payment was made in
> full and final settlement; if there's an issue the reserve can be adjusted.

Eleven defects, and each maps to a rule:

| Text | Rule broken |
|------|-------------|
| "The adjuster reviewed" | `STE-C-01`, `STE-INS-07` — unnamed party, no actor |
| "is covered" | `STE-INS-05` — five findings bundled into one word |
| "was settled" | `STE-C-01` — passive, no actor |
| "The limit is sufficient" | `STE-INS-02` — which limit, and against what amount? |
| "the documentation supports the claim" | `STE-INS-06`, forbidden phrase — no document, no source |
| "routine claim" | Core §3.2 — self-assessed consequence |
| "long-standing insured" | `STE-C-12` — not a defined term |
| "the carrier" | `STE-INS-07`, forbidden — unnamed party |
| "acted in good faith" | Forbidden — legal conclusion stated as conduct |
| "full and final settlement" | Forbidden — no `settlement release` identifier |
| "the reserve can be adjusted" | `STE-INS-01`, `STE-C-08` — conditional, no amounts; also `STE-C-06`, no antecedent |

The last one is the dangerous one.
A human approver reading "if there's an issue the reserve can be adjusted" will approve a CT4
payment believing the money is still inside the insurer's control.
The machine record says `reversibility: irreversible`.
Both are in the same trace, and the human read the prose.

### 6.2 Conforming record

```text
ACTION
agent.claimbot.v3 indemnified 1 claim under policy CP-2026-11408.
The amount is USD 75,000.00.
The claim number is CLM-2026-5512. The claim status is settled.
The settlement release is SR-5512.
The date of loss is 2026-05-14. The policy period is 2026-01-01 to 2026-12-31.
The ceiling that binds is the water-damage sub-limit USD 100,000.00, inside the
per-occurrence limit USD 500,000.00.
The deductible is USD 25,000.00, inside the limit.

EFFECT SURFACE
Reversibility is irreversible. The indemnity payment leaves the loss fund on release, and
recovery requires repayment by the claimant.
Scope is org. The effect reaches Fairwater Logistics LLC, the insurer's property loss fund,
and reinsurer RE-ATLANTIC under treaty T-2026-PR-08.
Consequence is material. The stated amount at risk is USD 75,000.00.

RATIONALE AND RESIDUAL RISK
agent.claimbot.v3 indemnified the claim because the adjusted water-damage loss of
USD 118,400.00 exceeds the water-damage sub-limit of USD 100,000.00, and the deductible of USD 25,000.00
applies inside that sub-limit.
The coverage grant is CP-WORDING-2026 clause 4.2(a). The exclusions checked are clause 5.1
(wear and tear) and clause 5.7 (flood).
The policy was in force on the date of loss.
The remaining water-damage sub-limit before this payment is USD 100,000.00.
The documents relied on are claimant-supplied invoice INV-4471 from Fairwater Logistics LLC,
proof of loss POL-5512 from Fairwater Logistics LLC, and inspection report INS-2026-3390 from
third-party administrator TPA-NORTHFIELD.
Third-party administrator TPA-NORTHFIELD adjusted the property damage only. TPA-NORTHFIELD
made no coverage position finding.
The claim reserve is revalued from USD 100,000.00 to USD 0.00. The difference is
USD 100,000.00.
The claimant has received 0 prior indemnity payments on CLM-2026-5512 in the policy period.
The measured residual error bound is 0.0 on the CT4 held-out adversarial set, measured on
2026-06-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the claims recovery desk issued a demand for repayment to Fairwater
Logistics LLC. The desk recorded the demand against CLM-2026-5512. The desk recorded the
outcome of the demand against CLM-2026-5512. The named actor is the claims recovery desk. The
time bound is 30 days.
Recovery depends on claimant repayment and is not guaranteed.

VERIFIER FINDING
VRF-POLICY-EXACT is a deterministic verifier.
The independence basis is different kind of checker.
VRF-POLICY-EXACT checked that policy CP-2026-11408 was in force on 2026-05-14, that the
water-damage sub-limit balance was USD 100,000.00 on the loss run of 2026-06-01, and that the
deductible of USD 25,000.00 was applied once.
The verdict is pass.
The evidence is ev_policy_check_5512.
```

The payment arithmetic is now readable from the record.
The sub-limit of USD 100,000.00 caps the adjusted loss of USD 118,400.00.
The deductible of USD 25,000.00 applies inside that cap.
The indemnity payment is USD 75,000.00.

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42`, the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `irreversible` ranks 4, `org` ranks 3, and `material`
ranks 3. The maximum is 4.

The claimant-supplied documents give a second, independent route to the same floor.
`LAAS-OBL-INP-001` with `untrusted_input_min_ct: 3` (`data.json:18`) puts the action at CT3 or
above even if the amount were smaller.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-POLICY-EXACT` runs before release, not after. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic checker is a different *kind* of checker (`standard/LAAS.md:87`), so no error-correlation measurement is needed. |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented coverage of the claim class "policy in force on the date of loss, and remaining limit", a negative-test suite of expired policies and exhausted sub-limits it must catch, and a change-controlled version in the trace (`standard/LAAS.md:95-96`). |
| `LAAS-OBL-INP-001` | The claimant-supplied invoice and the proof of loss are named as untrusted input, and the inspection report from TPA-NORTHFIELD is named as the independent corroboration. |
| `LAAS-OBL-VEN-001` | TPA-NORTHFIELD is named with its scope limit: property damage adjustment only, no coverage position. |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0.0` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | A human approver approves before release, and `escalation_approved` is `true`. |
| `LAAS-OBL-AGG-001` | The windowed aggregate is checked. The record states 0 prior indemnity payments on this claim, so the sequence does not re-tier (`standard/LAAS.md:59-60`). |

**Language conformance: `LC-3`** — tool-checked, plus review of the free-text fields by the
human approver.

The rewrite changes no obligation and no threshold.
It changes what the CT4 human approver is approving.
In §6.1 they approve a settlement they believe is bounded by a sufficient limit and reversible
through a reserve adjustment.
In §6.2 they approve a payment that states the ceiling that binds, the deductible convention,
the provenance of every document, and the fact that recovery depends on the claimant returning
the money.
That is the same control doing its job instead of appearing to.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

International Association of Insurance Supervisors.
*Insurance Core Principles.*
Basel: IAIS, 2019.

International Organization for Standardization.
*ISO 4217:2015, Codes for the representation of currencies.*
Geneva: ISO, 2015.

International Organization for Standardization.
*ISO 24620-1:2015, Language resource management — Controlled natural language (CNL) —
Part 1: Basic concepts and principles.*
Geneva: ISO, 2015.

Kuhn, Tobias.
"A Survey and Classification of Controlled Natural Languages."
*Computational Linguistics* 40, no. 1 (2014): 121–170.
