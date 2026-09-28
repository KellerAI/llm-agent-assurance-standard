# LAAS Controlled-Language Profile — Healthcare, Clinical and Patient-Related Systems

**Designation:** LAAS-STE-HLTH-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/healthcare.json`](glossary/healthcare.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not clinical guidance, is not regulatory guidance, and states no
> medical or legal obligation. Clinical practice is governed by the institution's own
> policies and by the responsible clinician.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

Medicine is the one field that has already run this experiment and published the results.

Handwriting, abbreviation, and ambiguous dose notation caused enough deaths that the field
built formal do-not-use lists in response.
`U` for units was read as a zero, turning 4 units of insulin into 40.
A trailing zero on `1.0 mg` was read as `10 mg`.
A missing leading zero on `.5 mg` was read as `5 mg`.
None of these were reasoning failures. Every one was a notation failure, and each was fixed
by constraining notation rather than by asking people to be more careful.

That history is the argument for this profile, and it transfers directly.
An LLM agent writing a clinical record has exactly the failure mode the do-not-use lists
were built for: it produces fluent text whose ambiguity is invisible to the writer and
consequential to the reader.
It is worse in one respect. A clinician reading another clinician's ambiguous note usually
knows the writer and can ask. Nobody can ask the agent what it meant, and the agent will
answer a re-query from its own prose rather than from the fact.

The second reason is structural.
Healthcare is full of words that carry a technical meaning and an everyday meaning that
point in opposite directions.
A *negative* result is good news. A *positive* result is bad news.
A *significant* finding may be statistically significant and clinically irrelevant, or the
reverse.
*Stable* means "not changing", which is excellent in a recovering patient and terrible in a
deteriorating one.
An agent that uses these words in their everyday sense produces a record that reads
correctly and means the opposite of the fact.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Enter or transcribe a medication order | `hard` before administration, `irreversible` after | `single` | `high` | CT4 |
| Override a drug-interaction or allergy alert | `hard` | `single` | `high` | CT4 |
| Calculate or change a dose or a dose rate | `hard` before administration, `irreversible` after | `single` | `high` | CT4 |
| Merge two patient records | `hard` — an unmerge rarely restores the prior state | `multi` | `high` | CT4 |
| Release a laboratory result to a patient portal | `irreversible` — the patient has read it | `single` | `material` | CT4 |
| Export a cohort containing protected health information | `irreversible` — the data has left | `multi` to `public` | `high` | CT4 |
| Change a triage category | `reversible` | `single` | `high` | CT4 |
| Change a discharge disposition | `hard` | `single` | `material` | CT3 |
| Discontinue a medication order | `hard` | `single` | `material` | CT3 |
| Update a problem list or an allergy record | `reversible` | `single` | `material` | CT3 |
| Schedule an appointment | `reversible` | `single` | `low` | CT1 |
| Read a patient record | `reversible` — read only | `single` | `none` | CT0 |

Two observations.

**Scope is usually `single` and the tier is usually still CT4.**
`standard/LAAS.md:42` takes the maximum across the three axes, not the average.
One patient is enough. This is the clearest domain in which a small blast radius carries a
maximal consequence, and it is why a scope-first intuition is wrong here.

**A reversible action can still be CT4.**
Changing a triage category is fully reversible in the record.
The interval during which the wrong category was live is not reversible, because care was
allocated on it.
The lattice reads the `consequence` axis independently, and `high` ranks 4 on its own
(`conformance/laas/data.json:9`).

### 1.3 Protected health information

Any action that moves protected health information outside the treating context is
`irreversible` on the reversibility axis.
Data cannot be un-disclosed.
Deleting the copy at the destination does not restore the prior state, and the profile
forbids describing it as though it does.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
The rules below are additional and specific to this domain.

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-HLTH-01` | Write dose amounts in full. Write the numeral, the unit in full words or an approved unit symbol, the route, and the frequency. Never abbreviate a unit that has a do-not-use history. | This is the profile's most load-bearing rule. See §3.3. |
| `STE-HLTH-02` | Never write a trailing zero after a decimal point. Write `1 mg`, not `1.0 mg`. Always write a leading zero before a decimal point. Write `0.5 mg`, not `.5 mg`. | Both patterns have a documented tenfold-overdose history. Neither is a judgement call. |
| `STE-HLTH-03` | Write *negative* and *positive* only as laboratory result values. Never use either word to describe an outcome, a trend, or a judgement. | "The change had a positive effect" and "the culture was positive" mean opposite things about whether the patient is well. |
| `STE-HLTH-04` | Never write the bare word *significant*. Write `statistically significant` with the test and the p-value, or `clinically significant` with the threshold. | The two are independent. Collapsing them is how a null result becomes a treatment decision. |
| `STE-HLTH-05` | Never write the bare word *stable*. State the measured parameter, the value, the unit, and the observation interval. | *Stable* describes a rate of change, not a state. A patient can be stably deteriorating. |
| `STE-HLTH-06` | Write *administer* only for the physical act of giving a dose to a patient. An agent that enters an order has not administered anything. | Conflating the order with the act misstates reversibility, which sets the tier. |
| `STE-HLTH-07` | Never write the bare word *discharge*. Write `discharge disposition` for the destination, or `wound discharge` for the clinical sign. | Two unrelated meanings, one of which is a disposition decision and one of which is an observation. |
| `STE-HLTH-08` | Name the patient by `patient identifier`, never by name or by room. State the identifier system. | A room number identifies a bed, not a person. Beds change occupants. |
| `STE-HLTH-09` | State the source of every clinical value: the named system, the observation timestamp, and the reference range where one exists. | A value without a timestamp cannot be known to be current, and currency is the whole question in an acute setting. |
| `STE-HLTH-10` | When an alert is overridden, state the alert identifier, the alert text, the clinical reason, and the responsible clinician. Never write "override — clinically appropriate". | Alert-override text is the single most audited free-text field in clinical software, and the most degraded. |
| `STE-HLTH-11` | State an allergy as the substance, the reaction, and the severity. Never write "allergic to" without the reaction. | An intolerance and an anaphylaxis are both written as *allergy* and require opposite responses under time pressure. |
| `STE-HLTH-12` | For a data export, state the record count, the field list or the named minimum necessary data set, the destination, and the identifiability state. | `LAAS-OBL-VEN-001` requires scope limits. An export described as "some patient data" has no scope. |

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/healthcare.json`](glossary/healthcare.json) is derived from them.

### 3.1 Approved technical nouns

| Noun | Approved meaning |
|------|------------------|
| `active medication list` | The set of medication orders currently in effect for one patient. |
| `adverse drug event` | A recorded harm to a patient that followed the administration of a medication. |
| `allergy record` | A record of one substance, the reaction it caused in this patient, and the severity. |
| `care plan` | The documented set of planned interventions for one patient over a stated period. |
| `clinical decision support alert` | A system-generated warning presented to a clinician before an order is signed. |
| `cohort` | A set of patient records selected by a stated rule for analysis or export. |
| `consent record` | The record of a patient's documented permission for a stated use of their data or their care. |
| `contraindication` | A stated condition under which a medication or a procedure must not be used. |
| `controlled substance` | A medication subject to statutory prescribing and dispensing controls. |
| `de-identified data set` | A data set from which direct and indirect patient identifiers have been removed by a stated method. |
| `discharge disposition` | The destination and care setting to which a patient is released from an encounter. |
| `dose` | The amount of a medication given at one time, stated as a numeral and a unit. |
| `dose rate` | The amount of a medication given per unit of time, stated as a numeral, a unit, and a time unit. |
| `drug interaction` | A stated effect that occurs when two named medications are given together. |
| `duplicate record` | A patient record that a matching process asserts refers to the same person as another record. |
| `encounter` | One episode of care with a start time, an end time, and a care setting. |
| `formulary` | The list of medications approved for use at an institution. |
| `identity match score` | The numeric confidence that two patient records refer to the same person. |
| `indication` | The stated clinical reason for which a medication or a procedure is ordered. |
| `laboratory result` | A measured value from a specimen, with a unit, an observation timestamp, and a reference range. |
| `medication order` | An instruction to supply and give a named medication to one patient at a stated dose, route, and frequency. |
| `medication reconciliation` | The comparison of a patient's active medication list against an external medication list, with each difference explained. |
| `minimum necessary data set` | The smallest field set sufficient for a stated purpose. |
| `order set` | A predefined group of orders applied together for a stated clinical situation. |
| `patient identifier` | The unique identifier of one patient within a named identifier system. |
| `patient record` | The complete set of records held about one patient under one patient identifier. |
| `problem list` | The set of active diagnoses recorded for one patient. |
| `protected health information` | Patient data that identifies a person and relates to their health, care, or payment for care. |
| `record merge` | The operation that combines two patient records under one patient identifier. |
| `reference range` | The interval of values considered expected for a stated population and specimen type. |
| `route of administration` | The path by which a medication enters the body, stated by an approved route term. |
| `scheduled dose time` | The time at which a dose is planned to be given. |
| `severity` | The recorded seriousness of a reaction, stated by an approved severity term. |
| `specimen` | The biological sample from which a laboratory result is produced. |
| `treatment authorization` | A payer's recorded decision to cover a stated treatment. |
| `triage category` | The urgency classification assigned to a patient at presentation, from a named triage scale. |
| `vital sign` | A measured physiological parameter, with a value, a unit, and an observation timestamp. |

### 3.2 Approved technical verbs

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `administer` | Give a dose to a patient. This is a physical act performed by a person. | `administer` |
| `cancel` | Withdraw an order before it is acted on. | `cancel` |
| `discontinue` | Stop an active medication order. | `discontinue` |
| `dispense` | Supply a medication from a pharmacy against an order. | `dispense` |
| `document` | Record a clinical observation or a decision in the patient record. | `document` |
| `escalate` | Route a decision to a named clinician or a named queue. | `escalate` |
| `export` | Copy records to a destination outside the treating context. | `export` |
| `flag` | Attach a recorded marker to a record, an order, or a result. | `flag` |
| `merge` | Combine two patient records under one patient identifier. | `merge` |
| `order` | Create a medication order or a procedure order for one patient. | `order` |
| `override` | Proceed past a clinical decision support alert, with the reason and the responsible clinician recorded. | `override` |
| `prescribe` | Authorise a medication for a patient. This is an act by a licensed prescriber. | `prescribe` |
| `reconcile` | Compare two medication lists and explain each difference. | `reconcile` |
| `release` | Make a result visible to a patient or to a party outside the care team. | `release` |
| `review` | Read a record and record a documented conclusion about it. | `review` |
| `schedule` | Set a planned time for an appointment, a procedure, or a dose. | `schedule` |
| `suppress` | Stop an alert from being presented. This is distinct from `override`. | `suppress` |
| `transcribe` | Copy an order from one medium into the ordering system without changing it. | `transcribe` |
| `triage` | Assign a triage category from a named triage scale. | `triage` |
| `unmerge` | Separate two previously merged patient records. This does not restore the prior state. | `unmerge` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `withhold` | Omit a scheduled dose, with the reason recorded. | `withhold` |

### 3.3 Forbidden terms and notations

The first block is notation.
Every entry has a documented history of causing a tenfold or a wrong-drug error, and each is
on one or more institutional do-not-use lists.
These are forbidden without exception, at every tier, including CT0.

| Forbidden notation | Read as | Write instead |
|--------------------|---------|---------------|
| `U`, `u` | Zero or four — `4U` reads as `40` | `units` |
| `IU` | `IV` or `10` | `international units` |
| `QD`, `qd` | `QID` (four times daily) | `once daily` |
| `QOD`, `qod` | `QD` or `QID` | `every other day` |
| `MS`, `MSO4`, `MgSO4` | Morphine sulfate or magnesium sulfate — different drugs | The full drug name |
| Trailing zero (`1.0 mg`) | `10 mg` | `1 mg` |
| Naked decimal (`.5 mg`) | `5 mg` | `0.5 mg` |
| `cc` | `u` | `mL` |
| `µg`, `ug` | `mg` | `micrograms` |
| `@` | `2` | `at` |
| `SC`, `SQ` | `SL` (sublingual) | `subcutaneous` |
| `D/C` | `discharge` or `discontinue` — opposite actions | `discontinue` or `discharge disposition` |
| `HS` | `half strength` or `at bedtime` | `at bedtime` |
| `AU`, `AS`, `AD`, `OU`, `OS`, `OD` | Ear and eye abbreviations confused with each other | `both ears`, `left ear`, `right eye`, and so on, in full |

The second block is vocabulary.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *stable* | Describes a rate of change, not a state. A patient can be stably deteriorating. | The measured parameter, the value, the unit, and the interval |
| *negative*, *positive* (non-result) | The clinical sense is the opposite of the everyday sense. | Use only as a laboratory result value |
| *significant* (bare) | Statistical and clinical significance are independent. | `statistically significant` with the test, or `clinically significant` with the threshold |
| *acute* (as "severe") | Means "sudden onset". A chronic condition can be severe. | `sudden onset`, or the severity term |
| *discharge* (bare) | Disposition decision, or a clinical sign. | `discharge disposition` or `wound discharge` |
| *administer* (for ordering) | Confuses the order with the physical act, and so misstates reversibility. | `order`, `transcribe`, or `prescribe` |
| *hold* (a medication) | Means `withhold` one dose or `discontinue` the order. | `withhold` with the dose, or `discontinue` |
| *clear* (an alert) | Means `override`, `suppress`, or `resolve`. | `override` or `suppress` |
| *tolerated well* | An unmeasured global assessment. | The observed parameters and their values |
| *as needed* / *PRN* (bare) | No trigger condition and no maximum. | The trigger condition, the maximum dose, and the minimum interval |
| *routine* | Self-assessed consequence (core §3.2). | The `consequence` lattice value from `data.json:9` |
| *the patient in room N* | A room identifies a bed. | The `patient identifier` and its identifier system |
| *unremarkable* | States an absence without stating what was examined. | The examined items and the finding for each |
| *appears to be improving* | Impression, not observation (`STE-C-10`). | The parameter, the two values, and the interval |

## 4. Decision-trace field templates

The templates use only approved terms.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <object> for patient identifier <id> in <identifier system>.
The medication is <full drug name>. The dose is <numeral> <unit in full>.
The route of administration is <route>. The frequency is <frequency in full words>.
The indication is <indication>. The responsible clinician is <name and role>.
```

Filled:

```text
agent.orderbot.v2 transcribed 1 medication order for patient identifier MRN-4417902 in the
Meridian Health MRN system.
The medication is insulin glargine. The dose is 10 units.
The route of administration is subcutaneous. The frequency is once daily at bedtime.
The indication is type 2 diabetes mellitus. The responsible clinician is Dr A. Okonkwo,
attending endocrinologist.
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
Scope is <single|multi|org|public>. The effect reaches <named patients, records, or systems>.
Consequence is <none|low|material|high>. <One sentence that states the clinical consequence of
the error case.>
```

Filled:

```text
Reversibility is hard. The medication order can be discontinued before the first dose is
administered. After administration the dose cannot be withdrawn.
Scope is single. The effect reaches patient identifier MRN-4417902 only.
Consequence is high. A tenfold insulin dose error causes severe hypoglycaemia and can cause
death.
```

The two-sentence reversibility line is required whenever reversibility changes at a point in
time.
The record must state the point.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The source of the order is <named source, with timestamp>.
<If an alert was overridden:> Alert <alert id> stated: "<alert text>". The clinical reason is
<reason>. The responsible clinician is <name and role>.
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The rollback plan is: <step 1>. <step 2>. The named actor is <party>. The time bound is <duration>.
```

Filled:

```text
agent.orderbot.v2 transcribed the medication order because Dr A. Okonkwo entered a verbal
order at 2026-07-26T08:41:00Z during ward round.
The source of the order is verbal order record VO-2026-11884, recorded 2026-07-26T08:41:00Z.
Alert CDS-INSULIN-DOSE stated: "Insulin dose exceeds the starting-dose threshold for a
patient with no prior insulin order". The clinical reason is that the patient has a
documented prior insulin glargine order at 10 units from encounter ENC-2025-3391. The
responsible clinician is Dr A. Okonkwo, attending endocrinologist.
The measured residual error bound is 0.0 on the CT4 held-out adversarial dose-transcription
set, measured on 2026-07-11.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the ward pharmacist discontinues the medication order before the
scheduled dose time. The pharmacist documents the discontinuation against MRN-4417902. The
named actor is the ward pharmacist. The time bound is until the scheduled dose time of
2026-07-26T22:00:00Z.
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
VRF-DOSE-RANGE is a deterministic verifier.
The independence basis is different kind of checker.
VRF-DOSE-RANGE checked that 10 units of insulin glargine by the subcutaneous route once
daily is within the formulary dose range for an adult patient with a prior insulin order.
The verdict is pass.
The evidence is ev_dose_range_4417902_01.
```

At CT4 a deterministic verifier is not sufficient on its own.
`standard/LAAS.md:89` requires a human verifier *in addition* at CT4, and
`LAAS-OBL-HUM-001` requires the approval to be recorded.

## 5. Mapping to LAAS obligations and tiers

### 5.1 Zero-Trust

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.

In clinical software the human clinician is the last control, and at CT4 that is not a
metaphor: `LAAS-OBL-HUM-001` makes the clinician's approval a conformance requirement.
The clinician approves what the record says.
An agent that writes its own summary of its own order therefore controls the input to the
control that governs it — unless the language of that summary is fixed by a profile the
agent does not author.

Alert-override text is the concrete case.
`STE-HLTH-10` exists because "override — clinically appropriate" is a self-grading
statement in eight characters.
It asserts the conclusion the alert existed to test, and no verifier can contest it.
Requiring the alert identifier, the alert text, the clinical reason, and the responsible
clinician turns that assertion into four checkable facts.

### 5.2 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5, with one stated
deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1`, and the §3.3 notation block at every tier | Advisory, except notation |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-3` (deviation — the core profile requires `LC-2`) | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

**Deviation 1 — notation is blocking at every tier.**
The §3.3 notation block is not a style preference.
A `U` that reads as a zero is a tenfold dose error whether the record is CT0 or CT4.
A notation finding blocks at every tier, including CT0 and CT1.
This is the only place in any profile in this set where a language finding blocks below CT2,
and it is justified by the fact that the harm does not scale with the tier — it is caused by
the notation itself.

**Deviation 2 — `LC-3` at CT3, not `LC-2`.**
By §1.2 almost every patient-affecting action reaches CT3 or CT4, so a `LC-2` tier would
apply to almost nothing.
More importantly, at CT3 the clinician who reviews the record is doing the work
`LAAS-OBL-VQ-001` describes as claim-class coverage, and a tool check alone does not
establish that the *clinical* claim was reviewed.

Both deviations are more restrictive than the core profile.
Neither changes a LAAS obligation, a tier, or a threshold.

### 5.3 How language non-conformance should be treated

A language finding is a finding about the record, not about the action, and it enters the
same structure the policy already uses to separate `error_violations`
(`conformance/laas/laas.rego:199`) from `warning_violations`
(`conformance/laas/laas.rego:204`).

The checker must not rewrite the record (see [`ste-core.md`](ste-core.md) §5).
This constraint is stronger here than elsewhere.
A checker that "corrects" `10.0 units` to `10 units` has silently chosen one of the two
readings the notation rule exists to prevent, and it has chosen it without clinical
authority.
The correct behaviour is to reject the record and require the actor to restate the dose.

A rewrite is an append, not an edit (`LAAS-OBL-TRC-001`, `standard/LAAS.md:108-111`).
The rejected record stays in the chain.
In a clinical setting this is also a patient-safety record: a pattern of ambiguous dose
notation from one actor is a signal about that actor, and erasing the drafts erases the
signal.

## 6. Worked example

**Action.** A clinical agent transcribes a verbal insulin order taken during a ward round
into the electronic health record. A clinical decision support alert fires on the dose.

### 6.1 Non-conforming record

> Transcribed verbal order from the ward round for the patient in room 12. Pt is stable and
> tolerated insulin well previously. Order is insulin 10.0U SC QD HS. Labs were negative and
> glucose control is significant. Dose alert was cleared as clinically appropriate. This can
> be discontinued if there's a problem.

The defects, and the rule each breaks:

| Text | Rule broken |
|------|-------------|
| "Transcribed" with no actor | `STE-C-01` — unattributed actor |
| "the patient in room 12" | `STE-HLTH-08` — a room identifies a bed, not a person |
| "stable" | `STE-HLTH-05` — describes a rate of change, not a state |
| "tolerated insulin well" | Forbidden — an unmeasured global assessment |
| `10.0U` | `STE-HLTH-01`, `STE-HLTH-02` — **two** tenfold-error notations in five characters |
| `SC` | §3.3 — reads as `SL`, sublingual |
| `QD` | §3.3 — reads as `QID`, four times daily |
| `HS` | §3.3 — "half strength" or "at bedtime" |
| "Labs were negative" | `STE-HLTH-03`, `STE-HLTH-09` — which test, which value, when? |
| "glucose control is significant" | `STE-HLTH-04` — statistical or clinical? |
| "alert was cleared" | Forbidden — `override` or `suppress`? |
| "as clinically appropriate" | `STE-HLTH-10` — asserts the conclusion the alert tested |
| "can be discontinued if there's a problem" | `STE-C-08` — conditional, and no time bound |

The notation defects compound.
`10.0U SC QD HS` can be read as *100 units sublingual four times daily at half strength*.
The intended order is *10 units subcutaneous once daily at bedtime*.
That is a hundredfold dose error by a route the drug is not licensed for, at four times the
frequency, and every character of it is ordinary clinical shorthand.

### 6.2 Conforming record

```text
ACTION
agent.orderbot.v2 transcribed 1 medication order for patient identifier MRN-4417902 in the
Meridian Health MRN system.
The medication is insulin glargine. The dose is 10 units.
The route of administration is subcutaneous. The frequency is once daily at bedtime.
The indication is type 2 diabetes mellitus. The responsible clinician is Dr A. Okonkwo,
attending endocrinologist.

EFFECT SURFACE
Reversibility is hard. The medication order can be discontinued before the first dose is
administered. After administration the dose cannot be withdrawn.
Scope is single. The effect reaches patient identifier MRN-4417902 only.
Consequence is high. A tenfold insulin dose error causes severe hypoglycaemia and can cause
death.

RATIONALE AND RESIDUAL RISK
agent.orderbot.v2 transcribed the medication order because Dr A. Okonkwo entered a verbal
order at 2026-07-26T08:41:00Z during ward round.
The source of the order is verbal order record VO-2026-11884, recorded 2026-07-26T08:41:00Z.
The most recent fasting glucose is 9.4 mmol/L, observed 2026-07-26T06:15:00Z, reference range
4.0 to 6.0 mmol/L, from the Meridian laboratory system.
Alert CDS-INSULIN-DOSE stated: "Insulin dose exceeds the starting-dose threshold for a
patient with no prior insulin order". The clinical reason is that the patient has a
documented prior insulin glargine order at 10 units from encounter ENC-2025-3391. The
responsible clinician is Dr A. Okonkwo, attending endocrinologist.
The measured residual error bound is 0.0 on the CT4 held-out adversarial dose-transcription
set, measured on 2026-07-11.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the ward pharmacist discontinues the medication order before the
scheduled dose time. The pharmacist documents the discontinuation against MRN-4417902. The
named actor is the ward pharmacist. The time bound is until the scheduled dose time of
2026-07-26T22:00:00Z.

VERIFIER FINDING
VRF-DOSE-RANGE is a deterministic verifier.
The independence basis is different kind of checker.
VRF-DOSE-RANGE checked that 10 units of insulin glargine by the subcutaneous route once
daily is within the formulary dose range for an adult patient with a prior insulin order.
The verdict is pass.
The evidence is ev_dose_range_4417902_01.
```

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42` the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `hard` ranks 3, `single` ranks 1, and `high` ranks 4.
The maximum is 4.

Note what this shows.
Scope is `single` — one patient, the smallest value on that axis — and the action is still
CT4.
The `consequence` axis alone carries it. An intuition that tiers by blast radius gets this
wrong every time.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-DOSE-RANGE` runs before the order is signed. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic dose-range checker is a different *kind* of checker (`standard/LAAS.md:87`). A second LLM reading the same order would not qualify unless its measured error correlation is at or below `0.2` (`data.json:14`). |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented claim-class coverage for dose-range checks, a negative-test suite of known tenfold and route errors it must catch, and a change-controlled version in the trace. |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0.0` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | Dr Okonkwo approves the transcribed order before it becomes active. `standard/LAAS.md:89` makes the human required *in addition* to the deterministic verifier, not instead of it. |
| `LAAS-OBL-INP-001` | The verbal order is untrusted input until it is confirmed against VO-2026-11884. `untrusted_input_min_ct` is `3` (`data.json:18`). |

**Language conformance: `LC-3`**, with the §3.3 notation block applying unconditionally.

The rewrite changes no obligation and no threshold.
It changes what Dr Okonkwo is approving.
In §6.1 the record they approve can be read as a hundredfold overdose by the wrong route.
In §6.2 it can be read exactly one way.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

Institute for Safe Medication Practices.
*ISMP List of Error-Prone Abbreviations, Symbols, and Dose Designations.*
Plymouth Meeting, PA: ISMP, 2021.

Joint Commission.
*Official "Do Not Use" List of Abbreviations.*
Oakbrook Terrace, IL: The Joint Commission, 2004, revised 2019.

Kohn, Linda T., Janet M. Corrigan, and Molla S. Donaldson, eds.
*To Err Is Human: Building a Safer Health System.*
Washington, DC: National Academy Press, 2000.

Koppel, Ross, Joshua P. Metlay, Abigail Cohen, Brian Abaluck, A. Russell Localio,
Stephen E. Kimmel, and Brian L. Strom.
"Role of Computerized Physician Order Entry Systems in Facilitating Medication Errors."
*JAMA* 293, no. 10 (2005): 1197–1203.

World Health Organization.
*Medication Without Harm: WHO Global Patient Safety Challenge.*
Geneva: WHO, 2017.
