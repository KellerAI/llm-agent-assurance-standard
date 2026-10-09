# LAAS Controlled-Language Profile — Legal and Contracts

**Designation:** LAAS-STE-LEGAL-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-2.0.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/legal.json`](glossary/legal.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not legal advice, is not regulatory guidance, and does not state a legal
> obligation.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

In this domain the record and the action are the same object.
A payment is an event that a record describes afterwards.
An executed amendment *is* the obligation. There is no underlying fact the text merely
reports.
An agent that writes a loose sentence into a contract has not described a risk. It has
created one.

The word "binding" is where this goes wrong.
An agent that writes "the draft is not binding yet" is making a claim about a legal
conclusion, not about a system state.
Whether a document binds depends on offer, acceptance, consideration, authority, and the
notice provision — none of which the agent observed.
A reader takes "not binding" as a statement of fact and reads the effect surface as
`reversible`. The gate, reading the observed surface, may have recorded
`irreversible`.

Two features of the domain make this worse than in most others.

**Effects fire on delivery, not on completion.**
A breach notice, a termination notice, and a waiver take effect when the counterparty
receives them. There is no settlement window and no pending state. The agent cannot
retract the notice; it can only negotiate about it afterwards.

**Some effects are destructive of a protection rather than of an asset.**
Disclosing a privileged document to a counterparty can waive privilege over the whole
subject matter. Nothing is deleted and nothing is spent. The protection is simply gone,
and no rollback restores it. An agent describing that action as "sent a document" has
described the mechanics and omitted the consequence.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Execute or countersign an agreement or an amendment | `irreversible` — binding on execution | `org` to `public` | `high` | CT4 |
| Disclose a document to a counterparty or in discovery | `irreversible` — privilege may be waived | `org` | `high` | CT4 |
| File or serve a document in a court matter | `irreversible` — the filing is on the public docket | `public` | `high` | CT4 |
| Waive a contractual right or a recorded breach | `irreversible` — the waiver takes effect on notice | `org` | `high` | CT4 |
| Send a termination notice or a breach notice | `irreversible` — the notice starts the cure period | `multi` | `material` | CT4 |
| Release a legal hold | `hard` — deleted material does not return | `org` | `material` | CT3 |
| Accept a redline that changes an indemnity or a limitation of liability clause | `hard` — the draft can be re-opened by consent | `multi` | `material` | CT3 |
| Grant or withhold consent to an assignment | `hard` | `multi` | `material` | CT3 |
| Send a draft to a counterparty under a non-disclosure agreement | `hard` | `multi` | `material` | CT3 |
| Update a matter status in the matter management system | `reversible` | `single` | `low` | CT1 |
| Read a clause in an executed agreement | `reversible` — read only | `single` | `none` | CT0 |

Three points about this table.

Scope is rarely `single` here, even for a one-document action.
An amendment binds two legal entities and every affiliate the definition of "Group" reaches.
By `standard/LAAS.md:42` the tier takes the maximum across the three axes, so a small
document with a wide definition is a high-tier action.

A missed deadline is an action.
A cure period, a limitation period, and a filing deadline all convert inaction into an
irreversible outcome at a fixed time. An agent that holds a draft past a deadline has taken
the action of letting the right lapse, and the trace must record it as one.

A read is CT0 only while it stays a read.
Reading a clause to decide whether to countersign is part of the countersignature.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
No core rule is weakened. The rules below are additional and specific to this domain.
Two of them refine a core rule, and §2.1 states each refinement as an explicit deviation.

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-LEGAL-01` | Write in the active voice and name the executing party and the signatory. Do not write "the amendment was executed". | Execution is an act by a party with authority. The passive voice removes exactly the fact an auditor needs: who bound the company. |
| `STE-LEGAL-02` | Capitalise a Defined Term on every use once the instrument defines it. Write the undefined ordinary word in lower case. Never mix the two in one record. Cite the defining clause for every Defined Term the record uses, in the §4.5 block. | See deviation 1 in §2.1. A Defined Term and its ordinary homonym have different scope, and the capital letter is the only signal that distinguishes them. |
| `STE-LEGAL-03` | Cite an authority in the form given in §2.1 deviation 2. Give the instrument, the clause number, and the version or the execution date. Do not write "the contract says". | An independent verifier must retrieve the cited text. A citation that does not resolve cannot be contested. |
| `STE-LEGAL-04` | State whether a document is a `draft`, an `execution version`, or an `executed agreement`. Never write the bare word *contract* for a document in negotiation. | The three states differ in whether the action is reversible. An unapproved state word makes the reversibility axis `undetermined`, which forces CT4 by `standard/LAAS.md:44`. |
| `STE-LEGAL-05` | State a deadline as an absolute timestamp with a time zone, and state the event it runs from. Write `2026-08-07T23:59:00+02:00, 10 calendar days from the notice date`. | "Within ten days" has three readings: business days, calendar days, and days from receipt. The reading decides whether the right survives. |
| `STE-LEGAL-06` | Distinguish `representation`, `warranty`, `covenant`, and `condition precedent` in every sentence that uses any of them. Never write the bare word *promise*. When the record states the strength of a **contractual** obligation, write `shall` for a binding obligation, `may` for a permission, and `must not` for a prohibition. Do not write *will*, *should*, or *agrees to*. The record's own prose stays in simple present, simple past, or the imperative (`STE-C-08`). | The four instruments have different remedies, and collapsing them hides which remedy the action created or gave up. The three modals are the only forms that carry a strength unambiguously when the record quotes an obligation. |
| `STE-LEGAL-07` | Name the governing law and the forum when an action creates, changes, or gives up a right. Do not write "under the agreement". | The same clause has different effects in different forums. Scope on the `data.json:8` lattice cannot be assessed without the forum. |
| `STE-LEGAL-08` | State the liability position as a number, a currency code (ISO 4217), and a cap basis. Write `capped at USD 2,000,000.00, equal to 12 months of fees`. Write `uncapped` when there is no cap. | The cap is the amount at risk, and the amount at risk is what the `consequence` axis at `data.json:9` ranks. `LAAS-OBL-TIER-001` derives the tier from that observed surface, and "liability is limited" gives the gate nothing to rank. |
| `STE-LEGAL-09` | Record the privilege status of every document the action touches: `privileged`, `not privileged`, or `undetermined`. | Privilege loss is the domain's clearest irreversible effect. `undetermined` is a conforming answer and forces CT4; silence is not an answer at all. |
| `STE-LEGAL-10` | Name the authority basis for the action: the signatory, the delegation instrument, and its clause. Do not write "authorised". | Authority is the fact that decides whether the company is bound. It is a citable instrument, not an adjective. |
| `STE-LEGAL-11` | Write *material* only as the `consequence` lattice value from `conformance/laas/data.json:9`. For the contractual concept write `Material Adverse Change` or the defined threshold. | The word is simultaneously a LAAS enum value and a term of art. Using it loosely corrupts the enum. |
| `STE-LEGAL-12` | State the rollback plan as a sequence of completed-tense steps with a named actor and a time bound. State plainly when rollback requires counterparty consent. | `LAAS-OBL-IRR-001` requires a rollback plan at CT3. A plan that depends on the counterparty is a negotiation, and the record must say so. |

### 2.1 Stated deviations from the core rule base

This profile deviates from [`ste-core.md`](ste-core.md) §3 in two places.
`ste-core.md:56-57` requires a profile to state any such deviation explicitly.

Deviation 1 is more restrictive than the core profile: it narrows what the writer may do.
Deviation 2 is a **scoped exemption**, and it is the only place in this profile that is less
restrictive than the core profile. It relaxes `STE-C-11` inside a citation and nowhere else.
Neither deviation changes a LAAS obligation, a tier, or a threshold.

**Deviation 1 — Defined Terms are capitalised, and capitalisation is load-bearing.**

`STE-C-04` gives each approved term exactly one meaning and one part of speech, and
`STE-C-05` forbids synonyms. The core profile assumes one surface form per meaning.
In this domain a single surface form carries two meanings that differ only in case.
`Confidential Information` as an instrument defines it is not the same set as confidential
information in ordinary use; `Services` under clause 2 is not the same set as services.

This profile therefore treats the capitalised form and the lower-case form as **two distinct
approved terms**, not one term written two ways. `STE-LEGAL-02` requires the capitalised
form on every use once the instrument defines it, and requires the record to cite the
defining clause for every Defined Term it uses, in the §4.5 block.

*Justification.* `LAAS-OBL-VQ-001` requires the verifier to have documented coverage of its
**claim class** (`standard/LAAS.md:95-96`). A claim about `Confidential Information` and a
claim about confidential information are different claim classes with different scopes.
If the record does not distinguish them, the verifier cannot state which class it covered,
and qualification cannot be demonstrated. `LAAS-OBL-TRC-001` adds the second reason: an
append-only trace fixes the bytes, and a term whose scope drifts between records changes the
meaning of an earlier record without an append (`ste-core.md:242`).

**Deviation 2 — citation notation uses a fixed form and is exempt from the parenthesis ban.**

`STE-C-11` forbids putting a qualification in a parenthesis in a normative field.
Standard citation form places load-bearing elements — the court and the year of a case, the
jurisdiction of a statute — inside parentheses. Rewriting them as prose produces a longer
sentence that is harder to resolve and easier to get wrong.

This profile permits parentheses **only** inside a citation, and only for the court, the
year, the jurisdiction, or the Defined Term that a definition clause defines. A parenthesis
anywhere else in a normative field remains a `STE-C-11` violation. The permitted forms are:

| Authority | Required form | Example |
|-----------|---------------|---------|
| Clause of an instrument | `<instrument short name> cl. <number>, <execution date or version>` | `MSA-2024-0417 cl. 11.3, executed 2024-04-17` |
| Definition in an instrument | `<instrument short name> cl. <number> (definition of <Defined Term>)` | `MSA-2024-0417 cl. 1.1 (definition of Confidential Information)` |
| Statute | `<short title> <section> (<jurisdiction>)` | `Uniform Commercial Code § 2-207 (New York)` |
| Case | `<case name>, <reporter citation> (<court> <year>)` | `Raffles v Wichelhaus, 2 H & C 906 (Exch 1864)` |
| Court filing | `<matter number>, docket entry <number>, filed <date>` | `2026-CV-01188, docket entry 42, filed 2026-06-30` |

*Justification.* `LAAS-OBL-IND-001` makes the independence of a verifier a load-bearing
claim, and an independent verifier can only contest a claim it can check
(`ste-core.md:247`). A citation that does not resolve to one text is not checkable, so the
verifier's finding covers nothing. `LAAS-OBL-TRC-001` requires the same citation to resolve
to the same text when the trace is read years later, which is why the version or the
execution date is mandatory rather than optional.

The parenthesis exemption is narrow by design. It buys a resolvable citation and nothing
else.

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/legal.json`](glossary/legal.json) is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`execute` is the verb; `execution version` is the noun. `waive` is the verb; `waiver` is
the noun. `mark up` is the verb; `redline` is the noun.

### 3.1 Approved technical nouns

Each noun carries exactly one approved meaning in this domain.

| Noun | Approved meaning |
|------|------------------|
| `agreement` | A document that two or more named parties have executed and that binds them. |
| `amendment` | An executed document that changes a term of an existing agreement. |
| `assignment` | A transfer of a party's rights under an agreement to a named third party. |
| `authority basis` | The named signatory, the delegation instrument, and the clause that permits a party to bind an entity. |
| `breach notice` | A notice that states a named failure to perform, the clause breached, and the cure period. |
| `clause` | A numbered provision of an instrument, identified by its number and the instrument. |
| `condition precedent` | An event that must occur before a stated obligation becomes due. |
| `confidentiality obligation` | A duty not to disclose defined information to a named class of recipient for a stated period. |
| `conflict check` | A recorded search for a relationship that would prevent a party from acting in a matter. |
| `consideration` | The value each party gives that makes an agreement enforceable. |
| `counterparty` | The external legal entity on the other side of an instrument or a negotiation. |
| `covenant` | A promise to do or not to do a stated act during the term. |
| `cure period` | The stated period in which a breaching party may remedy a named breach before a remedy becomes available. |
| `Defined Term` | A word or phrase that an instrument defines in a numbered clause and capitalises on every use. |
| `delegation instrument` | The document that grants a named person authority to bind an entity, such as a power of attorney or a board resolution. |
| `discovery request` | A formal demand in litigation that a party produce named documents or answer named questions. |
| `docket entry` | One numbered item on a court's public record of a matter. |
| `draft` | A document in negotiation that no party has executed. |
| `effective date` | The date stated in an instrument on which its obligations begin. |
| `execution version` | The final text of a document, agreed by all parties and awaiting signature. |
| `filing deadline` | The absolute time by which a document must reach a named court or registry. |
| `force majeure clause` | The clause that excuses performance on the occurrence of a named event outside a party's control. |
| `forum` | The court or the arbitral body named in an instrument to hear a dispute. |
| `governing law` | The legal system that an instrument names to interpret it. |
| `indemnity` | An obligation of one party to cover a named loss of another party. |
| `legal hold` | An instruction that suspends deletion of named records because litigation is reasonably anticipated. |
| `limitation of liability clause` | The clause that caps or excludes a party's liability, stated with a cap amount and a cap basis. |
| `limitation period` | The period after which a claim can no longer be brought. |
| `master services agreement` | The framework agreement whose terms govern individual statements of work. |
| `matter` | One identified piece of legal work, identified by a matter number. |
| `non-disclosure agreement` | An agreement whose primary obligation is a confidentiality obligation. |
| `notice provision` | The clause that states how a notice must be delivered, to whom, and when it takes effect. |
| `party` | A named legal entity that an instrument binds. |
| `privilege status` | One of `privileged`, `not privileged`, `undetermined`, for a named document. |
| `privilege log` | The record listing documents withheld from production and the ground for withholding each. |
| `redline` | A marked-up draft that shows every proposed change against a named prior version. |
| `renewal term` | A further period for which an agreement continues after the initial term. |
| `representation` | A statement of fact about the present or the past, made by a named party on a stated date. |
| `settlement agreement` | An executed agreement that resolves a dispute and states what each party gives up. |
| `side letter` | A separate executed document that varies an agreement between fewer than all parties to it. |
| `signatory` | The named natural person who signs on behalf of a party. |
| `statement of work` | A document that states the scope, the deliverables, and the fees under a master services agreement. |
| `termination for cause` | Termination permitted by a named breach that the breaching party did not cure. |
| `termination for convenience` | Termination permitted without a breach, on stated notice. |
| `term sheet` | A document that records agreed commercial points and states which of them bind. |
| `waiver` | A recorded decision by a party not to enforce a named right, effective on notice. |
| `warranty` | A promise that a stated fact is and remains true, with a stated remedy if it is not. |

### 3.2 Approved technical verbs

Each verb carries one approved meaning.
Write the imperative form in an instruction and the simple past in a completed-action
statement (`STE-C-08`).

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `accept` | Agree to a named proposed change or a named offer, with the accepting party recorded. | `accept` |
| `acknowledge` | Record receipt of a document without agreeing to its terms. | `acknowledge` |
| `amend` | Change a term of an existing agreement by an executed amendment. | `amend` |
| `assign` | Transfer a party's rights under an agreement to a named third party. | `assign` |
| `certify` | State, as a named person, that a stated fact is true, with the basis recorded. | `certify` |
| `cite` | Identify an authority in the form required by §2.1 deviation 2. | `cite` |
| `countersign` | Add the second party's signature to a document the first party has already signed. | `countersign` |
| `cure` | Remedy a named breach within the cure period. | `cure` |
| `disclose` | Make a named document or fact available to a named recipient. | `disclose` |
| `escalate` | Route a decision to a named approver or a named queue. | `escalate` |
| `execute` | Complete a document as binding by the signature of an authorised signatory. | `execute` |
| `file` | Deliver a document to a named court or registry so that it enters the record. | `file` |
| `indemnify` | Cover a named loss of another party under an indemnity. | `indemnify` |
| `negotiate` | Exchange proposed changes to a draft with a named counterparty. | `negotiate` |
| `notify` | Deliver a notice in the form and to the address the notice provision requires. | `notify` |
| `novate` | Replace a party to an agreement with a named third party, with all parties consenting. | `novate` |
| `produce` | Deliver named documents in response to a discovery request. | `produce` |
| `mark up` | Record every proposed change to a draft against a named prior version, producing a redline. | `mark up` |
| `rescind` | Unwind an agreement so that the parties return to their pre-agreement position. | `rescind` |
| `serve` | Deliver a document to a named party in the manner the forum requires. | `serve` |
| `settle` | Conclude a dispute by an executed settlement agreement. | `settle` |
| `submit` | Deliver a record to a named downstream system or a named internal reviewer. | `submit` |
| `terminate` | End an agreement under a named termination clause, with the effective date stated. | `terminate` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `waive` | Give up a named right, effective on notice, with the waiving party recorded. | `waive` |
| `withhold` | Refuse a consent or a document, with the named ground recorded. | `withhold` |

### 3.3 Forbidden terms

These words are dangerously ambiguous in this domain.
Each row states the replacement.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *contract* (for a document in negotiation) | Collapses `draft`, `execution version`, and `agreement`, which differ in reversibility. | `draft`, `execution version`, or `agreement` |
| *binding* / *not binding* (bare) | A legal conclusion the agent did not observe. | The document state, the authority basis, and the execution date |
| *sign* (as "execute") | Signing without authority does not bind. The two are different acts. | `execute` with the authority basis, or `acknowledge` |
| *material* (informal) | Collides with the `consequence` enum value at `data.json:9` and with the contractual term of art. | The enum value, or `Material Adverse Change` with its defined threshold |
| *reasonable efforts*, *best efforts* (undefined) | An unmeasured standard read differently in each forum. | The named acts required, or the clause that defines the standard |
| *promptly*, *as soon as practicable*, *in due course* | A deadline with no time. | An absolute timestamp and the event it runs from (`STE-LEGAL-05`) |
| *standard terms*, *boilerplate*, *market standard* | Asserts that a clause needs no review. | The clause citation and the text that differs from the named template |
| *the contract says* | An unresolvable citation. | The citation form at §2.1 deviation 2 |
| *including* (without *without limitation*) | Reads as exhaustive to one party and illustrative to the other. | `including without limitation`, or the complete list |
| *subject to* | Hides whether the item is a condition precedent, a carve-out, or a cross-reference. | `condition precedent`, or the named carve-out and its clause |
| *term* (bare) | Means the duration of an agreement or a provision of it. | `renewal term`, `initial term`, or `clause` |
| *counsel reviewed it* | An unattributed and unscoped review claim. | The named reviewer, the scope reviewed, and the date |
| *low legal risk*, *we're covered* | Self-assessed consequence with no basis. | The `consequence` lattice value and the liability position (`STE-LEGAL-08`) |
| *waive* (as "ignore") | A waiver is an effective act that gives up a right permanently. | `waive` only for the act; `did not enforce on this occasion` for a one-off |
| *settle* (as "finish") | Means conclude a dispute by an executed settlement agreement. | `settle` only for a dispute; `complete` for finishing work |
| *the system*, *the team* (as actor) | Unattributed actor. | The `actor_id` or the named component |

## 4. Decision-trace field templates

The templates use only approved terms.
Angle brackets mark a slot.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <count> document(s) in matter <matter number>.
The document state is <draft|execution version|agreement>.
The instrument is <citation>. The clauses changed are <clause numbers>.
The selection rule is <rule>.
The parties are <party> and <party>. The signatory is <name>, <role>.
The authority basis is <delegation instrument> <clause>.
```

Filled:

```text
agent.contractbot.v2 executed 1 document in matter MAT-2026-0441.
The document state is execution version.
The instrument is MSA-2024-0417 cl. 11.3, executed 2024-04-17.
The clauses changed are 11.3 and 14.2.
The selection rule is amendment 3 to MSA-2024-0417 only.
The parties are Northvale Systems Ltd and Orsted Marine Services AS.
The signatory is J. Ramanathan, Director of Commercial.
The authority basis is board resolution BR-2025-11 cl. 4(b).
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
Scope is <single|multi|org|public>. The effect reaches <named parties or entities>.
Consequence is <none|low|material|high>. The liability position is <capped at <currency code>
<amount>, <cap basis>|uncapped>.
The privilege status of every document this action touches is <privileged|not privileged|undetermined>.
```

Filled:

```text
Reversibility is irreversible. The amendment binds both parties on execution, and reversal
requires an executed further amendment that Orsted Marine Services AS has not agreed to.
Scope is org. The effect reaches Northvale Systems Ltd, Orsted Marine Services AS, and every
entity inside the definition of Group at MSA-2024-0417 cl. 1.1.
Consequence is high. The liability position is uncapped for the indemnity at cl. 14.2.
The privilege status of every document this action touches is not privileged.
```

The second sentence of the reversibility line is where `STE-LEGAL-12` does its work.
It states that reversal needs the counterparty, and it names the counterparty.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The authority for the change is <citation>.
The governing law is <law>. The forum is <forum>.
The exact-verified claim class is <claim class>. The gate verifier for it is <verifier_id>.
The open-world claim class is <claim class, or none>.
The backtest observed <k> escapes in <n> samples on <named evaluation set>, measured on <date>.
The residual error bound is <number>, the one-sided <confidence> upper bound by the <Wilson|Clopper-Pearson> method.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The backtest verdict is <pass|fail|indeterminate>. The evidence is <evidence_id>.
The rollback plan is: <step 1>. <step 2>. <step 3>. The named actor is <party>. The time bound is <duration>.
```

The residual-risk lines follow [`ste-core.md`](ste-core.md) §3.3.
Write `none` for the open-world claim class only when the gate verifier checks every claim
the action depends on, and then omit the four backtest sentences.
At CT4 the tolerance is `0`, and no finite backtest demonstrates it
(`docs/laas/backtest.md:116`), so the backtest verdict at CT4 is `indeterminate`.

Filled:

> Illustrative values. The sample size, escape count, bound, and evidence IDs in this example are not measured data.

```text
agent.contractbot.v2 executed the amendment because the renewal term at MSA-2024-0417 cl. 3.2
expires on 2026-08-31 and the counterparty returned the execution version unchanged.
The authority for the change is board resolution BR-2025-11 cl. 4(b).
The governing law is the law of England and Wales. The forum is the courts of England and
Wales, MSA-2024-0417 cl. 22.1.
The exact-verified claim class is the location of each change in MSA-2024-0417. The gate
verifier for it is VRF-CLAUSE-DIFF.
The open-world claim class is the effect of each changed clause on the liability position.
The backtest observed 0 escapes in 300 samples on the CT4 held-out adversarial clause set,
measured on 2026-06-19.
The residual error bound is 0.008938, the one-sided 0.95 upper bound by the Wilson method.
The tolerance for CT4 is 0 from conformance/laas/data.json.
The backtest verdict is indeterminate. The evidence is ev_backtest_86bcfce27a3cf97f.
The rollback plan is: the legal operations team prepares a further amendment that restores
cl. 14.2. The team requests execution by Orsted Marine Services AS. The team records the
outcome against MAT-2026-0441. The named actor is the legal operations team. The time bound
is 10 business days.
Reversal depends on counterparty consent and is not guaranteed.
```

The last sentence is required whenever the rollback plan depends on a party outside the
entity. A plan that depends on consent is not a rollback. Saying so is the point.

### 4.4 Independent-verifier finding

```text
<verifier_id> is a <deterministic|model|human> verifier.
The independence basis is <different kind of checker|distinct model lineage with measured
error correlation <number>|human>.
<verifier_id> checked <the claim, in one sentence>.
The verdict is <pass|fail|indeterminate> for a deterministic verifier.
The verdict is <pass|fail|abstain|indeterminate> for a model or human verifier.
The evidence is <evidence_ref>.
```

Filled:

```text
VRF-CLAUSE-DIFF is a deterministic verifier.
The independence basis is different kind of checker.
VRF-CLAUSE-DIFF checked that the execution version differs from MSA-2024-0417 only at
cl. 11.3 and cl. 14.2, and that no Defined Term in cl. 1.1 changed.
VRF-CLAUSE-DIFF did not check the liability position.
The verdict is pass.
The evidence is ev_clause_diff_0441.
```

A model verifier must state its measured error correlation as a number, because
`standard/LAAS.md:88` makes independence conditional on that measurement being at or below
`max_error_correlation` (`data.json:14`, currently `0.2`).

### 4.5 Defined-term and citation block

Every record that uses a Defined Term carries this block once, before the action
description. It exists to satisfy `STE-LEGAL-02` and `STE-LEGAL-03` without repeating the
defining clause in every sentence.

```text
DEFINED TERMS
<Defined Term> is defined at <citation>.
<Defined Term> is defined at <citation>.
```

Filled:

```text
DEFINED TERMS
Group is defined at MSA-2024-0417 cl. 1.1 (definition of Group).
Confidential Information is defined at MSA-2024-0417 cl. 1.1 (definition of Confidential
Information).
```

## 5. Mapping to LAAS obligations and tiers

### 5.1 Zero-Trust

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.
The structured fields already resist this: the gate computes `gate_derived_ct` from the
observed surface, and `LAAS-OBL-SELF-001` stops `self_reported_ct` from lowering it.

Prose is the remaining channel, and in this domain the prose is unusually persuasive,
because it reads like a legal conclusion rather than an opinion.
An agent that writes "the draft is not binding yet" is not editing `gate_derived_ct`. It is
telling a human approver that the gate is wrong, in the register of an answer rather than a
guess.
At CT4 the human approver is the control (`LAAS-OBL-HUM-001`), and a control briefed with a
confident misstatement is not independent of the party that briefed it.

This profile closes the channel in four places.
`STE-LEGAL-04` replaces the conclusion *binding* with the observable document state.
`STE-LEGAL-09` forces `privileged`, `not privileged`, or `undetermined`, so a privilege
question cannot be answered by silence; `undetermined` then triggers the default-to-CT4 rule
at `standard/LAAS.md:44`, which is what `LAAS-OBL-TIER-001` protects.
`STE-LEGAL-11` stops the `consequence` enum from being diluted by the term of art.
§4.2 pins the effect-surface prose to the same enum values the machine record uses, so the
two cannot disagree without the disagreement being visible.

### 5.2 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5 without deviation.
Its two stated deviations are deviations from the core **rule base**, and §2.1 states both.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1` | Advisory |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

By §1.2, every action that binds a party, gives up a right, or discloses a document lands at
CT3 or CT4. The practical effect is that controlled language is blocking for the actions
that matter and advisory for everything else.

### 5.3 Obligation mapping for this domain

Each row states what this profile's rules add to an obligation that already exists at
`standard/LAAS.md:68-81` and `conformance/laas/data.json:19-32`. No obligation below is new.

| Obligation | CT floor | What this profile adds |
|------------|----------|------------------------|
| `LAAS-OBL-TIER-001` | 0 | `STE-LEGAL-04` and `STE-LEGAL-09` keep `undetermined` writable for document state and privilege status, so the default-to-CT4 rule at `standard/LAAS.md:44` fires instead of being absorbed by a legal conclusion. |
| `LAAS-OBL-SELF-001` | 0 | `STE-LEGAL-11` stops *material* from being used as ordinary English, which is the softest channel through which an agent re-describes its own consequence. |
| `LAAS-OBL-ENF-001` | 0 | Nothing directly. Enforcement-plane integrity is structural. |
| `LAAS-OBL-TRC-001` | 0 | Deviation 1 fixes the scope of each Defined Term, and deviation 2 makes every citation resolve to one version, so an earlier record does not change meaning without an append. |
| `LAAS-OBL-AGG-001` | 0 | `STE-C-02` as adopted, plus `STE-LEGAL-03`, makes clause changes countable. A series of small amendments to the same master services agreement aggregates only if each record names its clauses. |
| `LAAS-OBL-INP-001` | 0 | A redline received from a counterparty is untrusted input. `STE-LEGAL-03` requires the received version to be cited, so `untrusted_input_min_ct` (`data.json:18`, currently `3`) applies to an identified document. |
| `LAAS-OBL-VEN-001` | 0 | `STE-LEGAL-10` states the authority basis, which is the scope limit on any party acting for another. |
| `LAAS-OBL-IRR-001` | 3 | `STE-LEGAL-12` requires a rollback plan in completed-tense steps and requires the record to say when reversal needs counterparty consent. |
| `LAAS-OBL-IND-001` | 3 | Deviation 2 makes the cited authority retrievable, which is the precondition for a verifier contesting the claim at all. |
| `LAAS-OBL-VQ-001` | 3 | Deviation 1 gives the claim class a stable scope, so documented coverage under `standard/LAAS.md:95-96` is provable. |
| `LAAS-OBL-RES-001` | 2 | `STE-C-10` as adopted forces a quantity, a unit, and a measurement basis, which is the only form a measured residual bound can be compared against `escape_rate_tolerance_by_ct` (`data.json:15`). The escape rate is a rate, not a money amount; `STE-LEGAL-08` fixes the separate money figure that the `consequence` axis ranks. |
| `LAAS-OBL-HUM-001` | 4 | `STE-LEGAL-02` and `STE-LEGAL-03` make the approval package state which text the approver is approving, rather than a paraphrase of it. |

### 5.4 How language non-conformance should be treated

A language finding is a finding about the **record**, not about the action.
The recommended handling mirrors the split the policy already makes between
`error_violations` (`conformance/laas/laas.rego:200`) and `warning_violations`
(`conformance/laas/laas.rego:205`).

At CT2 the finding is recorded and the action proceeds.
At CT3 and CT4 the record is rejected and the actor must rewrite it.

Two constraints on the checker.

The checker must not rewrite the record.
A checker that repairs prose has authored a claim the actor did not make. In this domain the
risk is sharper than elsewhere: a checker that "corrects" a clause reference has changed
which obligation the record describes.

A rewrite is an **append**, not an edit.
`LAAS-OBL-TRC-001` requires an append-only trace (`standard/LAAS.md:119-122`).
The rejected record and the corrected record both stay in the chain.

## 6. Worked example

**Action.** A contracts agent is asked to execute amendment 3 to a master services agreement
before the renewal term expires. The counterparty returned the execution version with two
changes: a fee change at cl. 11.3 and a change at cl. 14.2 that removes the liability cap
from the indemnity.

### 6.1 Non-conforming record

> The system reviewed the renewal and the contract was signed. The changes are standard
> terms and the fee increase is minor. Counsel reviewed it. Clause 14.2 was adjusted subject
> to the usual limits, so liability is limited as before. This is not binding until
> countersigned, and it can be unwound if there's an issue. Notice will be sent promptly.

Eleven defects, and each maps to a rule:

| Text | Rule broken |
|------|-------------|
| "The system reviewed" | `STE-C-01`, `STE-LEGAL-01` — unattributed actor |
| "the contract was signed" | `STE-LEGAL-01`, `STE-LEGAL-04` — passive, no signatory, wrong document state |
| "standard terms" | Forbidden — asserts a clause needs no review |
| "minor" | Core §3.2 — self-assessed consequence |
| "Counsel reviewed it" | Forbidden — unattributed and unscoped review claim; also `STE-C-06`, no antecedent |
| "Clause 14.2 was adjusted" | `STE-LEGAL-03` — no instrument, no version; the cite does not resolve |
| "subject to the usual limits" | Forbidden — hides whether this is a condition precedent or a carve-out |
| "liability is limited as before" | `STE-LEGAL-08` — no cap amount, no currency code, no cap basis, and factually reversed |
| "not binding until countersigned" | Forbidden — a legal conclusion the agent did not observe |
| "it can be unwound" | `STE-LEGAL-12` — reversal needs counterparty consent; also `STE-C-06` |
| "promptly" | Forbidden, `STE-LEGAL-05` — a deadline with no time |

The eighth one is the dangerous one.
`cl. 14.2` removed the cap. The record says liability is limited as before. A human approver
reading this record approves an uncapped indemnity believing the cap survived, and the
approval at CT4 is exactly the control `LAAS-OBL-HUM-001` requires.

### 6.2 Conforming record

> Illustrative values. The sample size, escape count, bound, and evidence IDs in this example are not measured data.

```text
DEFINED TERMS
Group is defined at MSA-2024-0417 cl. 1.1 (definition of Group).

ACTION
agent.contractbot.v2 executed 1 document in matter MAT-2026-0441.
The document state is execution version.
The instrument is MSA-2024-0417 cl. 11.3, executed 2024-04-17.
The clauses changed are 11.3 and 14.2.
The selection rule is amendment 3 to MSA-2024-0417 only.
The parties are Northvale Systems Ltd and Orsted Marine Services AS.
The signatory is J. Ramanathan, Director of Commercial.
The authority basis is board resolution BR-2025-11 cl. 4(b).

EFFECT SURFACE
Reversibility is irreversible. The amendment binds both parties on execution, and reversal
requires an executed further amendment that Orsted Marine Services AS has not agreed to.
Scope is org. The effect reaches Northvale Systems Ltd, Orsted Marine Services AS, and every
entity inside the definition of Group at MSA-2024-0417 cl. 1.1.
Consequence is high. The liability position is uncapped for the indemnity at cl. 14.2.
The prior liability position was capped at GBP 1,500,000.00, equal to 12 months of fees.
The privilege status of every document this action touches is not privileged.

RATIONALE AND RESIDUAL RISK
agent.contractbot.v2 executed the amendment because the renewal term at MSA-2024-0417
cl. 3.2 expires on 2026-08-31 and the counterparty returned the execution version unchanged.
The authority for the change is board resolution BR-2025-11 cl. 4(b).
The governing law is the law of England and Wales. The forum is the courts of England and
Wales, MSA-2024-0417 cl. 22.1.
The notice under cl. 18.1 must reach Orsted Marine Services AS by
2026-08-14T23:59:00+01:00, 10 business days from the execution date.
The exact-verified claim class is the location of each change in MSA-2024-0417. The gate
verifier for it is VRF-CLAUSE-DIFF.
The open-world claim class is the effect of each changed clause on the liability position.
The backtest observed 0 escapes in 300 samples on the CT4 held-out adversarial clause set,
measured on 2026-06-19.
The residual error bound is 0.008938, the one-sided 0.95 upper bound by the Wilson method.
The tolerance for CT4 is 0 from conformance/laas/data.json.
The backtest verdict is indeterminate. The evidence is ev_backtest_86bcfce27a3cf97f.
The rollback plan is: the legal operations team prepares a further amendment that restores
cl. 14.2. The team requests execution by Orsted Marine Services AS. The team records the
outcome against MAT-2026-0441. The named actor is the legal operations team. The time bound
is 10 business days.
Reversal depends on counterparty consent and is not guaranteed.

VERIFIER FINDING
VRF-CLAUSE-DIFF is a deterministic verifier.
The independence basis is different kind of checker.
VRF-CLAUSE-DIFF checked that the execution version differs from MSA-2024-0417 only at
cl. 11.3 and cl. 14.2, and that no Defined Term in cl. 1.1 changed.
VRF-CLAUSE-DIFF did not check the liability position.
The verdict is pass.
The evidence is ev_clause_diff_0441.
```

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42`, the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `irreversible` ranks 4, `org` ranks 3, and `high`
ranks 4. The maximum is 4.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-CLAUSE-DIFF` runs before execution, not after. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic text diff is a different *kind* of checker (`standard/LAAS.md:87`), so no error-correlation measurement is needed. |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented coverage of the clause-change claim class, a negative-test suite of known cap-removal and indemnity-widening edits it must catch, and a change-controlled version in the trace (`standard/LAAS.md:95-96`). |
| `LAAS-OBL-RES-001` | `VRF-CLAUSE-DIFF` passed, so the gate treats the action as Bucket A and does not require a numeric `residual_error_bound` (`conformance/laas/laas.rego:244-247`, `:256-261`). That `pass` does not cover the open-world claim class. The CT4 tolerance is `0` (`data.json:15`), no finite backtest demonstrates it, and the backtest verdict is `indeterminate` (`docs/laas/backtest.md:116`). The human approver is the control for the open-world claim class. |
| `LAAS-OBL-HUM-001` | A human approver approves before execution, and `escalation_approved` is `true`. |
| `LAAS-OBL-INP-001` | The returned redline is untrusted input from the counterparty, so the floor at `untrusted_input_min_ct` (`data.json:18`) applies before the tier is taken. |
| `LAAS-OBL-AGG-001` | The windowed aggregate is checked. Amendment 3 follows amendments 1 and 2 to the same master services agreement, and the aggregate re-tiers the sequence (`standard/LAAS.md:59-60`). |

**Language conformance: `LC-3`** — tool-checked, plus review of the free-text fields by the
human approver.

The rewrite changes no obligation and no threshold.
It changes what the CT4 human approver is approving.
In §6.1 they approve an amendment they believe leaves the liability cap in place.
In §6.2 they approve an amendment that states, in one sentence, that the indemnity at
cl. 14.2 is now uncapped, and states what the cap was before.
That is the same control doing its job instead of appearing to.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

Adams, Kenneth A.
*A Manual of Style for Contract Drafting.*
5th ed. Chicago: American Bar Association, 2023.

Garner, Bryan A.
*Garner's Dictionary of Legal Usage.*
3rd ed. New York: Oxford University Press, 2011.

International Organization for Standardization.
*ISO 4217:2015, Codes for the representation of currencies.*
Geneva: ISO, 2015.

International Organization for Standardization.
*ISO 8601-1:2019, Date and time — Representations for information interchange — Part 1:
Basic rules.*
Geneva: ISO, 2019.

Tiersma, Peter M.
*Legal Language.*
Chicago: University of Chicago Press, 1999.
