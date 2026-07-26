# LAAS Controlled-Language Profile — Real Estate

**Designation:** LAAS-STE-RE-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/real-estate.json`](glossary/real-estate.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not legal advice and states no legal obligation. Fair-housing,
> licensing, and contract law vary by jurisdiction. The occupant-description rule in
> §2 is a writing discipline, not a compliance opinion, and it does not replace review
> by qualified counsel.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

Real estate has two failure modes that a controlled language addresses directly, and they
are unusual because in this domain **the text is the action**.

In banking an agent moves money and then writes a record about it. In real estate an agent
writes a listing, a notice, or an offer, and the writing *is* the thing with legal effect.
A published listing is an advertisement. A served notice starts a statutory clock. A
delivered signature forms a contract. There is no gap between the prose and the consequence
in which a reviewer can catch a wording problem.

**The first failure mode is deadline arithmetic.**
Real-estate contracts run on contingency deadlines counted in days, and the word *days* is
not one word. Calendar days and business days differ, jurisdictions differ on whether the
count starts on the day of acceptance or the day after, and *acceptance* itself means the
moment a signed offer is **delivered**, not the moment it is signed. An agent that writes
"inspection contingency expires in 10 days" has written four different deadlines depending
on the reader. Missing a contingency deadline forfeits earnest money and extinguishes the
right to terminate. The loss is total, immediate, and caused entirely by an ambiguous
sentence.

**The second failure mode is who the text describes.**
Fair-housing law does not turn on an agent's intent. It turns on whether an advertisement
or a communication indicates a preference based on a protected characteristic. An LLM
writing listing copy produces exactly the phrasing that creates this exposure, because the
phrasing is idiomatic, warm, and everywhere in its training data. "Perfect for a young
family." "Safe, quiet neighbourhood." "Walking distance to shops." Each reads as praise for
the property and each describes a person.

This gives the profile its central rule, and it is a genuine controlled-language rule rather
than a compliance checklist:

> **Describe the property. Never describe the occupant.**

A sentence that says what the building is can be verified against the building. A sentence
that says who would like the building cannot be verified at all, and it is the class of
sentence that carries the exposure. The rule is checkable by a party that knows nothing
about fair-housing law, which is what makes it useful to an independent verifier under
`LAAS-OBL-IND-001`.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Record a deed or a lien release with the county recorder | `irreversible` — a public record | `public` | `high` | CT4 |
| Publish or syndicate a listing | `irreversible` — copied by portals within minutes | `public` | `material` | CT4 |
| Execute or countersign a purchase agreement | `irreversible` — the contract is formed | `multi` | `high` | CT4 |
| Waive a contingency | `irreversible` — the right is extinguished | `multi` | `high` | CT4 |
| Disburse earnest money from an escrow account | `irreversible` | `multi` | `high` | CT4 |
| Deny a tenant application | `hard` — the applicant has been told | `single` | `high` | CT4 |
| Serve a notice of eviction, termination, or rent increase | `irreversible` — the statutory clock has started | `single` | `high` | CT4 |
| Set or change a rent amount across a portfolio | `reversible`, but charged rent is not | `org` | `material` | CT4 |
| Extend a contingency deadline by written amendment | `hard` | `multi` | `material` | CT3 |
| Withhold or return a security deposit | `hard` | `single` | `material` | CT3 |
| Change a listing status or a list price | `hard` — the price history is public | `public` | `low` to `material` | CT3 |
| Order an appraisal or an inspection | `reversible` | `single` | `low` | CT2 |
| Read a property record | `reversible` — read only | `single` | `none` | CT0 |

Three observations.

**Recording is the hardest stop in the domain.**
A recorded instrument enters a public chain of title. Correcting it requires recording a
further instrument, which does not remove the first. This is the real-estate equivalent of
settlement finality, and it deserves the same treatment the banking profile gives to
`reverse`.

**Publication is faster than review.**
A listing syndicates to portals within minutes and is scraped, cached, and screenshotted.
Withdrawing the listing changes what the listing service serves. It does not retrieve the
copy. The SEO profile makes the same point about published pages; here the published text
is also an advertisement with a regulator.

**Tenant screening is `single` scope and still CT4.**
One applicant is one person, the smallest value on the scope axis. The `consequence` axis
carries it alone, exactly as in the healthcare profile. A portfolio-wide screening rule
applied by an agent is worse: it is a `multi` or `org` scope repetition of the same decision,
and `LAAS-OBL-AGG-001` re-tiers the sequence.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
The rules below are additional and specific to this domain.

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-RE-01` | **Describe the property. Never describe the occupant.** Write what the property is, has, or measures. Never write who would want it, who lives nearby, or who it suits. | This is the profile's most important rule. See §1.1. A property claim is verifiable; an occupant claim is not, and it is the class of sentence that carries fair-housing exposure. |
| `STE-RE-02` | State every period as a number, the word `calendar days` or `business days`, and the named event the count starts from. Never write the bare word *days*. | A contingency deadline written as "10 days" has at least four readings. The loss from picking the wrong one is total. |
| `STE-RE-03` | Write `acceptance` only for the delivery of a signed offer to the offering party. State the delivery method and the timestamp. Do not use it for signature alone. | Contract formation turns on delivery, not on ink. Every deadline in the contract counts from this moment. |
| `STE-RE-04` | Never write the bare word *closing*. Write `closing date`, `closing costs`, or `settlement statement`. | Three unrelated meanings, all present in the same email thread. |
| `STE-RE-05` | Never write the bare word *escrow*. Write `escrow account`, `escrow holder`, or `escrow period`. | In some jurisdictions *escrow* names the whole transaction; in others it names only the account. |
| `STE-RE-06` | Never write the bare word *deposit*. Write `earnest money`, `security deposit`, or `down payment`. | Three different sums with three different owners and three different release conditions. |
| `STE-RE-07` | Never write the bare word *value* or the bare word *price*. Write `list price`, `offer price`, `appraised value`, or `assessed value`, each with its source and date. | These four numbers routinely differ by double-digit percentages for the same property on the same day. |
| `STE-RE-08` | State area as a number, the unit, and the named measurement standard. Never write a bare square-footage figure. | Gross area, finished area, and gross living area measure different things. A listing figure without its standard is not comparable to any other figure. |
| `STE-RE-09` | Write `serve` only for delivery by a legally prescribed method. State the method, the recipient, and the timestamp. Do not write *sent* or *notified* for a notice. | A notice that was emailed is not a notice that was served, and only one of the two starts the clock. |
| `STE-RE-10` | State a tenant-screening decision against the written criteria published before the application was received. Cite the criterion by identifier. Never state a conclusion about the applicant. | An adverse decision must rest on a criterion that existed beforehand. "Not a good fit" is both unverifiable and the exact phrasing a regulator reads as pretext. |
| `STE-RE-11` | Never write the bare word *contract* or *approved*. Write `executed contract`, or name what was approved and by whom. | *Approved* covers offer acceptance, loan approval, association approval, and inspection approval. They fail independently. |
| `STE-RE-12` | Name the property by `property identifier` and the listing by its listing number. Do not identify a property by street address alone in a decision record. | Addresses are ambiguous across units, and unit numbers are the field most often dropped. |

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/real-estate.json`](glossary/real-estate.json) is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`accept` is the verb; `acceptance` is the noun. `disclose` is the verb; `disclosure
statement` is the noun.

### 3.1 Approved technical nouns

| Noun | Approved meaning |
|------|------------------|
| `acceptance` | The delivery of a signed offer to the offering party. The moment a contract is formed. |
| `appraised value` | An opinion of value stated by a licensed appraiser, with a report date. |
| `assessed value` | The value assigned to a property by a taxing authority for one tax year. |
| `broker` | The licensed party responsible for a transaction under a named licence. |
| `closing costs` | The fees and charges payable by a party at settlement, itemised on the settlement statement. |
| `closing date` | The date on which the transaction settles and the deed is delivered. |
| `commission` | The fee payable to a broker, stated as an amount or a rate and a payer. |
| `comparative market analysis` | A broker's estimate of value from comparable sales. It is not an appraisal. |
| `contingency` | A stated condition that must be satisfied or waived before a party is bound to proceed. |
| `contingency deadline` | The date and time at which a contingency expires, counted from a named event. |
| `counteroffer` | An offer made in response to an offer, which terminates the prior offer. |
| `deed` | The instrument that transfers title, effective on delivery and recording. |
| `disclosure statement` | The document in which a seller states known conditions of the property. |
| `down payment` | The buyer's own funds applied to the purchase price at settlement. |
| `earnest money` | Funds deposited by a buyer to an escrow account to evidence commitment to a contract. |
| `easement` | A recorded right of a named party to use part of the property for a stated purpose. |
| `encumbrance` | A recorded claim against a property that limits its transfer or use. |
| `escrow account` | The account held by an escrow holder into which transaction funds are deposited. |
| `escrow holder` | The neutral party that holds funds and documents under the escrow instructions. |
| `escrow period` | The interval between acceptance and the closing date. |
| `executed contract` | An agreement signed by all parties and delivered, and therefore binding. |
| `gross living area` | Finished, above-grade living area measured to a named standard. |
| `inspection report` | The written findings of an inspection, with an inspector identifier and a date. |
| `lease agreement` | The executed contract that grants possession for a stated term at a stated rent amount. |
| `lien` | A recorded claim securing a debt against the property. |
| `list price` | The price at which a property is publicly offered on a named listing service. |
| `listing number` | The unique identifier of a listing on a named listing service. |
| `listing status` | The published state of a listing on a named listing service. |
| `notice period` | The number of days between service of a notice and the date it takes effect. |
| `offer price` | The price stated in an offer by a named party on a stated date. |
| `property identifier` | The parcel or assessor identifier that uniquely names the property. |
| `purchase agreement` | The contract that states the terms of sale between a named buyer and a named seller. |
| `rent amount` | The periodic sum payable under a lease agreement, with a currency code and a period. |
| `screening criteria` | The written standards, published before an application is received, against which a tenant application is evaluated. |
| `security deposit` | Funds held against a tenant's obligations under a lease agreement, refundable on stated conditions. |
| `seller concession` | An amount the seller agrees to credit the buyer at settlement. |
| `settlement statement` | The itemised statement of all funds paid and received at closing. |
| `tenant application` | A prospective tenant's submitted request to lease, evaluated against screening criteria. |
| `title commitment` | The title insurer's statement of the conditions on which it will insure title. |
| `title defect` | A recorded matter that prevents title from being conveyed as agreed. |

### 3.2 Approved technical verbs

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `accept` | Deliver a signed offer to the offering party, forming a contract. | `accept` |
| `amend` | Change an executed contract by a written instrument signed by all parties. | `amend` |
| `cancel` | End a contract under a right stated in that contract. | `cancel` |
| `countersign` | Sign a document already signed by another party. | `countersign` |
| `deliver` | Transmit a document to a party by a method the contract states. | `deliver` |
| `disburse` | Pay funds out of an escrow account to a named party. | `disburse` |
| `disclose` | State a known condition of the property in a disclosure statement. | `disclose` |
| `execute` | Sign and deliver a document so that it becomes binding. | `execute` |
| `extend` | Move a stated deadline to a later date by written amendment. | `extend` |
| `list` | Publish a property to a named listing service at a stated list price. | `list` |
| `record` | File an instrument with the county recorder. This enters the public record and cannot be removed. | `record` |
| `release` | Pay or return funds held in an escrow account under the escrow instructions. | `release` |
| `rescind` | Undo a contract from its beginning under a stated statutory or contractual right. | `rescind` |
| `screen` | Evaluate a tenant application against published screening criteria and record the result. | `screen` |
| `serve` | Deliver a notice by a legally prescribed method, starting the notice period. | `serve` |
| `syndicate` | Distribute a listing from a listing service to named portals. | `syndicate` |
| `terminate` | End a lease agreement or a contract prospectively under a stated right. | `terminate` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `waive` | Give up a stated right by a written instrument. The right does not return. | `waive` |
| `withdraw` | Remove a listing from a named listing service. | `withdraw` |
| `withhold` | Retain part of a security deposit against a stated, itemised obligation. | `withhold` |

### 3.3 Forbidden terms

The first block is occupant description.
Every entry describes a person rather than the property, which is the failure `STE-RE-01`
exists to prevent.
These are forbidden in any published or party-facing text at **every** tier, including CT0,
because publication is not tiered by the agent and the exposure does not scale with the
Consequence Tier.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *perfect for families*, *family-friendly*, *ideal for couples* | States a preferred household composition. | The bedroom count, the room dimensions, and the floor plan |
| *safe neighbourhood*, *good area*, *nice part of town* | Unverifiable, and read as a proxy for the people who live there. | Nothing. State property facts only. |
| *walking distance*, *walkable* | Assumes an ability. | The measured distance and the named destination |
| *young professionals*, *empty nesters*, *mature residents* | States a preferred age group. | The property features that prompted the phrase |
| *near churches*, *close to the synagogue*, *Christian community* | States a religious preference. | The named amenity, if a party asked for it, without a category |
| *English speaking*, *must speak English* | States a national-origin preference. | The written screening criteria, applied to every applicant |
| *no children*, *adults only*, *quiet building, no kids* | States a familial-status preference. | The lease terms that apply to every occupant |
| *handicapped*, *not suitable for disabled* | States a disability judgement about the occupant. | The measured accessibility features the property has |
| *exclusive*, *private community*, *restricted* | Historic exclusionary vocabulary. | The named amenity or the named association |
| *diverse*, *integrated*, *changing neighbourhood* | Describes the residents. Steering, whether the intent is favourable or not. | Nothing. State property facts only. |
| *good fit*, *not a good fit*, *ideal tenant* | An unverifiable conclusion about a person, and the phrasing read as pretext. | The screening criterion identifier and the applicant's value against it |

The second block is ambiguity.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *days* (bare) | Calendar or business, counted from the signature or from delivery (`STE-RE-02`). | The number, `calendar days` or `business days`, and the starting event |
| *closing* (bare) | The date, the costs, or the process. | `closing date`, `closing costs`, or `settlement statement` |
| *escrow* (bare) | The account, the holder, or the period. | `escrow account`, `escrow holder`, or `escrow period` |
| *deposit* (bare) | Earnest money, security deposit, or down payment. | The named sum |
| *value*, *price* (bare) | List, offer, appraised, or assessed. Four different numbers. | The named figure, with its source and date |
| *approved* (bare) | Offer, loan, association, or inspection approval. They fail independently. | What was approved, by whom, and on what date |
| *contract* (bare) | Sent, signed, delivered, or binding. | `executed contract`, or the stage by name |
| *clear title* | A conclusion, not a finding. | The title commitment identifier and each listed exception |
| *as-is* | Does not remove a disclosure duty, though it reads as though it does. | The named contract clause and the disclosure statement |
| *sent*, *notified* (for a notice) | A sent notice is not a served notice, and only one starts the clock. | `serve`, with the method, the recipient, and the timestamp |
| *square feet* (bare) | Gross, finished, or gross living area. | The number, the unit, and the named measurement standard |
| *motivated seller*, *must sell* | Discloses a party's position and is unverifiable. | The list price and the days on market |
| *the property* (unidentified) | Ambiguous across units (`STE-RE-12`). | The `property identifier` and the `listing number` |

## 4. Decision-trace field templates

The templates use only approved terms.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <object> for property identifier <id> on <listing service or platform>.
The listing number is <number>.
The old value is <value>. The new value is <value>.
The counterparties are <named parties>.
```

Filled:

```text
agent.listbot.v3 listed 1 property for property identifier APN-047-221-018 on the Cascade
Regional listing service.
The listing number is CR-2026-114872.
The old value is no active listing. The new value is an active listing at list price
USD 615,000.
The counterparties are Ellery Voss, seller, and Northgate Realty, listing broker.
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
<One sentence that states what a withdrawal or a correction does not recover.>
Scope is <single|multi|org|public>. The effect reaches <named surfaces, parties, or counts>.
Consequence is <none|low|material|high>. <One sentence that states the stated exposure.>
```

Filled:

```text
Reversibility is irreversible. The listing syndicates to 14 named portals within 15 minutes
of publication.
A withdrawal removes the listing from the listing service. It does not retrieve the
syndicated copies, the cached copies, or the published price history.
Scope is public. The effect reaches any requester of the 14 syndication portals.
Consequence is material. The published text is an advertisement subject to fair-housing
advertising rules in this jurisdiction.
```

The second sentence is mandatory in this profile whenever the action publishes or records.
It is the sentence a non-conforming record always omits.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The written criteria that apply are <criteria identifier>, published <date>.
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The rollback plan is: <step 1>. <step 2>. The named actor is <party>.
Recovery depends on <named third party>. Recovery is not guaranteed.
```

Filled:

```text
agent.listbot.v3 listed the property because Ellery Voss executed a listing agreement with
Northgate Realty on 2026-07-24.
The written criteria that apply are the Northgate advertising standard ADV-STD-2026-01,
published 2026-01-15.
The measured residual error bound is 0.0 on the CT4 held-out adversarial listing-copy set,
measured on 2026-07-09.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the listing broker withdraws the listing from the Cascade Regional
listing service. The broker submits a removal request to each of the 14 syndication portals.
The named actor is the listing broker.
Recovery depends on the removal schedule of each syndication portal. Recovery is not
guaranteed.
```

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
VRF-OCCUPANT-DESC is a deterministic verifier.
The independence basis is different kind of checker.
VRF-OCCUPANT-DESC checked the listing text against the forbidden occupant-description list
in LAAS-STE-RE-DRAFT-1.0 section 3.3 and reported each match with its offset.
The verdict is fail.
The evidence is ev_listing_copy_114872.
```

A deterministic term matcher is the correct verifier class for the occupant-description
block, and it is available at any tier because it is a different *kind* of checker
(`standard/LAAS.md:87`).
Asking a second language model whether listing copy "sounds discriminatory" is not
independence: a model of the same lineage produces and forgives the same idiom, and
`standard/LAAS.md:91` presumes it non-independent.

## 5. Mapping to LAAS obligations and tiers

### 5.1 Zero-Trust

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.

This domain's version is subtle, because the agent is not summarising an action taken
elsewhere — the text *is* the action. An agent that drafts listing copy and also drafts the
effect-surface description of that copy is grading its own output twice in the same record.

`STE-RE-01` breaks that loop by changing what kind of claim the record contains.
"The listing copy is appropriate" is a self-assessment. "The listing copy contains no term
from the occupant-description list" is a fact about a string, checkable by a party that has
never seen the property and knows nothing about the market.
The rule converts a judgement only the agent can make into a check anyone can run, which is
what makes independent verification available at all.

`STE-RE-02` closes the second channel. A deadline written as "10 days" lets the agent
resolve the ambiguity later, in whichever direction suits the outcome. Writing
`10 calendar days from acceptance on 2026-07-24T16:12:00Z` fixes it in the trace, before
the outcome is known.

### 5.2 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5, with one stated
deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1`, and the §3.3 occupant-description block at every tier | Advisory, except occupant description |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

**Deviation — occupant description is blocking at every tier.**
The §3.3 first block is not a style preference. Its exposure does not scale with the
Consequence Tier, because the harm is caused by the published sentence itself and the
publication is not tiered by the agent.
This mirrors the healthcare profile's treatment of dose notation
([`healthcare.md`](healthcare.md) §5.2), and for the same structural reason: some defects are
caused by the notation rather than by the size of the action.

The deviation is more restrictive than the core profile. It changes no LAAS obligation, no
tier, and no threshold.

### 5.3 How language non-conformance should be treated

A language finding is a finding about the record, not about the action, and it enters the
same structure the policy already uses to separate `error_violations`
(`conformance/laas/laas.rego:199`) from `warning_violations`
(`conformance/laas/laas.rego:204`).

The checker must not rewrite the record (see [`ste-core.md`](ste-core.md) §5).
This constraint carries extra weight here.
A checker that silently rewrites "perfect for families" to "three bedrooms" has produced
compliant copy and destroyed the evidence that the agent generated non-compliant copy.
The pattern is the finding. An operator needs to know that this actor produces
occupant-description language, because that is a fact about the actor and about every listing
it has drafted, not about this one listing.

A rewrite is an append, not an edit (`LAAS-OBL-TRC-001`, `standard/LAAS.md:108-111`).
Both records stay in the chain.

## 6. Worked example

**Action.** A listing agent is asked to publish a new residential listing to the regional
listing service, which syndicates to 14 portals. The agent drafts the public remarks.

### 6.1 Non-conforming record

> Listed the property at 118 Marlowe St. Great starter home, perfect for a young family —
> safe quiet neighbourhood, walking distance to the elementary school and two churches.
> About 1,850 sq ft. Priced at market value. Seller is motivated so we should get an offer
> approved fast. Inspection contingency is 10 days. This is easily reverted if we need to
> change anything.

The defects, and the rule each breaks:

| Text | Rule broken |
|------|-------------|
| "Listed" with no actor | `STE-C-01` — unattributed actor |
| "118 Marlowe St" alone | `STE-RE-12` — no property identifier, no listing number, no unit |
| "perfect for a young family" | `STE-RE-01` — familial status and age. Occupant description |
| "safe quiet neighbourhood" | `STE-RE-01` — unverifiable, read as a proxy for residents |
| "walking distance" | `STE-RE-01` — assumes an ability |
| "two churches" | `STE-RE-01` — religious preference |
| "About 1,850 sq ft" | `STE-RE-08` — no measurement standard, and "about" is a hedge |
| "market value" | `STE-RE-07` — list, offer, appraised, or assessed? |
| "Seller is motivated" | Forbidden — discloses the seller's position |
| "an offer approved" | `STE-RE-11` — accepted, or loan-approved? |
| "10 days" | `STE-RE-02` — calendar or business, counted from what? |
| "easily reverted" | `STE-C-08`, §4.2 — false. Syndicated copy is not retrievable |

Four of these are the same defect.
"Perfect for a young family", "safe quiet neighbourhood", "walking distance", and "two
churches" all describe who should live there rather than what the property is. Each names or
proxies a protected characteristic, and the text is an advertisement the moment it publishes.

"10 days" is the second live defect. Counted as business days from delivery of acceptance,
the deadline is roughly four days later than counted as calendar days from signature. The
record does not say which, so the agent can decide afterwards — which is the self-grading
the profile exists to prevent.

### 6.2 Conforming record

```text
ACTION
agent.listbot.v3 listed 1 property for property identifier APN-047-221-018 on the Cascade
Regional listing service.
The listing number is CR-2026-114872.
The old value is no active listing. The new value is an active listing at list price
USD 615,000.
The counterparties are Ellery Voss, seller, and Northgate Realty, listing broker.

PUBLIC REMARKS AS SUBMITTED
The property is a detached single-family residence built in 1974.
The gross living area is 1,847 square feet, measured to the ANSI Z765 standard on
2026-07-22.
The property has 3 bedrooms and 2 full bathrooms on one storey.
The lot area is 6,098 square feet per the assessor record.
The property has a detached two-car garage, a gas forced-air furnace installed in 2019, and
a composition-shingle roof installed in 2016.
Ashford Elementary School is 0.4 miles from the property by public road.

EFFECT SURFACE
Reversibility is irreversible. The listing syndicates to 14 named portals within 15 minutes
of publication.
A withdrawal removes the listing from the listing service. It does not retrieve the
syndicated copies, the cached copies, or the published price history.
Scope is public. The effect reaches any requester of the 14 syndication portals.
Consequence is material. The published text is an advertisement subject to fair-housing
advertising rules in this jurisdiction.

RATIONALE AND RESIDUAL RISK
agent.listbot.v3 listed the property because Ellery Voss executed a listing agreement with
Northgate Realty on 2026-07-24.
The list price of USD 615,000 is the price stated in that listing agreement. The comparative
market analysis dated 2026-07-20 states a range of USD 598,000 to USD 627,000.
The written criteria that apply are the Northgate advertising standard ADV-STD-2026-01,
published 2026-01-15.
The inspection contingency deadline is 10 business days from acceptance. Acceptance has not
occurred. The deadline is undetermined until acceptance is delivered.
The measured residual error bound is 0.0 on the CT4 held-out adversarial listing-copy set,
measured on 2026-07-09.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the listing broker withdraws the listing from the Cascade Regional
listing service. The broker submits a removal request to each of the 14 syndication portals.
The named actor is the listing broker.
Recovery depends on the removal schedule of each syndication portal. Recovery is not
guaranteed.

VERIFIER FINDING
VRF-OCCUPANT-DESC is a deterministic verifier.
The independence basis is different kind of checker.
VRF-OCCUPANT-DESC checked the public remarks against the forbidden occupant-description list
in LAAS-STE-RE-DRAFT-1.0 section 3.3 and reported each match with its offset.
The verdict is pass. The matcher reported 0 matches in 1,043 characters.
The evidence is ev_listing_copy_114872.
```

Every sentence in the public remarks states a property fact with a source. The school
appears as a measured distance to a named school rather than as "walking distance", which
keeps the information a buyer wanted and removes the ability claim. Nothing describes a
person.

Note the use of `undetermined` for the contingency deadline.
Acceptance has not happened, so the deadline genuinely cannot be computed. Writing
`undetermined` is the conforming statement ([`ste-core.md`](ste-core.md) §3.1); writing
"about two weeks" would be a hedge that routes around the default-to-highest rule at
`standard/LAAS.md:44`.

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42` the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `irreversible` ranks 4, `public` ranks 4, and
`material` ranks 3. The maximum is 4.

This example has **two** axes at 4 independently.
That differs from the other profiles, where one axis carries the tier: reversibility in
[`banking.md`](banking.md), consequence in [`healthcare.md`](healthcare.md), scope in
[`seo-adsense.md`](seo-adsense.md).
The practical consequence is that an argument about any single axis cannot lower this
action's tier. An agent that persuaded a reviewer the listing is withdrawable would still be
at CT4 on scope alone.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-OCCUPANT-DESC` runs before publication, not after. Running it after is worthless: the copy has syndicated. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic term matcher is a different *kind* of checker (`standard/LAAS.md:87`). A second language model reviewing the copy would be presumed non-independent (`standard/LAAS.md:91`). |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented claim-class coverage for the occupant-description list, a negative-test suite of known non-compliant listing phrases it must catch, and a change-controlled version in the trace. |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0.0` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | The listing broker approves before publication, and `escalation_approved` is `true`. The licensed broker, not the agent, carries the advertising responsibility. |
| `LAAS-OBL-VEN-001` | Syndication is third-party distribution. The record names the 14 portals and states the scope limit, rather than writing "and partner sites". |

**Language conformance: `LC-3`**, with the §3.3 occupant-description block applying
unconditionally.

The rewrite changes no obligation and no threshold.
It changes whether the CT4 human approver is looking at an advertisement or at a description.
In §6.1 the broker approves copy that names a family type, an age group, an ability, and a
religion, and the record tells them it is "easily reverted".
In §6.2 the broker approves eight verifiable property facts and a sentence stating that
syndicated copies cannot be retrieved.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

American National Standards Institute and American Measurement Standard.
*ANSI Z765-2021: Square Footage — Method for Calculating.*
Washington, DC: ANSI, 2021.

United States Congress.
*Fair Housing Act, Title VIII of the Civil Rights Act of 1968, as amended.*
42 U.S.C. §§ 3601–3619.

United States Department of Housing and Urban Development.
*Advertising and Marketing.*
24 C.F.R. Part 100, Subpart D. Washington, DC: HUD.

Appraisal Foundation.
*Uniform Standards of Professional Appraisal Practice (USPAP), 2024–2025 Edition.*
Washington, DC: The Appraisal Foundation, 2024.
