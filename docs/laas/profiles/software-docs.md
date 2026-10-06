# LAAS Controlled-Language Profile — Software and SaaS Documentation

**Designation:** LAAS-STE-SWD-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.1`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/software-docs.json`](glossary/software-docs.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not legal advice and does not state a legal obligation.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

Published documentation is executed, not read.
A reader copies a command from a page and runs it against their own system.
The effect surface of a documentation change is therefore the set of systems on which
readers run the instruction, not the set of files in the docs repository.

The word "revert" is where this goes wrong.
In a documentation repository, a revert restores a file to a prior commit.
It does not restore the reader who already ran the published command.
It does not evict the page from a CDN edge cache, from a search index, from a mirror, or
from a model training corpus that already crawled it.
An agent that writes "this page can be reverted" is stating something true about the
repository and false about consequence.
A human approver hears "reversible" and approves a CT4 publish as if it were CT1.

Documentation has a second, sharper problem.
A code example is a specification of behaviour, and readers treat it as tested even when it
is not.
An example containing a destructive command, a real credential, or an obsolete flag is a
defect that ships to every reader at once.
`LAAS-OBL-IND-001` asks for a verifier that can contest a claim
(`standard/LAAS.md:78`).
"The example looks correct" cannot be contested.
"The example was executed on runner `ci-docs-07` against version `4.2.0` and exited `0`" can.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Publish a page to the public documentation site | `irreversible` — readers, caches, and crawlers have the content | `public` | `material` to `high` | CT4 |
| Publish a code example that contains a destructive command | `irreversible` — readers execute it | `public` | `high` | CT4 |
| Publish a page that contains a credential or a private endpoint | `irreversible` — the secret is disclosed | `public` | `high` | CT4 |
| Publish a migration guide or an upgrade procedure | `irreversible` — readers run the procedure | `public` | `high` | CT4 |
| Change a documented API contract or a documented default value | `irreversible` — readers rely on the published contract | `public` | `material` | CT4 |
| Remove a published page, or redirect a published URL | `hard` — the URL and its inbound links are affected | `public` | `material` | CT4 |
| Publish a deprecation notice or an end-of-life date | `irreversible` — customers plan against the date | `public` | `material` | CT4 |
| Change a release note for a shipped version | `hard` — the prior text was already read | `public` | `material` | CT4 |
| Publish a page to an internal documentation site | `hard` | `org` | `material` | CT3 |
| Merge a documentation change to the default branch without publishing | `reversible` — a revert restores the file | `org` | `low` | CT1 |
| Publish to a staging site that no customer can reach | `reversible` | `single` | `low` | CT1 |
| Read a page, a schema, or a build log | `reversible` — read only | `single` | `none` | CT0 |

Four points about this table.

**A public publish is CT4 on the scope axis alone.**
`scope: public` ranks 4 in `conformance/laas/data.json:8`, and `standard/LAAS.md:42` takes
the maximum across the three axes, not the average.
A one-word typo fix on a public page is CT4 by the lattice.
Operators who find this expensive should change the scope of the action — publish to
staging first — not restate the scope of the same action.

**A revert is not a rollback.**
The repository is `reversible`. The publication is not.
Both axes are read independently, and the higher one sets the tier.

**A documentation change can be higher-tier than the code it documents.**
Code ships behind a flag, a canary, and a rollback.
A published page ships to every reader at once with none of the three.

**A read is CT0 only while it stays a read.**
Reading a build log to decide a publish is part of the publish.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
The rules below are additional and specific to this domain.
Section 2.1 states two deviations, both more restrictive than the core rules they refine.

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-SWD-01` | Write a code identifier, a command, a flag, a path, or an environment variable name verbatim, in backticks, exactly as the software accepts it. Never paraphrase it, never correct its case, and never split it across lines. | An identifier is executed, not read. A paraphrased identifier is a different identifier. See §2.1. |
| `STE-SWD-02` | State every version as the complete version string, in backticks, with its named scheme. Write `` `4.2.0` (semver) `` or `` `2024-10-01` (dated API version) ``. Never write *the latest version* or *a recent version*. | A claim about behaviour is only checkable against a named version. See §2.1. |
| `STE-SWD-03` | Never write *revert* to mean *undo a publication*. `revert` means only "restore a file to a prior commit". State the reversibility of the published page separately from the reversibility of the file. | This is the profile's single most important rule. See §1.1. |
| `STE-SWD-04` | State the publication target by name and by audience reach: `staging site`, `internal site`, or `public site`. Never write the bare word *deploy* or *ship*. | Reach is the `scope` axis in `conformance/laas/data.json:8`. An unnamed target makes scope `undetermined`, which forces CT4. |
| `STE-SWD-05` | State the publication state using one approved term: `drafted`, `merged`, `built`, `published`, `cached`, `withdrawn`. Do not invent an intermediate state. | Publication state determines what a rollback can still reach. A page that is `cached` is not recalled by a revert. |
| `STE-SWD-06` | For every code example, state the runtime, the version string, the command that executed it, the exit status, and the date of execution. If the example was not executed, write `not executed`. | An unexecuted example is a claim with no evidence. `not executed` is a conforming statement; silence is not. |
| `STE-SWD-07` | Never write the bare word *deprecated*. Write `deprecated` with the version that deprecated it and the version or date that removes it. | *Deprecated* alone tells a customer nothing they can plan against, and a removal date is a commitment. |
| `STE-SWD-08` | Never write *supported* without naming what supports what. Write `supported by <component> from version <string>`. | *Supported* is read as a contractual promise. An unqualified promise has unbounded scope. |
| `STE-SWD-09` | State a breaking change as `breaking change`, name the affected interface, and name the required reader action. Never write *small change*, *minor update*, or *cleanup*. | *Minor* collides with the semver level and with the `consequence` lattice. Both collisions hide a breaking change. |
| `STE-SWD-10` | Redact a credential, a token, a key, or a private endpoint before publication, and state the redaction. Write `redacted credential`. Never write a live value, and never write a value you have not confirmed is synthetic. | A published secret is `irreversible` on the reversibility axis. Rotation is a new secret, not a restored state. |
| `STE-SWD-11` | State a performance or availability figure as a number, a unit, a measurement basis, and a measurement date. Never write *fast*, *scalable*, or *highly available*. | `STE-C-10` requires a quantity with a basis. Marketing adjectives are the standard way that requirement is evaded in this domain. |
| `STE-SWD-12` | Write one instruction per numbered step. State the expected observable result of the step. | A step without an observable result gives the reader no way to detect that the step failed before running the next one. |
| `STE-SWD-13` | Name the source of every documented behaviour: the source file and line, the test, or the schema. Do not write "according to the docs". | A documented behaviour with no source is unverifiable, and a verifier cannot document claim-class coverage over it. |

### 2.1 Deviations from the core profile

The core profile permits an industry profile to deviate within its domain when the profile
states the deviation explicitly ([`ste-core.md`](ste-core.md) §2).
This profile states two.

**Deviation 1 — code identifier notation.**
`STE-C-04` gives each approved term one meaning and one part of speech, `STE-C-05` forbids
synonyms, and `STE-C-07` forbids a noun cluster longer than three words.
A literal code identifier is not a dictionary term and cannot be governed by those rules.
`ALLOW_UNSAFE_MIGRATIONS`, `/etc/app/config.d/10-db.yaml`, and `--force-recreate` are
strings the software parses, not English the writer may restructure.
This profile therefore exempts a literal identifier, command, flag, path, or environment
variable name from `STE-C-04`, `STE-C-05`, and `STE-C-07`, and from the sentence-length
counts of `STE-C-03`, and replaces them with a stricter rule: the identifier is written
verbatim, in backticks, and is repeated verbatim on every occurrence
(`STE-SWD-01`).
Paraphrase, case correction, hyphenation, and line-breaking are forbidden.
Justification: `LAAS-OBL-IRR-001` requires independent pre-commit verification at CT≥3
(`standard/LAAS.md:77`), and a verifier re-executes the identifier it is given.
An identifier the writer has restructured for readability is a different string, so the
verifier's `pass` covers a command the reader will never run.
`LAAS-OBL-TRC-001` (`standard/LAAS.md:73`) makes the same point about the trace: an
append-only store fixes bytes, and only a verbatim identifier makes those bytes mean the
same thing in the record and on the page.
The deviation is more restrictive than the rules it refines.

**Deviation 2 — version notation.**
`STE-C-10` requires a quantity, a unit, and a measurement basis.
A version string is none of the three.
`4.2.0` has no unit, and `2024-10-01` as an API version designator is not a measurement.
This profile therefore exempts a version designator from `STE-C-10` and replaces it with a
stricter rule: the complete version string is written verbatim, in backticks, together with
the name of the scheme that produced it — semver, a dated API version, a build identifier,
or a commit SHA (`STE-SWD-02`).
A version range is written as an explicit interval with both bounds.
*Latest*, *current*, *recent*, and *newer* are forbidden, because each resolves to a
different value on a different day and the record is read later than it is written.
Justification: `LAAS-OBL-VQ-001` requires a change-controlled verifier version recorded in
the trace (`standard/LAAS.md:96`), and `LAAS-OBL-RES-001` requires the residual escape rate
to be re-measured on any model, prompt, tool, or policy change
(`standard/LAAS.md:102`).
Both obligations compare a record against a named version.
A floating word such as *latest* makes the comparison undefined, so the obligation passes on
paper and checks nothing.
`LAAS-OBL-VEN-001` (`standard/LAAS.md:76`) adds the third case: a third-party component's
scope limit is only a limit if the version it applies to is named.

Neither deviation changes a LAAS obligation, a tier, or a threshold.
Both are more restrictive than the core rules they refine.

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/software-docs.json`](glossary/software-docs.json) is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`publish` is the verb; `published page` is the noun.
`redirect` is the verb; `redirect rule` is the noun.

### 3.1 Approved technical nouns

Each noun carries exactly one approved meaning in this domain.

| Noun | Approved meaning |
|------|------------------|
| `API version` | The identifier of one published interface contract, stated as a version string and a named scheme. |
| `breaking change` | A change that makes a previously documented caller stop working without a change by that caller. |
| `build artifact` | The output file set produced by one documentation build, identified by a build identifier. |
| `build identifier` | The unique identifier of one documentation build run. |
| `canonical URL` | The one URL that a published page declares as its own address for indexing. |
| `changelog entry` | The record of one shipped change, bound to one version string. |
| `code example` | A block of code or commands in a page that a reader is expected to run. |
| `code identifier` | A literal string the software parses: a symbol name, a command, a flag, a path, or an environment variable name. |
| `commit SHA` | The content hash that identifies one commit in the source repository. |
| `default value` | The value a documented parameter takes when the caller supplies none. |
| `deprecation notice` | A published statement that names a feature, the version that deprecated it, and the version or date that removes it. |
| `documentation site` | One published web location that serves pages to a stated audience. |
| `edge cache` | A content delivery network store that serves a copy of a published page after the origin changes. |
| `end-of-life date` | The stated date after which a named version receives no further support. |
| `environment variable` | A named runtime value read by the software, written verbatim as a code identifier. |
| `exit status` | The integer a command returns to its caller on completion. |
| `feature flag` | A named runtime switch that enables or disables a behaviour without a code change. |
| `internal site` | A documentation site reachable only by members of the publishing organization. |
| `migration guide` | A published procedure that moves a reader's system from one named version to another named version. |
| `public site` | A documentation site reachable by any reader on the internet. |
| `published page` | One page that has reached a documentation site and can be fetched by a reader of that site. |
| `publication state` | One of `drafted`, `merged`, `built`, `published`, `cached`, `withdrawn`. |
| `redacted credential` | A placeholder written in place of a secret value, marked as a placeholder. |
| `redirect rule` | A published mapping from one URL to another URL, served to every request for the first URL. |
| `release note` | The customer-facing description of the changes in one named version. |
| `runtime` | The named program and version that executes a code example. |
| `semver string` | A version string of the form `MAJOR.MINOR.PATCH` under Semantic Versioning. |
| `source of record` | The file, test, or schema that proves a documented behaviour, cited by path and line. |
| `staging site` | A documentation site reachable only by the publishing team, used before a public publish. |
| `support statement` | A published claim that a named component works with a named component from a named version. |
| `upgrade path` | The ordered sequence of versions a reader must pass through to reach a target version. |
| `version string` | The complete literal designator of one release, written verbatim with its named scheme. |

### 3.2 Approved technical verbs

Each verb carries one approved meaning.
Write the imperative form in an instruction and the simple past in a completed-action
statement (`STE-C-08`).

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `approve` | Record a named party's decision to permit an action. | `approve` |
| `block` | Prevent an action from proceeding, with the reason recorded. | `block` |
| `build` | Produce a build artifact from source files by running a named build command. | `build` |
| `cite` | Name the source of record for a stated behaviour, by path and line. | `cite` |
| `deprecate` | Publish a deprecation notice that names the deprecating version and the removal version or date. | `deprecate` |
| `execute` | Run a code example on a named runtime and record the exit status. | `execute` |
| `invalidate` | Instruct an edge cache to discard its stored copy of a named URL. | `invalidate` |
| `merge` | Combine a change into the default branch of the source repository. | `merge` |
| `pin` | Fix a dependency or an example to one named version string. | `pin` |
| `publish` | Make a page fetchable by readers of a named documentation site. | `publish` |
| `redact` | Replace a secret value with a marked placeholder before publication. | `redact` |
| `redirect` | Serve requests for one URL from another URL by a published redirect rule. | `redirect` |
| `restore` | Return a named file to a named prior state in the source repository. | `restore` |
| `revert` | Restore a file to a prior commit. The published copy is unaffected. | `revert` |
| `review` | Read a change against stated criteria and record the findings. | `review` |
| `rotate` | Replace a disclosed secret with a new secret value. | `rotate` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `withdraw` | Remove a published page from a documentation site and record the removal. | `withdraw` |

### 3.3 Forbidden terms

These words are dangerously ambiguous in this domain.
Each row states the replacement.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *revert* (as "undo a publication") | A revert restores a file. It does not recall a published page. See `STE-SWD-03`. | `revert` only for the repository; `withdraw` for the page; state page reversibility separately |
| *deploy*, *ship*, *push live* | No named target and no stated reach, so the `scope` axis is unassessable. | `publish to the <staging\|internal\|public> site` |
| *latest*, *current*, *recent*, *newer* (as a version) | Resolves to a different value on a different day. | The version string and its named scheme |
| *minor* (informal) | Collides with the semver level and with the `consequence` enum at `data.json:9`. | The semver level, or the enum value, or the stated number |
| *just*, *simply*, *only* (before an instruction) | Asserts the step is easy and suppresses the failure case. | The step, and its expected observable result |
| *should work*, *should be safe* | States a hope, not an executed result (`ste-core.md` §3.2). | The exit status, the runtime, and the date of execution, or `not executed` |
| *fast*, *scalable*, *highly available* | Self-assessed performance with no measurement basis (`STE-SWD-11`). | The number, the unit, the measurement basis, and the date |
| *supported* (bare) | Reads as a contractual promise of unbounded scope. | `supported by <component> from version <string>` |
| *deprecated* (bare) | Gives the reader no date and no version to plan against. | `deprecated in <version>, removed in <version or date>` |
| *cleanup*, *tidy-up*, *small change*, *minor update* | Hides a breaking change behind a size adjective. | `breaking change`, the affected interface, and the required reader action |
| *the docs*, *the system* (as actor) | Unattributed actor. | The `actor_id` or the named component |
| *example key*, *dummy token* | Claims a value is synthetic without evidence. A real key has shipped this way. | `redacted credential`, with the redaction stated |
| *rollback* (for a published page) | Implies restoration of reader state, which no publication control provides. | `withdraw the published page`, then state what readers already ran |
| *etc.*, *and more* (in a flag or parameter list) | Unbounded scope in a list a reader will execute against. | The complete list, or the count and the selection rule |

## 4. Decision-trace field templates

The templates use only approved terms.
Angle brackets mark a slot.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <count> page(s) to the <staging|internal|public> site.
The pages are <paths>.
The selection rule is <rule>.
The documented component is <component> at version <version string> (<scheme>).
The publication state is <drafted|merged|built|published|cached|withdrawn>.
```

Filled:

```text
agent.docbot.v2 published 1 page to the public site.
The page is /docs/guides/upgrade-4-2.
The selection rule is pull request 1184 only.
The documented component is orchestrator at version 4.2.0 (semver).
The publication state is published.
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
Scope is <single|multi|org|public>. The effect reaches <named sites, caches, or audiences>.
Consequence is <none|low|material|high>. The stated harm is <one sentence, with a number where one exists>.
```

Filled:

```text
Reversibility is irreversible. A revert restores the file in the repository, and it does not
recall the page from the edge cache, from the search index, or from readers who already ran
the procedure.
Scope is public. The effect reaches the public documentation site, the CDN edge cache, and
every self-hosted operator who follows the upgrade path.
Consequence is high. The published procedure drops a database table before the backup step,
and 1,340 operators fetched the page in the first hour.
```

The second sentence of the reversibility line is where `STE-SWD-03` does its work.
It separates the file from the publication and states both.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The source of record is <path:line or test identifier>.
Each code example was executed on <runtime> at version <version string>, and the exit status
was <integer>, on <date>. Examples not executed are: <list, or none>.
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The rollback plan is: <step 1>. <step 2>. <step 3>. The named actor is <party>. The time bound is <duration>.
```

Filled:

```text
agent.docbot.v2 published the upgrade guide because release 4.2.0 changed the migration
command and the prior guide named the removed command.
The source of record is src/migrate/cli.py:88-131 and test tests/migrate/test_cli.py::test_v42_order.
Each code example was executed on python 3.12.4 against orchestrator 4.2.0, and the exit
status was 0, on 2026-08-11. Examples not executed are: none.
The measured residual error bound is 0.0 on the CT4 held-out adversarial docs set, measured
on 2026-07-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the docs operations team withdraws /docs/guides/upgrade-4-2. The team
invalidates the edge cache for that URL. The team publishes a correction notice on the
release-notes page and emails the operator mailing list. The named actor is the docs
operations team. The time bound is 1 hour.
Readers who already ran the published procedure are not restored by this plan.
```

The last sentence is required whenever the published content instructs a reader to act.
A withdrawal removes the page, not the effect.
Saying so is the point.

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
VRF-DOCS-EXEC is a deterministic verifier.
The independence basis is different kind of checker.
VRF-DOCS-EXEC executed every code example on the page in a disposable container at
orchestrator 4.2.0, compared each exit status against the documented exit status, and
matched every code identifier on the page against the shipped CLI grammar.
The verdict is pass.
The evidence is ev_docs_exec_1184.
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
An agent that writes "this is a docs-only change and can be reverted" is not editing
`gate_derived_ct`, but it is telling a human approver that the tier is wrong.
At CT4 the human approver is the control (`LAAS-OBL-HUM-001`), and an approver briefed with
"docs-only" approves a publication believing the blast radius stops at the repository.

This profile closes the channel in four places.
`STE-SWD-03` removes the specific word that carries the misdirection.
`STE-SWD-04` forces the publication target to be named, so the `scope` axis cannot be left
to an adjective.
`STE-SWD-06` converts "the example works" into an exit status and a date.
§4.2 pins the effect-surface prose to the same enum values the machine record uses, so the
two cannot disagree without the disagreement being visible.

### 5.2 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5, with one stated
deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1`, and the `STE-SWD-01`, `STE-SWD-02`, and `STE-SWD-10` findings at every tier | Advisory, except those three |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

**Deviation — identifier notation, version notation, and credential redaction block at
every tier.**
A wrong flag, a floating version word, and an unredacted credential cause the same harm in a
CT0 draft as in a CT4 publication, because the defect travels with the text when the text is
promoted.
A draft is the input to a publish.
Findings under `STE-SWD-01`, `STE-SWD-02`, and `STE-SWD-10` therefore block at every tier,
including CT0 and CT1.
Every other language finding follows the core gate policy unchanged.

The deviation is more restrictive than the core profile.
It changes no LAAS obligation, no tier, and no threshold.

By §1.2, every publication to a public site lands at CT4 on the `scope` axis alone.
The practical effect is that controlled language is blocking for public publication and
advisory for drafting.

### 5.3 Obligation mapping

Every obligation identifier below is taken from `conformance/laas/data.json:19-32` and
`standard/LAAS.md:68-81`.
No obligation is new.

| Obligation | CT floor | What this profile adds |
|------------|----------|------------------------|
| `LAAS-OBL-TIER-001` | 0 | `STE-SWD-04` names the publication target, so the `scope` axis is observed rather than implied. An unnamed target is `undetermined` and defaults to CT4 (`standard/LAAS.md:44`). |
| `LAAS-OBL-SELF-001` | 0 | `STE-SWD-03` and the forbidden entry for *deploy* remove the two phrasings that let an agent describe a public publication as a local file change. |
| `LAAS-OBL-ENF-001` | 0 | Nothing directly. Enforcement-plane integrity is structural. |
| `LAAS-OBL-TRC-001` | 0 | `STE-SWD-01` keeps identifiers byte-identical between the record and the page, so an append-only trace preserves meaning and not only bytes. |
| `LAAS-OBL-AGG-001` | 0 | `STE-SWD-12` and `STE-SWD-04` make records comparable across pages, so a sequence of small page edits that together change a documented contract can be counted (`standard/LAAS.md:59-60`). |
| `LAAS-OBL-INP-001` | 0 | `STE-SWD-13` names the source of every documented behaviour, so content taken from an untrusted issue, forum post, or model output is distinguishable from content taken from the source of record. |
| `LAAS-OBL-VEN-001` | 0 | `STE-SWD-08` and `STE-SWD-02` turn a support statement into a named component and a named version, which is the only form a scope limit can take. |
| `LAAS-OBL-IRR-001` | 3 | `STE-SWD-06` supplies the pre-commit evidence: the runtime, the version, the command, the exit status, and the date. |
| `LAAS-OBL-IND-001` | 3 | A deterministic example-executor is a different kind of checker (`standard/LAAS.md:87`), and `STE-SWD-01` is what lets it execute exactly what the reader will execute. |
| `LAAS-OBL-VQ-001` | 3 | Claim-class coverage needs a stable claim class. `STE-SWD-02` and Deviation 2 bind every claim to a named version. |
| `LAAS-OBL-RES-001` | 2 | `STE-SWD-11` forces a number, a unit, a basis, and a date, which is the only form comparable against `escape_rate_tolerance_by_ct` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | 4 | The §4.3 closing sentence tells the CT4 approver, in one sentence, that withdrawal does not restore readers who already acted. |

### 5.4 How language non-conformance should be treated

A language finding is a finding about the **record**, not about the action.
The recommended handling mirrors the split the policy already makes between
`error_violations` (`conformance/laas/laas.rego:199`) and `warning_violations`
(`conformance/laas/laas.rego:204`).

At CT2 the finding is recorded and the action proceeds.
At CT3 and CT4 the record is rejected and the actor must rewrite it.
Rejection is not a block on the action itself: after a conforming rewrite, the action
proceeds through the normal obligation checks.

The checker must not rewrite the record (see [`ste-core.md`](ste-core.md) §5).
This constraint bites hard in this domain.
A checker that "corrects" `--force-recreate` to `--force_recreate` has authored a command
the actor never wrote and the software never accepts.
The checker reports the finding and blocks.

A rewrite is an **append**, not an edit.
`LAAS-OBL-TRC-001` requires an append-only trace (`standard/LAAS.md:108-111`).
The rejected record and the corrected record both stay in the chain.

## 6. Worked example

**Action.** A documentation agent is asked to publish an upgrade guide for release `4.2.0`
to the public documentation site. Release `4.2.0` changed the order of the migration
commands: the backup step now runs before the schema drop, and the flag that skipped the
backup was removed.

### 6.1 Non-conforming record

> The system updated the upgrade docs for the latest release and shipped them. The migration
> steps were cleaned up a bit and the examples should work. This is a docs-only change, so
> if there's an issue it can be reverted. Just run the migrate command with the usual flags.
> Performance is much better in this version.

Eleven defects, and each maps to a rule:

| Text | Rule broken |
|------|-------------|
| "The system updated" | `STE-C-01`, forbidden *the system* — unattributed actor |
| "the latest release" | `STE-SWD-02`, Deviation 2 — floating version designator |
| "shipped them" | `STE-SWD-04` — no named target, so `scope` is unassessable |
| "cleaned up a bit" | `STE-SWD-09`, forbidden *cleanup* — a breaking change described as a size |
| "the examples should work" | `STE-SWD-06`, `ste-core.md` §3.2 — a hope, not an exit status |
| "docs-only change" | `STE-SWD-04` — asserts a low scope by adjective |
| "it can be reverted" | `STE-SWD-03` — the load-bearing error; also `STE-C-06`, no antecedent |
| "Just run" | Forbidden *just* — suppresses the failure case |
| "the migrate command" | `STE-SWD-01` — a paraphrase, not a verbatim code identifier |
| "the usual flags" | `STE-SWD-01`, forbidden *etc.* class — an unbounded flag list the reader will execute |
| "Performance is much better" | `STE-SWD-11` — a performance claim with no number and no basis |

The dangerous pair is "docs-only change" and "it can be reverted".
A human approver reading them approves a CT4 publication believing the effect stops at the
repository.
The machine record says `scope: public` and `reversibility: irreversible`.
Both are in the same trace, and the human read the prose.

### 6.2 Conforming record

```text
ACTION
agent.docbot.v2 published 1 page to the public site.
The page is /docs/guides/upgrade-4-2.
The selection rule is pull request 1184 only.
The documented component is orchestrator at version 4.2.0 (semver).
The publication state is published.

EFFECT SURFACE
Reversibility is irreversible. A revert restores the file in the repository, and it does not
recall the page from the edge cache, from the search index, or from readers who already ran
the procedure.
Scope is public. The effect reaches the public documentation site, the CDN edge cache, and
every self-hosted operator who follows the upgrade path.
Consequence is material. The procedure drops and rebuilds the `events` table, and a reader
who runs the steps in the published order without the backup loses that table.

RATIONALE AND RESIDUAL RISK
agent.docbot.v2 published the upgrade guide because release 4.2.0 removed the
`--skip-backup` flag and reordered the migration steps, and the prior guide named the removed
flag.
This is a breaking change. The affected interface is the `orchestrator migrate` command. The
required reader action is to remove `--skip-backup` from any automation before upgrading to
4.2.0.
The source of record is src/migrate/cli.py:88-131 and test tests/migrate/test_cli.py::test_v42_order.
Each code example was executed on python 3.12.4 against orchestrator 4.2.0, and the exit
status was 0, on 2026-08-11. Examples not executed are: none.
The example connection string contains a redacted credential.
The measured residual error bound is 0.0 on the CT4 held-out adversarial docs set, measured
on 2026-07-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is at the tolerance.
The rollback plan is: the docs operations team withdraws /docs/guides/upgrade-4-2. The team
invalidates the edge cache for that URL. The team publishes a correction notice on the
release-notes page and emails the operator mailing list. The named actor is the docs
operations team. The time bound is 1 hour.
Readers who already ran the published procedure are not restored by this plan.

VERIFIER FINDING
VRF-DOCS-EXEC is a deterministic verifier.
The independence basis is different kind of checker.
VRF-DOCS-EXEC executed every code example on the page in a disposable container at
orchestrator 4.2.0, compared each exit status against the documented exit status, and
matched every code identifier on the page against the shipped CLI grammar.
The verdict is pass.
The evidence is ev_docs_exec_1184.
```

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42`, the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `irreversible` ranks 4, `public` ranks 4, and
`material` ranks 3. The maximum is 4.

The tier does not depend on the consequence assessment being right.
`scope: public` alone ranks 4.
This is the practical reason a documentation agent cannot argue itself down a tier by calling
a change small.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-DOCS-EXEC` runs before publication, not after. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a container that executes the examples is a different *kind* of checker (`standard/LAAS.md:87`), so no error-correlation measurement is needed. |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented claim-class coverage over executable examples and code identifiers, a negative-test suite of known-bad pages it must catch, and a change-controlled version in the trace (`standard/LAAS.md:95-96`). |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0.0` (`data.json:15`). |
| `LAAS-OBL-HUM-001` | A human approver approves before publication, and `escalation_approved` is `true`. |
| `LAAS-OBL-AGG-001` | The windowed aggregate is checked. Several page edits that together change one documented contract re-tier as one change (`standard/LAAS.md:59-60`). |
| `LAAS-OBL-VEN-001` | Any third-party component named in the guide carries its version string and its scope limit. |

**Language conformance: `LC-3`** — tool-checked, plus review of the free-text fields by the
human approver.

The rewrite changes no obligation and no threshold.
It changes what the CT4 human approver is approving.
In §6.1 they approve a "docs-only change" they believe is reversible.
In §6.2 they approve a breaking change, on a public site, whose rollback plan states in one
sentence that readers who already ran the procedure are not restored.
That is the same control doing its job instead of appearing to.

## Annex A (informative): Bibliography

Aerospace, Security and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Standard for technical documentation.*
Issue 9. Brussels: ASD, January 2025.
<https://www.asd-ste100.org/>

Bradner, Scott.
*Key words for use in RFCs to Indicate Requirement Levels.*
RFC 2119, BCP 14. Internet Engineering Task Force, 1997.

International Organization for Standardization, International Electrotechnical Commission,
and Institute of Electrical and Electronics Engineers.
*ISO/IEC/IEEE 26514:2022, Systems and software engineering — Design and development of
information for users.*
Geneva: ISO, 2022.

International Organization for Standardization, International Electrotechnical Commission,
and Institute of Electrical and Electronics Engineers.
*ISO/IEC/IEEE 26515:2018, Systems and software engineering — Developing information for
users in an agile environment.*
Geneva: ISO, 2018.

Preston-Werner, Tom.
*Semantic Versioning 2.0.0.*
2013.
