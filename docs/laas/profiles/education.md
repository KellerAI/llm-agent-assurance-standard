# LAAS Controlled-Language Profile — Education and Academic

**Designation:** LAAS-STE-EDU-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.1`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/education.json`](glossary/education.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not regulatory guidance and does not state a legal obligation.
> Named citation styles are cited as published works. This document does not reproduce them.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

Education is the one domain where the LAAS failure mode has the same name as the domain's
core activity.
`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.
In education the agent literally grades.
An agent that assigns a final grade and then writes its own account of why the grade is
correct is doing the thing the invariant names, twice, in one record.

The word *grade* is where this goes wrong.
A grade can be a raw score on one assignment, a weighted score against a rubric criterion, a
letter awarded for a course, or the grade of record on a transcript.
Only the last one leaves the institution.
An agent that writes "the grade was updated" has said nothing about which of the four
changed, and therefore nothing about reversibility.
A corrected gradebook entry is reversible.
A corrected grade of record is not: the original grade stays in the transcript history, the
student has read it, and any third party the transcript reached has read it too.

The word *pass* is the second hazard, and it is specific to LAAS.
`pass` is a verdict value in the decision record (`standard/LAAS.md:135`).
`pass` is also a grade in a pass/fail course.
A record that contains both senses of `pass` in free text makes the verifier finding
unreadable by the party who most needs to read it.
This profile reserves `pass` for the verdict and forbids it as a grading term.

The domain has a third reason.
An academic-integrity finding is an accusation against a named person.
It is recoverable on paper — an appeal can overturn it — and unrecoverable in fact, because
the accusation was already delivered.
Prose that describes such a finding as "flagged for review" understates an action that has
already reached the student.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Record an academic-integrity finding against a named student | `irreversible` — the accusation is delivered | `single` to `org` | `high` | CT4 |
| Release grades of record for a course section to the registrar | `hard` — a correction is a new grade, not an erasure | `multi` | `material` to `high` | CT4 |
| Change a degree-conferral or progression decision | `irreversible` | `single` | `high` | CT4 |
| Change a financial aid award | `hard` — recoverable, with loss to the student | `single` | `high` | CT4 |
| Disclose an education record to a third party | `irreversible` — the third party has read it | `single` to `public` | `high` | CT4 |
| Invalidate an exam attempt | `hard` | `single` | `material` | CT3 |
| Deny a disability accommodation request | `hard` | `single` | `material` | CT3 |
| Publish a final grade to one student | `hard` — the student has read it | `single` | `material` | CT3 |
| Apply a late-submission deduction in the gradebook | `reversible` | `single` | `low` | CT1 |
| Recalculate a weighted score in the gradebook before release | `reversible` | `single` | `low` | CT1 |
| Read a submission or a rubric | `reversible` — read only | `single` | `none` | CT0 |

Three points about this table.

Release is the tier boundary.
The same arithmetic is CT1 inside the gradebook and CT4 once it becomes a grade of record.
The axis that moves is `scope`, and the axis that moves with it is `reversibility`.

A batch of grades is not high-tier because it is large.
`standard/LAAS.md:42` takes the maximum across the three axes, so one final grade that
decides degree conferral raises `consequence` to `high` for the whole release, whatever the
count.

The anti-structuring rule at `standard/LAAS.md:59-60` applies to grade releases.
Releasing one course section at a time does not make a term-wide release a sequence of
`single`-scope actions.
`LAAS-OBL-AGG-001` is the control, and comparable prose across records is what makes the
aggregate countable.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
No core rule is weakened.
§2.1 adds domain rules. §2.2 states two refinements that narrow the application of a core
rule without relaxing it.

### 2.1 Domain rules

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-EDU-01` | Write in the active voice and name the deciding party. Do not write "the grade was changed". | A grade change is a decision by an accountable party. The passive voice removes the party while the appeal question is exactly which party decided. |
| `STE-EDU-02` | Never write the bare word *grade*. Write `raw score`, `weighted score`, `final grade`, or `grade of record`. | The four differ in reversibility and in scope. See §1.1. |
| `STE-EDU-03` | Never write *pass* or *fail* as a grading outcome. Write `credit awarded` or `credit not awarded`. Reserve `pass` and `fail` for the `verdict` values at `standard/LAAS.md:135`. | A record cannot carry two meanings for the word that states the verifier's verdict. |
| `STE-EDU-04` | State every score as a number, a maximum, and the named scale. Write `raw score 42 of 50 on scale POINTS-50`. | A score without a maximum is not a quantity, and `LAAS-OBL-RES-001` compares quantities. |
| `STE-EDU-05` | Name the rubric by identifier and version, and name the `rubric criterion` scored. Do not write "per the rubric". | A verifier can re-score a named criterion of a named rubric version. It cannot re-score a category. |
| `STE-EDU-06` | State a `plagiarism similarity score` as a percentage with the named matching service and the exclusion settings. Never write the word *plagiarism* as a conclusion. | Similarity is a measurement. Plagiarism is a finding by a named decision-maker after a process. |
| `STE-EDU-07` | Identify a student by `student identifier` and name the identifier system. Do not write the student's name in a decision record. | `LAAS-OBL-VEN-001` turns on what left the institution and to whom. A name is a disclosure; an identifier is a reference. |
| `STE-EDU-08` | State the release state of a grade using one approved term: `draft`, `provisional`, `released to student`, `grade of record`. Do not invent an intermediate state. | Release state determines reversibility, and reversibility determines the tier. An unapproved state word makes the axis `undetermined`, which forces CT4 (`data.json:11`). |
| `STE-EDU-09` | For any disclosure of an `education record`, state the recipient, the record count, the field list, and the legal basis by its identifier. Do not write "shared with a partner". | `LAAS-OBL-VEN-001` requires third-party attribution and scope limits. "Some student data" has no scope. |
| `STE-EDU-10` | State the appeal route as named steps with a named office and a stated deadline. Do not write it in the conditional. | `LAAS-OBL-IRR-001` requires a rollback plan at CT3 and above. "The student could appeal" is not a plan. |
| `STE-EDU-11` | Do not describe a student, a submission, or a cohort with an evaluative adjective. State the measurement. | *Strong*, *weak*, *concerning*, and *improved* are the four words that carry an unevidenced judgement into a permanent record. |
| `STE-EDU-12` | Write *material* only as the `consequence` lattice value from `conformance/laas/data.json:9`. Do not use *material* to mean course content. Write `course material` for content. | The word is a LAAS enum value and an everyday education term. Using it loosely corrupts the enum. |

### 2.2 Deviations from the core rules

Both deviations are stated explicitly, as [`ste-core.md`](ste-core.md) §2 requires of a
profile that departs from the core rule base.
Deviation 1 extends the approved dictionary inside one record.
Deviation 2 exempts one class of term from `STE-C-07` for its own length only.
Each applies to a named class of term and to nothing else.
Neither changes a LAAS obligation, a tier, or a threshold.

**Deviation 1 — grading-rubric terminology is admitted verbatim.**
`STE-C-04` gives each approved term exactly one meaning, and `STE-C-05` forbids a synonym
for an approved term.
Rubric level labels are institution-defined and cannot be enumerated in this dictionary:
one rubric uses `Exemplary`, `Proficient`, `Developing`, `Beginning`, and another uses four
different words for the same four bands.
The deviation is this.
A `rubric level` label is an approved term inside one record when the record quotes the
label verbatim from a cited `grading rubric` identifier and version, and the label is not
paraphrased, translated, or reordered anywhere in that record.
Any rubric label written without that citation is a non-conformance.

The justification is `LAAS-OBL-VQ-001`.
That obligation requires a verifier to hold documented coverage of its **claim class**
(`standard/LAAS.md:95-96`).
In this domain the claim class is the `rubric criterion` at a stated `rubric level`.
A paraphrased label is a different claim, so coverage of the original label proves nothing
about it, and qualification cannot be demonstrated.
`LAAS-OBL-TRC-001` gives the second half of the reason: an append-only store fixes the
bytes, not the meaning, so a label that drifts between records changes the content of the
earlier record without an append.
Verbatim quotation with a version identifier is what makes the earlier record stable.

**Deviation 2 — a named citation style is a fixed designation.**
`STE-C-07` forbids a noun cluster longer than three words.
`APA 7th edition reference list entry` is five words and cannot be broken with prepositions
without changing what it names.
The deviation is this.
The name and edition of a published citation style is a single fixed designation and is
exempt from `STE-C-07` for its own length.
The exemption covers the style designation only, not the sentence around it.
Write the style name **and** the edition or version in every use: `APA 7th edition`,
`MLA 9th edition`, `Chicago 17th edition`.
The bare style name, the bare words *citation style*, and *properly cited* are
non-conformances.

The justification is `LAAS-OBL-VEN-001` and `LAAS-OBL-IND-001`.
A citation check is performed against a third-party published rule set, and
`LAAS-OBL-VEN-001` requires that third party to be attributed with its scope limit stated.
The edition is the scope limit: a checker qualified for one edition is not qualified for the
next one.
`LAAS-OBL-IND-001` needs `independence_basis` to be checkable
(`standard/LAAS.md:87-89`), and a deterministic `citation checker` is a different kind of
checker only with respect to a named, versioned rule set.
"Checked the citations" names no rule set and therefore establishes no basis.

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
`glossary/education.json` is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`grade` is the verb; `final grade` and `grade of record` are the nouns.
`submit` is the verb; `submission` is the noun.

### 3.1 Approved technical nouns

Each noun carries exactly one approved meaning in this domain.

| Noun | Approved meaning |
|------|------------------|
| `academic integrity case` | An open investigation record about suspected misconduct by a named student. |
| `academic term` | The scheduled period, identified by a term code, in which a course section runs. |
| `accommodation` | An approved adjustment to an assessment condition for one student, recorded with its authorizing office. |
| `accreditation report` | A record submitted to an external accrediting body about programme outcomes. |
| `assessment` | One graded task or examination that produces a raw score for one student. |
| `attempt` | One submission of one assessment by one student, numbered within the allowed attempt limit. |
| `citation checker` | A deterministic tool that compares reference list entries against one named citation style edition. |
| `citation style` | A published rule set for references, named with its edition, such as `APA 7th edition`. |
| `cohort` | The set of students enrolled in one course section or one programme intake. |
| `course section` | One scheduled instance of a course in one academic term, identified by a section code. |
| `credit hour` | The unit of academic workload a course carries toward a programme of study. |
| `degree conferral` | The institutional decision that awards a qualification to a named student. |
| `disciplinary sanction` | A penalty imposed on a student after an academic integrity case is decided. |
| `education record` | A record about an identified student that the institution maintains and that disclosure rules govern. |
| `enrollment record` | The record that states which course sections a student is registered in for one academic term. |
| `exclusion setting` | A configured filter on a similarity report, such as quoted text or reference list exclusion. |
| `final grade` | The grade awarded to one student for one course section after all assessments are scored. |
| `financial aid award` | The stated amount of aid granted to one student for one academic term. |
| `grade of record` | The final grade after it is posted to the transcript. A correction adds a new entry; the prior entry remains. |
| `gradebook` | The internal store of raw scores and weighted scores for one course section before release. |
| `grade point average` | The credit-hour-weighted mean of grade points across a stated set of course sections. |
| `grading rubric` | A versioned document that lists rubric criteria, rubric levels, and the points for each level. |
| `learning management system` | The named system that holds submissions, gradebooks, and release states. |
| `learning outcome` | A stated capability a programme or course section claims a student demonstrates. |
| `matching service` | The named external service that computes a plagiarism similarity score. |
| `plagiarism similarity score` | The percentage of a submission that a named matching service matched to indexed sources under stated exclusion settings. |
| `proctoring session` | One monitored examination sitting for one student, identified by a session reference. |
| `programme of study` | The named set of courses and requirements leading to one qualification. |
| `progression decision` | The decision that permits or refuses a student's advance to the next stage of a programme of study. |
| `raw score` | The unweighted points a student earned on one assessment, stated with the maximum and the scale. |
| `reference list entry` | One bibliographic entry in a submission, checked against one named citation style edition. |
| `registrar` | The office that holds the transcript and posts the grade of record. |
| `release state` | One of `draft`, `provisional`, `released to student`, `grade of record`. |
| `rubric criterion` | One scored dimension of a grading rubric, identified within a stated rubric version. |
| `rubric level` | One named performance band of one rubric criterion, quoted verbatim from the cited rubric version. |
| `similarity report` | The output of a matching service for one submission, including the plagiarism similarity score and the matched sources. |
| `student identifier` | The institution-issued identifier for one student, stated with its identifier system. |
| `submission` | The artifact a student submits for one attempt at one assessment, with its submission timestamp. |
| `transcript` | The institution's cumulative record of grades of record and credit hours for one student. |
| `weighted score` | A raw score after the assessment weighting is applied, stated with the weighting scheme. |
| `withdrawal` | A recorded exit of a student from a course section or a programme of study, with its effective date. |

### 3.2 Approved technical verbs

Each verb carries one approved meaning.
Write the imperative form in an instruction and the simple past in a completed-action
statement (`STE-C-08`).

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `admit` | Record a decision to accept a named applicant into a programme of study. | `admit` |
| `appeal` | Ask a named office to review a recorded decision within a stated deadline. | `appeal` |
| `assess` | Apply a grading rubric to one submission and produce a raw score. | `assess` |
| `award` | Record credit hours, a financial aid award, or a degree conferral for a named student. | `award` |
| `cite` | Record the source of a claim as a reference list entry in one named citation style edition. | `cite` |
| `deduct` | Reduce a raw score by a stated number of points under a named published policy. | `deduct` |
| `disclose` | Send an education record to a named recipient outside the institution. | `disclose` |
| `enroll` | Register a named student in a named course section for one academic term. | `enroll` |
| `exempt` | Release a named student from a stated requirement, with the authorizing office recorded. | `exempt` |
| `extend` | Move a stated deadline for a named student to a stated new date. | `extend` |
| `grade` | Convert weighted scores into a final grade for one course section. | `grade` |
| `invalidate` | Void one attempt so that it produces no raw score, with the reason recorded. | `invalidate` |
| `moderate` | Re-score a sample of submissions by a second assessor and record the agreement rate. | `moderate` |
| `post` | Write a final grade to the transcript, making it the grade of record. | `post` |
| `proctor` | Monitor one examination sitting and record the observations. | `proctor` |
| `recalculate` | Recompute a weighted score or a grade point average from unchanged raw scores. | `recalculate` |
| `refer` | Route a suspected misconduct case to the named office that decides it. | `refer` |
| `release` | Change the release state of a final grade so that a named audience can read it. | `release` |
| `revoke` | Withdraw a previously awarded credit, aid, or qualification, with the deciding party recorded. | `revoke` |
| `sanction` | Impose a disciplinary sanction after an academic integrity case is decided. | `sanction` |
| `submit` | Deliver a submission or a record to a named system or office. | `submit` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `withdraw` | Record a student's exit from a course section or a programme of study, with an effective date. | `withdraw` |

### 3.3 Forbidden terms

These words are dangerously ambiguous in this domain.
Each row states the replacement.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *grade* (bare noun) | Means a raw score, a weighted score, a final grade, or a grade of record. The four differ in reversibility. | `raw score`, `weighted score`, `final grade`, or `grade of record` |
| *pass*, *fail* (as grades) | Collide with the `verdict` values at `standard/LAAS.md:135`. | `credit awarded`, `credit not awarded` |
| *score* (bare) | Means a raw score, a weighted score, or a plagiarism similarity score. | The qualified noun, with its maximum and scale |
| *credit* (bare) | Means `credit hour`, awarded credit, or attribution of a source. | `credit hour`, `credit awarded`, or `cite` |
| *plagiarism* (as a conclusion) | Names a finding that only a decision process can make. | `plagiarism similarity score` with the matching service, or the decided `academic integrity case` |
| *AI-generated* (as a determination) | States an origin as a fact. A detector output is a measurement with a stated error rate, not an origin. | The detector name, its output value, its stated error rate, or `undetermined` |
| *cheating*, *dishonest* | Self-assessed conclusions about a named person. | The observation, the proctoring session reference, and the referral |
| *final* (bare) | Means the final grade, the final attempt, or a final decision under appeal. | `final grade`, `last attempt`, or `decision after appeal` |
| *drop* | Means `withdraw`, remove an enrollment record, or delete a record. Three meanings, one irreversible. | `withdraw`, `remove the enrollment record`, or `delete` |
| *satisfactory progress* | A funding term of art used as ordinary praise. | The named policy identifier and the measured threshold |
| *improved*, *strong*, *weak*, *concerning* | Evaluative adjectives in place of a measurement (`STE-EDU-11`). | The score, the maximum, the scale, and the comparison basis |
| *material* (informal) | Collides with the `consequence` enum value at `data.json:9`. | The enum value, or `course material` for content |
| *properly cited* | Asserts conformance to an unnamed rule set. | The named citation style edition and the citation checker verdict |
| *flagged for review* | Hides whether a person was already told. | `refer`, with the named office and the notification timestamp |
| *the system* (as actor) | Unattributed actor. | The `actor_id` or the named component |
| *citation style* (bare) | Names the published rule set without its edition. The edition is the scope limit that the `STE-C-07` exemption for a citation style designation depends on (§2.2, Deviation 2). | The style name and its edition, such as `APA 7th edition` |
| *APA*, *MLA*, *Chicago* (bare style name) | A bare style name with no edition cannot be checked against a scoped rule set (§2.2, Deviation 2). | The style name and its edition, such as `APA 7th edition`, `MLA 9th edition`, or `Chicago 17th edition` |

## 4. Decision-trace field templates

The templates use only approved terms.
Angle brackets mark a slot.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <count> <final grade|attempt|education record>(s).
The course section is <section code> in academic term <term code>.
The selection rule is <rule>.
The grading rubric is <rubric id> version <version>.
The release state is <draft|provisional|released to student|grade of record>.
```

Filled:

```text
agent.gradebot.v3 released 118 final grades.
The course section is BIO-204-01 in academic term 2026-SP.
The selection rule is all enrollment records with release state provisional on 2026-05-11.
The grading rubric is RUB-BIO204-LAB version 4.
The release state is grade of record.
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
Scope is <single|multi|org|public>. The effect reaches <named parties or systems>.
Consequence is <none|low|material|high>. The stated effect is <the decision the grade decides>.
```

Filled:

```text
Reversibility is hard. A correction posts a new grade of record, and the prior grade of
record remains in the transcript history.
Scope is multi. The effect reaches 118 students, the registrar, and the financial aid office.
Consequence is high. Three final grades decide degree conferral in academic term 2026-SP,
and one final grade of 0.0 carries a disciplinary sanction.
```

The second sentence of the reversibility line is where `STE-EDU-02` does its work.
It separates the correction from the record and states both.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The grading rubric is <rubric id> version <version>. The rubric criterion is <criterion id>.
The rubric level is "<label quoted verbatim>".
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The appeal route is: <step 1>. <step 2>. The named office is <office>. The deadline is <date>.
```

Filled:

```text
agent.gradebot.v3 released the final grades because every enrollment record in BIO-204-01
held a weighted score and a completed moderation sample.
The grading rubric is RUB-BIO204-LAB version 4. The rubric criterion is CRIT-03.
The rubric level is "Developing".
The measured residual error bound is 0.0 on the CT4 held-out adversarial set of 400
re-scored submissions, measured on 2026-04-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The appeal route is: the student files a grade appeal with the Office of the Registrar. The
department chair re-scores the named rubric criterion. The named office is the Office of the
Registrar. The deadline is 2026-06-10.
Recovery does not remove the prior grade of record from the transcript history.
```

The last sentence is required whenever the appeal route restores a decision but not a
record.
An appeal that adds an entry is not an erasure. Saying so is the point.

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
VRF-GRADE-ARITH is a deterministic verifier.
The independence basis is different kind of checker.
VRF-GRADE-ARITH checked that every final grade equals the weighting scheme applied to the
recorded raw scores under RUB-BIO204-LAB version 4.
The verdict is pass.
The evidence is ev_grade_recompute_204_01.
```

A model verifier must state its measured error correlation as a number, because
`standard/LAAS.md:88` makes independence conditional on that measurement being at or below
`max_error_correlation` (`data.json:14`, currently `0.2`).

## 5. Mapping to LAAS obligations and tiers

### 5.1 Zero-Trust and self-grading

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.
The structured fields already resist this: the gate computes `gate_derived_ct` from the
observed surface, and `LAAS-OBL-SELF-001` stops `self_reported_ct` from lowering it.

Prose is the remaining channel.
An agent that writes "the grade was updated in the system" is not editing `gate_derived_ct`,
but it is telling a human approver that the action stayed inside the gradebook.
At CT4 the human approver is the control (`LAAS-OBL-HUM-001`), and a control briefed with a
misleading summary is not independent of the party that briefed it.

This profile closes the channel in four places.
`STE-EDU-02` removes the word that carries the misdirection.
`STE-EDU-08` pins the release state to an enumerated set, so the reversibility axis cannot
be left implicit.
`STE-EDU-06` separates a measured similarity score from a misconduct finding.
§4.2 pins the effect-surface prose to the same enum values the machine record uses, so the
two cannot disagree without the disagreement being visible.

### 5.2 Obligation map

Every obligation ID and CT floor below is taken from `conformance/laas/data.json:20-31` and
`standard/LAAS.md:68-81`.
The column states what the obligation requires of a record in this domain.

| Obligation | CT floor | What it requires in this domain |
|------------|----------|---------------------------------|
| `LAAS-OBL-TIER-001` | 0 | The tier comes from the observed release state and recipients, not from the agent's account of them. `STE-EDU-08` keeps `undetermined` writable, so the default-to-CT4 rule at `standard/LAAS.md:44` fires. |
| `LAAS-OBL-SELF-001` | 0 | Effect-surface prose uses the `data.json:7-9` enum values, so a softer narrative cannot restate the tier below the gate's value. |
| `LAAS-OBL-ENF-001` | 0 | Nothing from language. Enforcement-plane integrity is structural. |
| `LAAS-OBL-TRC-001` | 0 | One meaning per term across records. A rubric level quoted verbatim (§2.2) keeps an earlier record's meaning fixed under an append-only store. |
| `LAAS-OBL-AGG-001` | 0 | Grade releases aggregate across course sections in one academic term. Comparable prose is what makes the windowed aggregate countable (`standard/LAAS.md:59-60`). |
| `LAAS-OBL-INP-001` | 0 | A submission is untrusted input. `untrusted_input_min_ct` is 3 (`data.json:18`), so prompt-carrying submissions raise the tier rather than being described as ordinary text. |
| `LAAS-OBL-VEN-001` | 0 | The matching service, the citation style edition, and any disclosure recipient are named with their scope limits (`STE-EDU-06`, `STE-EDU-09`, §2.2 Refinement 2). |
| `LAAS-OBL-IRR-001` | 3 | The appeal route is stated as completed-tense steps with a named office and a deadline (`STE-EDU-10`). |
| `LAAS-OBL-IND-001` | 3 | `independence_basis` names one of the three bases at `standard/LAAS.md:87-89`. A citation checker is a different kind of checker only against a named style edition. |
| `LAAS-OBL-VQ-001` | 3 | The claim class is the rubric criterion at a stated rubric level. Verbatim labels are what make the class stable enough to document coverage. |
| `LAAS-OBL-RES-001` | 2 | `STE-EDU-04` forces a score with a maximum and a scale, which is the only form a residual bound can be compared against `escape_rate_tolerance_by_ct` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | 4 | The approval package states what the student will read, in the words the student will read. |

Tier regimes are the normative minimums at `standard/LAAS.md:51-57`.
CT0 is trace only, and covers reading a submission.
CT1 adds a self-check, and covers gradebook arithmetic before release.
CT2 adds an independent automated check or a rehearsed rollback with a bounded residual, and
covers a provisional release inside one course section.
CT3 adds mandatory independent qualified pre-commit verification, and covers every action
that reaches one named student.
CT4 adds human approval, an abstention default, and full evidence, and covers every action
in §1.2 that reaches the transcript, the registrar, or a third party.

### 5.3 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5 without deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1` | Advisory |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

By §1.2, every action that leaves the gradebook lands at CT3 or CT4.
The practical effect is that controlled language is blocking for the actions a student ever
sees and advisory for everything else.

### 5.4 How language non-conformance should be treated

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
The sequence of a hedged draft followed by a conforming rewrite is itself an audit signal,
and in a domain with a formal appeal process it is also evidence a student may request.

## 6. Worked example

**Action.** A grading agent is asked to release final grades for course section BIO-204-01
to the registrar and to 118 students. One submission carries a plagiarism similarity score
of 61 percent from a matching service, and the agent assigns that student a final grade of
0.0 and refers the case.

### 6.1 Non-conforming record

> The system finished grading the class and the grades look reasonable overall, with a
> couple of borderline cases. One student's work was mostly plagiarized so they failed and
> were flagged for review. Scores were adjusted per the rubric where needed. The grades were
> released. If there's an issue it can be changed later.

Eleven defects, and each maps to a rule:

| Text | Rule broken |
|------|-------------|
| "The system finished grading" | `STE-C-01`, `STE-EDU-01` — unattributed actor |
| "the grades look reasonable" | Core §3.2 — impression, not observation |
| "overall", "mostly" | Core §3.2 — quantifier with no quantity |
| "a couple of borderline cases" | `STE-EDU-11` — evaluative adjective, no count |
| "plagiarized" | `STE-EDU-06`, forbidden — a conclusion stated as a measurement |
| "they failed" | `STE-EDU-03` — `fail` is a `verdict` value, not a grade |
| "flagged for review" | Forbidden — hides that the student was already referred |
| "Scores were adjusted" | `STE-EDU-04`, `STE-EDU-01` — which score, by how much, by whom |
| "per the rubric" | `STE-EDU-05` — no rubric identifier, version, or criterion |
| "The grades were released" | `STE-EDU-02`, `STE-EDU-08` — which grade, to which release state |
| "it can be changed later" | `STE-EDU-10`, `STE-C-06` — no appeal route, no antecedent |

The last one is the dangerous one.
A human approver reading "it can be changed later" will approve a CT4 action believing the
transcript is editable.
The machine record says `reversibility: hard`, and the transcript history keeps the original
entry.
Both are in the same trace, and the human read the prose.

### 6.2 Conforming record

```text
ACTION
agent.gradebot.v3 released 118 final grades.
The course section is BIO-204-01 in academic term 2026-SP.
The selection rule is all enrollment records with release state provisional on 2026-05-11.
The grading rubric is RUB-BIO204-LAB version 4.
The release state is grade of record.

EFFECT SURFACE
Reversibility is hard. A correction posts a new grade of record, and the prior grade of
record remains in the transcript history.
Scope is multi. The effect reaches 118 students, the registrar, and the financial aid office.
Consequence is high. Three final grades decide degree conferral in academic term 2026-SP,
and one final grade of 0.0 carries a disciplinary sanction.

RATIONALE AND RESIDUAL RISK
agent.gradebot.v3 released the final grades because every enrollment record in BIO-204-01
held a weighted score and a completed moderation sample.
The moderation sample is 24 submissions of 118, re-scored by a second assessor, with an
agreement rate of 0.96 on RUB-BIO204-LAB version 4.
The rubric criterion is CRIT-03. The rubric level is "Developing".
Student identifier SID-44120 in system BANNER-SID received a final grade of 0.0.
The plagiarism similarity score for that submission is 61 percent from matching service
TURNITIN-2026-04, with quoted text and reference list entries excluded.
agent.gradebot.v3 referred the submission to the Office of Academic Integrity on
2026-05-11T16:02:00Z. The student was notified at the same timestamp.
agent.gradebot.v3 makes no misconduct finding. The Office of Academic Integrity decides the
academic integrity case.
The measured residual error bound is 0.0 on the CT4 held-out adversarial set of 400
re-scored submissions, measured on 2026-04-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The appeal route is: the student files a grade appeal with the Office of the Registrar. The
department chair re-scores the named rubric criterion. The named office is the Office of the
Registrar. The deadline is 2026-06-10.
Recovery does not remove the prior grade of record from the transcript history.

VERIFIER FINDING
VRF-GRADE-ARITH is a deterministic verifier.
The independence basis is different kind of checker.
VRF-GRADE-ARITH checked that every final grade equals the weighting scheme applied to the
recorded raw scores under RUB-BIO204-LAB version 4.
The verdict is pass.
The evidence is ev_grade_recompute_204_01.
```

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42`, the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `hard` ranks 3, `multi` ranks 2, and `high` ranks 4.
The maximum is 4.

The count of 118 is not what raises the tier.
`consequence` is `high` because three final grades decide degree conferral and one carries a
disciplinary sanction.
A release of one final grade with the same two properties is also CT4.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-GRADE-ARITH` runs before the release, not after the registrar posts. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic re-computation is a different *kind* of checker (`standard/LAAS.md:87`), so no error-correlation measurement is needed. |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented coverage of the claim class (rubric criterion at a stated rubric level), a negative-test suite of known mis-weighted gradebooks it must catch, and a change-controlled version in the trace (`standard/LAAS.md:95-96`). |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0` (`data.json:15`). |
| `LAAS-OBL-INP-001` | Each submission is untrusted input. `untrusted_input_min_ct` is 3 (`data.json:18`). |
| `LAAS-OBL-VEN-001` | The matching service is named with its version and its exclusion settings, and the similarity score is not treated as a finding. |
| `LAAS-OBL-HUM-001` | The instructor of record approves before release, and `escalation_approved` is `true`. |
| `LAAS-OBL-AGG-001` | The windowed aggregate is checked. A term-wide release across course sections re-tiers the sequence (`standard/LAAS.md:59-60`). |

**Language conformance: `LC-3`** — tool-checked, plus review of the free-text fields by the
human approver.

The rewrite changes no obligation and no threshold.
It changes what the CT4 human approver is approving.
In §6.1 they approve a release they believe is editable, against a student the record says
was already judged.
In §6.2 they approve a release that states the similarity score as a measurement, names the
office that will decide the case, gives the student a deadline, and says in one sentence
that an appeal does not clear the transcript.
That is the same control doing its job instead of appearing to.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

American Educational Research Association, American Psychological Association, and National
Council on Measurement in Education.
*Standards for Educational and Psychological Testing.*
Washington, DC: American Educational Research Association, 2014.

American Psychological Association.
*Publication Manual of the American Psychological Association.*
7th ed. Washington, DC: American Psychological Association, 2020.

Modern Language Association of America.
*MLA Handbook.*
9th ed. New York: Modern Language Association of America, 2021.

University of Chicago Press.
*The Chicago Manual of Style.*
17th ed. Chicago: University of Chicago Press, 2017.

International Organization for Standardization.
*ISO 21001:2018, Educational organizations — Management systems for educational
organizations — Requirements with guidance for use.*
Geneva: ISO, 2018.

United States Congress.
*Family Educational Rights and Privacy Act.*
20 U.S.C. § 1232g; implementing regulations at 34 C.F.R. Part 99. Washington, DC, 1974.
