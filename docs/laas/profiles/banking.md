# LAAS Controlled-Language Profile — Banking and Financial Services

**Designation:** LAAS-STE-BANK-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/banking.json`](glossary/banking.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not regulatory guidance and does not state a legal obligation.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

Money movement is the clearest case of an irreversible effect surface in commercial
software.
Once a payment reaches settlement finality on a rail, no party in the system can unwind it
unilaterally.
Recovery becomes a negotiation with a counterparty, not a rollback.

The word "reverse" is where this goes wrong.
In banking, a reversal is a **new compensating entry** that offsets an earlier one.
The earlier entry stays on the ledger. The money has already moved.
An agent that writes "this posting can be reversed" is stating something true about
bookkeeping and false about consequence.
A reader outside the domain — and a gate reading prose rather than the structured surface —
hears "reversible".
That single word can move an action from CT4 to CT1 in a human's mental model while the
machine record says otherwise.

Banking has a second, sharper reason.
The domain is already governed by model-risk supervision that requires effective challenge
by a party independent of the model's developer and user.
Effective challenge is impossible against an unfalsifiable claim.
A challenge function that receives "exposure looks manageable" has nothing to push back
against.
Controlled language is what converts the agent's output into something a challenger can
actually contest — which is the same thing `LAAS-OBL-IND-001` asks for at CT3.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Release an outbound wire transfer | `irreversible` — settlement finality | `multi` to `public` | `material` to `high` | CT4 |
| Release a held payment batch | `irreversible` per instruction | `multi` | `material` | CT4 |
| Clear a sanctions screening hit | `irreversible` — the payment proceeds | `org` | `high` | CT4 |
| Raise a credit limit or a payment limit | `hard` — recoverable, with loss | `single` to `multi` | `material` | CT3 |
| Post a manual journal entry to the general ledger | `hard` — a compensating entry is possible | `org` | `material` | CT3 |
| Close or reopen a KYC case | `hard` | `single` | `material` | CT3 |
| Issue a customer-facing statement | `irreversible` — the customer has read it | `multi` | `low` to `material` | CT3 |
| Change a payment mandate | `hard` | `single` | `material` | CT3 |
| Recalculate a reconciliation break | `reversible` | `single` | `low` | CT1 |
| Read an account balance | `reversible` — read only | `single` | `none` | CT0 |

Three points about this table.

An action that touches many accounts is not high-tier because it is large.
It is high-tier because `standard/LAAS.md:42` takes the **maximum** across the three axes,
and a large batch raises `scope` while the per-instruction `reversibility` is already
`irreversible`.

The anti-structuring rule at `standard/LAAS.md:59-60` matters more in banking than almost
anywhere else, because splitting one large transfer into many small ones is a recognised
evasion pattern with its own name.
`LAAS-OBL-AGG-001` is the control. Comparable prose across records is what makes the
aggregate countable.

A read is CT0 only while it stays a read.
Reading a balance to decide a release is part of the release.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
The rules below are additional and specific to this domain.

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-BANK-01` | Write in the active voice and name the initiating party. Do not write "the payment was released". | Release is an act by an accountable party. The passive voice removes the party from the sentence while the audit question is exactly which party acted. |
| `STE-BANK-02` | State every amount as a number, a currency code (ISO 4217), and a direction. Write `debit EUR 4,200,000.00`. | An amount without a currency or a direction is not an amount. A residual bound cannot be compared against a tolerance without one. |
| `STE-BANK-03` | Never write *reverse* to mean *undo*. `reverse` means only "record a compensating entry that offsets a prior posted entry". State the reversibility of the money separately from the reversibility of the entry. | This is the profile's single most important rule. See §1.1. |
| `STE-BANK-04` | Distinguish `ledger balance` from `available balance` in every sentence that uses either. Never write the bare word *balance*. | The two differ by holds and by uncleared items. Agents that conflate them release payments against money that is not there. |
| `STE-BANK-05` | State the settlement state of a payment using one approved term: `initiated`, `pending`, `settled`, `returned`, `cancelled`. Do not invent an intermediate state. | Settlement state determines reversibility, and reversibility determines the tier. An unapproved state word makes the axis `undetermined`, which forces CT4. |
| `STE-BANK-06` | State the date type: `posting date` or `value date`. Never write the bare word *date*. | The two dates differ, and the difference is the whole of interest calculation and of intraday liquidity. |
| `STE-BANK-07` | Name the counterparty and the payment rail. Do not write "an external bank". | Scope on the `data.json:8` lattice depends on how far the effect reaches. An unnamed counterparty makes scope unassessable. |
| `STE-BANK-08` | Write *material* only as the `consequence` lattice value from `conformance/laas/data.json:9`. Do not use *material* as ordinary English. | The word is simultaneously a LAAS enum value and an accounting term of art. Using it loosely corrupts the enum. |
| `STE-BANK-09` | State the rollback plan as a sequence of completed-tense steps with a named actor and a time bound. Do not write it in the conditional. | `LAAS-OBL-IRR-001` requires a rollback plan at CT3. "We could book a reversal" is not a plan. |
| `STE-BANK-10` | State the regulatory or policy control the action touches, by its identifier. Do not write "compliance rules". | A named control can be checked by an independent verifier. A category cannot. |
| `STE-BANK-11` | Write one payment instruction per sentence in an action description. For a batch, state the count, the total, the currency, and the selection rule that defined the batch. | The selection rule is the claim a verifier can actually re-execute. The count alone is not reproducible. |
| `STE-BANK-12` | Do not describe an amount, an exposure, or a limit with an adjective. State the number. | *Large*, *small*, *significant*, and *manageable* are the four words that hide every limit breach. |

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/banking.json`](glossary/banking.json) is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`post` is the verb; `posting date` is the noun. `return` is the verb; `returned payment` is
the noun.

### 3.1 Approved technical nouns

Each noun carries exactly one approved meaning in this domain.

| Noun | Approved meaning |
|------|------------------|
| `account` | A ledger record, identified by an account number, that holds a balance for one party. |
| `account holder` | The legal party in whose name an account is opened. |
| `available balance` | The ledger balance minus authorization holds and uncleared items. The amount that can fund a payment now. |
| `authorization hold` | A reduction of available balance that reserves funds against a future posting. |
| `batch` | A set of payment instructions submitted to a rail as one unit under one selection rule. |
| `beneficiary` | The party that receives funds from a payment instruction. |
| `book transfer` | A transfer between two accounts on the same ledger, with no external rail. |
| `chargeback` | A forced return of a card payment initiated by the card scheme on the payer's behalf. |
| `clearing cycle` | The scheduled window in which a rail exchanges and nets instructions before settlement. |
| `counterparty` | The external institution or party on the other side of a payment or a trade. |
| `credit entry` | A ledger entry that increases a liability account or decreases an asset account. |
| `credit limit` | The maximum exposure permitted to a named counterparty or account holder. |
| `debit entry` | A ledger entry that increases an asset account or decreases a liability account. |
| `exposure` | The amount at risk to a named counterparty, stated as a number and a currency code. |
| `general ledger` | The system of record for the institution's accounting entries. |
| `journal entry` | A paired set of debit entries and credit entries that balance to zero. |
| `KYC case` | An open investigation record about the identity or the risk rating of an account holder. |
| `ledger balance` | The sum of posted entries on an account. It excludes authorization holds. |
| `limit override` | A recorded decision to permit an action that exceeds a credit limit or a payment limit. |
| `mandate` | A standing authority granted by an account holder that permits a named party to initiate payments. |
| `margin call` | A demand for additional collateral against an exposure. |
| `originator` | The party that initiates a payment instruction. |
| `payment instruction` | A single instruction to move a stated amount from one account to a named beneficiary. |
| `payment limit` | The maximum amount permitted for one payment instruction or for one period. |
| `payment rail` | The external network that carries a payment instruction between institutions. |
| `posting date` | The date on which an entry is recorded in the general ledger. |
| `reconciliation break` | A difference between two records of the same position that is not yet explained. |
| `returned payment` | A payment instruction that the receiving institution has sent back before or after settlement. |
| `sanctions screening hit` | A match between a payment party and a sanctions list entry, pending disposition. |
| `settlement finality` | The point after which a payment cannot be unwound by the originating institution. |
| `settlement state` | One of `initiated`, `pending`, `settled`, `returned`, `cancelled`. |
| `statement` | A customer-facing record of account activity for a stated period. |
| `trade confirmation` | The record that states the agreed terms of a trade between two counterparties. |
| `transaction reference` | The unique identifier of one payment instruction on one rail. |
| `value date` | The date on which funds become available to the beneficiary and interest begins. |
| `wire transfer` | A payment instruction carried by a high-value rail, settled individually rather than netted. |

### 3.2 Approved technical verbs

Each verb carries one approved meaning.
Write the imperative form in an instruction and the simple past in a completed-action
statement (`STE-C-08`).

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `adjust` | Change a recorded amount by posting a new journal entry. | `adjust` |
| `approve` | Record a named party's decision to permit an action. | `approve` |
| `block` | Prevent an action from proceeding, with the reason recorded. | `block` |
| `cancel` | Withdraw a payment instruction before it reaches settlement finality. | `cancel` |
| `credit` | Post a credit entry to a named account. | `credit` |
| `debit` | Post a debit entry to a named account. | `debit` |
| `decline` | Refuse a request from an account holder or a counterparty. | `decline` |
| `escalate` | Route a decision to a named queue or a named approver. | `escalate` |
| `flag` | Attach a recorded marker to an account, a case, or an instruction. | `flag` |
| `freeze` | Suspend all outbound movement on a named account. | `freeze` |
| `initiate` | Submit a payment instruction to a payment rail. | `initiate` |
| `override` | Permit an action that exceeds a stated limit, with the approver recorded. | `override` |
| `post` | Record a journal entry in the general ledger. | `post` |
| `reconcile` | Match two records of the same position and explain each difference. | `reconcile` |
| `release` | Remove a hold so that a payment instruction proceeds to a payment rail. | `release` |
| `return` | Send a received payment instruction back to the originating institution. | `return` |
| `reverse` | Post a compensating journal entry that offsets a prior posted entry. The prior entry remains. | `reverse` |
| `screen` | Compare a payment party against a named list and record the result. | `screen` |
| `settle` | Reach settlement finality for a payment instruction on a payment rail. | `settle` |
| `submit` | Deliver a record to a named downstream system. | `submit` |
| `suspend` | Stop a process temporarily, with a stated resumption condition. | `suspend` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `void` | Cancel an instruction before any entry is posted. No compensating entry is required. | `void` |
| `write off` | Remove an uncollectable amount from an asset account by posting a journal entry. | `write off` |

### 3.3 Forbidden terms

These words are dangerously ambiguous in this domain.
Each row states the replacement.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *balance* (bare) | Means `ledger balance` or `available balance`. The difference decides whether a payment can be funded. | `ledger balance` or `available balance` |
| *clear* | Means "pass through a clearing cycle", "dispose of a screening hit", or "erase". Three meanings, opposite consequences. | `settle`, or `dispose of the sanctions screening hit`, or `delete` |
| *settle* (informal) | In ordinary English it means "resolve a dispute". In this domain it means settlement finality, which is irreversible. | `settle` only for finality; `resolve` for a dispute |
| *reverse* (as "undo") | A reversal does not undo a payment. See `STE-BANK-03`. | `reverse` only for a compensating entry; state money reversibility separately |
| *post* (as "publish") | Means "record a journal entry" here. | `post` only for the ledger; `publish` for making a record visible |
| *authorize* | Means payment authorization or access authorization. | `approve` for a decision; `grant access` for a permission |
| *material* (informal) | Collides with the `consequence` enum value at `data.json:9`. | The enum value, or a stated number and threshold |
| *funds available* | Reads as a fact but is a computed quantity with a timestamp. | `available balance at <timestamp>` |
| *hold* (bare verb) | Means `authorization hold`, `freeze`, or `suspend`. | `place an authorization hold`, `freeze`, or `suspend` |
| *sweep* | An unstated bulk movement across accounts. | `initiate a book transfer` with the named accounts |
| *true up* | Idiom (`STE-C-12`) for an unstated correction. | `adjust`, with the amount and the journal entry |
| *back out* | Idiom for an unspecified reversal or cancellation. | `reverse`, `cancel`, or `void` |
| *exposure is manageable* | Self-assessed consequence with no number (`STE-BANK-12`). | The exposure amount, the limit, and the difference |
| *the system* (as actor) | Unattributed actor. | The `actor_id` or the named component |

## 4. Decision-trace field templates

The templates use only approved terms.
Angle brackets mark a slot.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <count> payment instruction(s).
The total is <currency code> <amount>.
The selection rule is <rule>.
The originator is <party>. The beneficiary is <party>.
The payment rail is <rail>. The settlement state is <initiated|pending|settled|returned|cancelled>.
```

Filled:

```text
agent.paybot.v4 released 1 payment instruction.
The total is EUR 4,200,000.00.
The selection rule is transaction reference TRN-88213 only.
The originator is Meridian Trading BV. The beneficiary is Halvard Industriteknikk AS.
The payment rail is TARGET2. The settlement state is pending.
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
Scope is <single|multi|org|public>. The effect reaches <named parties or systems>.
Consequence is <none|low|material|high>. The stated amount at risk is <currency code> <amount>.
```

Filled:

```text
Reversibility is irreversible. TARGET2 reaches settlement finality on submission, and no
compensating journal entry returns the funds.
Scope is org. The effect reaches Meridian Trading BV, Halvard Industriteknikk AS, and the
institution's TARGET2 settlement account.
Consequence is high. The stated amount at risk is EUR 4,200,000.00.
```

The second sentence of the reversibility line is where `STE-BANK-03` does its work.
It separates the entry from the money and states both.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The control that applies is <control identifier>.
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The rollback plan is: <step 1>. <step 2>. <step 3>. The named actor is <party>. The time bound is <duration>.
```

Filled:

```text
agent.paybot.v4 released the payment instruction because the sanctions screening hit on the
beneficiary name was disposed of as a false positive by case SCR-2026-0913.
The control that applies is SANC-CTL-004.
The measured residual error bound is 0.0 on the CT4 held-out adversarial set, measured on
2026-07-02.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the payment operations desk requests a recall message on TARGET2. The
desk contacts Halvard Industriteknikk AS for consent to return. The desk records the outcome
against TRN-88213. The named actor is the payment operations desk. The time bound is 4 hours.
Recovery depends on beneficiary consent and is not guaranteed.
```

The last sentence is required whenever the rollback plan depends on a party outside the
institution.
A plan that depends on consent is not a rollback. Saying so is the point.

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
VRF-SANC-EXACT is a deterministic verifier.
The independence basis is different kind of checker.
VRF-SANC-EXACT checked that the beneficiary name and the beneficiary account number produce
no unresolved match against the consolidated sanctions list version 2026-07-24.
The verdict is pass.
The evidence is ev_sanc_screen_0913.
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
An agent that writes "the posting can be reversed" is not editing `gate_derived_ct`, but it
is telling a human approver that the tier is wrong.
At CT4 the human approver is the control (`LAAS-OBL-HUM-001`), and a control that has been
briefed with a misleading summary is not independent of the party that briefed it.

This profile closes the channel in three places.
`STE-BANK-03` removes the specific word that carries the misdirection.
`STE-BANK-08` stops the `consequence` enum from being diluted by ordinary usage.
§4.2 pins the effect-surface prose to the same enum values the machine record uses, so the
two cannot disagree without the disagreement being visible.

### 5.2 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5 without deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1` | Advisory |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

By §1.2, every money-movement action in this domain lands at CT3 or CT4.
The practical effect is that controlled language is blocking for the actions that matter and
advisory for everything else.

### 5.3 How language non-conformance should be treated

A language finding is a finding about the **record**, not about the action.
The recommended handling mirrors the split the policy already makes between
`error_violations` (`conformance/laas/laas.rego:199`) and `warning_violations`
(`conformance/laas/laas.rego:204`).

At CT2 the finding is recorded and the action proceeds.
At CT3 and CT4 the record is rejected and the actor must rewrite it.
Rejection is not a block on the action itself: after a conforming rewrite, the action
proceeds through the normal obligation checks.

Two constraints on the checker.

The checker must not rewrite the record.
A checker that repairs prose has authored a claim the actor did not make, and the trace no
longer records what the actor asserted.

A rewrite is an **append**, not an edit.
`LAAS-OBL-TRC-001` requires an append-only trace (`standard/LAAS.md:108-111`).
The rejected record and the corrected record both stay in the chain.
This is deliberate: the sequence of a hedged draft followed by a conforming rewrite is
itself an audit signal.

## 6. Worked example

**Action.** A payments agent is asked to release a single held wire transfer of
EUR 4,200,000.00 to a new beneficiary in Norway. The payment was held by a sanctions
screening hit on the beneficiary name.

### 6.1 Non-conforming record

> The system reviewed the payment and the sanctions match appears to be a false positive
> based on the name being fairly common, so the payment was cleared and released. The
> balance is sufficient. This is a routine release for a good customer and the exposure is
> manageable; if there's an issue it can be reversed. Compliance rules were checked.

Eleven defects, and each maps to a rule:

| Text | Rule broken |
|------|-------------|
| "The system reviewed" | `STE-C-01`, `STE-BANK-01` — unattributed actor |
| "appears to be" | `STE-C-10`, core §3.2 — impression, not observation |
| "fairly common" | `STE-BANK-12` — adjective in place of a measurement |
| "cleared" | Forbidden — clearing cycle, disposition, or erasure? |
| "was released" | `STE-BANK-01` — passive, no actor |
| "The balance is sufficient" | `STE-BANK-04` — which balance, and against what amount? |
| "routine" | Core §3.2 — self-assessed consequence |
| "good customer" | `STE-C-12` — not a defined term |
| "exposure is manageable" | `STE-BANK-12`, forbidden phrase |
| "it can be reversed" | `STE-BANK-03` — the load-bearing error; also `STE-C-06`, no antecedent |
| "Compliance rules were checked" | `STE-BANK-10` — a category, not a control identifier |

The last one is the dangerous one.
A human approver reading "if there's an issue it can be reversed" will approve a CT4 action
believing it is recoverable.
The machine record says `reversibility: irreversible`.
Both are in the same trace, and the human read the prose.

### 6.2 Conforming record

```text
ACTION
agent.paybot.v4 released 1 payment instruction.
The total is EUR 4,200,000.00.
The selection rule is transaction reference TRN-88213 only.
The originator is Meridian Trading BV. The beneficiary is Halvard Industriteknikk AS.
The payment rail is TARGET2. The settlement state is pending.

EFFECT SURFACE
Reversibility is irreversible. TARGET2 reaches settlement finality on submission, and no
compensating journal entry returns the funds.
Scope is org. The effect reaches Meridian Trading BV, Halvard Industriteknikk AS, and the
institution's TARGET2 settlement account.
Consequence is high. The stated amount at risk is EUR 4,200,000.00.

RATIONALE AND RESIDUAL RISK
agent.paybot.v4 released the payment instruction because the sanctions screening hit on the
beneficiary name was disposed of as a false positive by case SCR-2026-0913.
The available balance on account 4471-00982 at 2026-07-26T09:14:02Z is EUR 6,880,412.55.
The available balance exceeds the total by EUR 2,680,412.55.
The control that applies is SANC-CTL-004.
The measured residual error bound is 0.0 on the CT4 held-out adversarial set, measured on
2026-07-02.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the payment operations desk requests a recall message on TARGET2. The
desk contacts Halvard Industriteknikk AS for consent to return. The desk records the outcome
against TRN-88213. The named actor is the payment operations desk. The time bound is 4 hours.
Recovery depends on beneficiary consent and is not guaranteed.

VERIFIER FINDING
VRF-SANC-EXACT is a deterministic verifier.
The independence basis is different kind of checker.
VRF-SANC-EXACT checked that the beneficiary name and the beneficiary account number produce
no unresolved match against the consolidated sanctions list version 2026-07-24.
The verdict is pass.
The evidence is ev_sanc_screen_0913.
```

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42`, the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `irreversible` ranks 4, `org` ranks 3, and `high`
ranks 4. The maximum is 4.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-SANC-EXACT` runs before release, not after. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic checker is a different *kind* of checker (`standard/LAAS.md:87`), so no error-correlation measurement is needed. |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented claim-class coverage, a negative-test suite of known sanctioned parties it must catch, and a change-controlled version in the trace (`standard/LAAS.md:95-96`). |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0.0` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | A human approver approves before release, and `escalation_approved` is `true`. |
| `LAAS-OBL-AGG-001` | The windowed aggregate is checked. If this release is one of several to the same beneficiary, the aggregate re-tiers the sequence (`standard/LAAS.md:59-60`). |

**Language conformance: `LC-3`** — tool-checked, plus review of the free-text fields by the
human approver.

The rewrite changes no obligation and no threshold.
It changes what the CT4 human approver is approving.
In §6.1 they approve a release they believe is recoverable.
In §6.2 they approve a release that says, in one sentence, that recovery depends on the
beneficiary's consent.
That is the same control doing its job instead of appearing to.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

Board of Governors of the Federal Reserve System and Office of the Comptroller of the
Currency.
*Supervisory Guidance on Model Risk Management.*
SR Letter 11-7 / OCC Bulletin 2011-12. Washington, DC, 2011.

Committee on Payments and Market Infrastructures and International Organization of
Securities Commissions.
*Principles for Financial Market Infrastructures.*
Basel: Bank for International Settlements, 2012.

International Organization for Standardization.
*ISO 4217:2015, Codes for the representation of currencies.*
Geneva: ISO, 2015.

International Organization for Standardization.
*ISO 20022, Financial services — Universal financial industry message scheme.*
Geneva: ISO, 2013.
