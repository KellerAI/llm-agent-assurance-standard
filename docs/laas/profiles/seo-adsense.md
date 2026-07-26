# LAAS Controlled-Language Profile — SEO, AdSense and Digital Advertising

**Designation:** LAAS-STE-ADV-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/seo-adsense.json`](glossary/seo-adsense.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> Product names are used descriptively. This document is not affiliated with, endorsed by,
> or an interpretation of the policies of any advertising platform or search engine.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

This domain has the opposite problem to banking and healthcare, and it is more dangerous
for being less obvious.

Banking knows its actions are serious. Healthcare knows its actions are serious.
Digital marketing has a user interface that says **Undo**, a version history, and a culture
that describes production changes as tweaks.
Everything looks reversible. Almost nothing is.

Three effects in this domain are irreversible in the LAAS sense, and all three are routinely
described as reversible:

**Spend is gone.**
Setting a budget cap back to its old value does not return the money spent while it was
wrong. An agent that raises a daily budget cap by a factor of ten at 09:00 and reverts at
17:00 has not reverted anything. It has spent the money and restored a setting.

**Publication cannot be unpublished.**
A published ad creative has been served. A published page has been crawled, cached,
screenshotted, syndicated, and scraped into somebody's training set. Deleting the page
changes what the origin serves. It does not change what the internet has.

**Deindexation is slow in one direction only.**
A `Disallow` rule or a `noindex` directive takes effect within days. Recovery takes weeks to
months, depends on a third party's recrawl schedule, and does not reliably restore prior
positions. This is the cleanest asymmetry in the domain: the destructive path is fast and
the recovery path is slow, external, and uncertain.

The vocabulary actively conceals all three.
The platform UI calls a state change **pause**, which sounds temporary.
The agent writes **revert**, which sounds complete.
The team calls a change an **optimization**, which asserts that the outcome is an improvement
before any outcome has been observed.
That last one is the domain's signature failure: *optimize* is a verb that grades its own
result. An agent that writes "optimized the bid strategy" has recorded a verdict, not an
action, and it has recorded it about its own work.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Edit `robots.txt` or deploy a `noindex` directive | `hard` — recovery depends on a third-party recrawl | `public` | `material` to `high` | CT4 |
| Change a canonical tag across a URL set | `hard` | `public` | `material` | CT4 |
| Deploy a redirect rule across a URL set | `hard` | `public` | `material` | CT4 |
| Publish an ad creative | `irreversible` — it has been served | `public` | `material` | CT4 |
| Publish or edit page content at scale | `irreversible` — crawled and cached | `public` | `material` | CT4 |
| Raise a budget cap or a bid amount | `irreversible` — spend cannot be recovered | `org` | `material` | CT4 |
| Upload an audience list containing personal data | `irreversible` — the data has left | `org` to `public` | `high` | CT4 |
| Inject or change structured data markup | `hard` | `public` | `material` | CT3 |
| Submit or change a sitemap | `hard` | `public` | `low` to `material` | CT3 |
| Add negative keywords across ad groups | `reversible`, but spend during the interval is not | `org` | `material` | CT3 |
| Change a campaign serving state to `paused` | `reversible`, but lost serving time is not | `org` | `material` | CT3 |
| Change an attribution model in reporting | `reversible` | `org` | `low` | CT2 |
| Read a performance report | `reversible` — read only | `single` | `none` | CT0 |

**Scope is `public` far more often than in the other two profiles.**
An SEO change is served to anyone who asks for the URL.
`public` ranks 4 on the scope axis (`conformance/laas/data.json:8`), so a change that reaches
the open web is CT4 on scope alone, regardless of how small it looks in a diff.

**The aggregation rule binds hard here.**
`LAAS-OBL-AGG-001` and `standard/LAAS.md:59-60` exist for sequences.
Bulk operations in this domain are sequences by construction: one bid change is CT2, and
four thousand bid changes in one window are not four thousand CT2 actions.
An agent that iterates a per-item change to stay under a per-action threshold is
structuring, whether or not it intends to.

### 1.3 Third-party dependency

Recovery in this domain usually depends on a party the operator does not control: a search
engine's recrawl, a CDN cache expiry, an ad review queue.
A rollback plan that depends on a third party's schedule is not a rollback plan, and this
profile requires the record to say so (`STE-ADV-04`).
This is the same constraint the banking profile places on beneficiary consent, arrived at
from a different direction.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
The rules below are additional and specific to this domain.

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-ADV-01` | Never write *optimize*, *improve*, or *boost*. State the parameter changed, the old value, and the new value. | These verbs record a verdict about the agent's own work before any outcome exists. This is self-grading in a single word. |
| `STE-ADV-02` | State the count of affected items, the selection rule that produced the set, and the platform. Never write "some pages" or "the campaigns". | The selection rule is the only part a verifier can re-execute. A count alone is not reproducible. |
| `STE-ADV-03` | Never write *revert* or *undo* for spend or for publication. State what the change restores and what it does not restore. | See §1.1. This is the profile's most important rule. |
| `STE-ADV-04` | When recovery depends on a third party, name the party and state that recovery is not guaranteed. Give the observed recovery interval, not a target. | `LAAS-OBL-IRR-001` requires a rollback plan at CT3. A plan that waits on somebody else's crawler is a hope with a timetable. |
| `STE-ADV-05` | Never write the bare word *impression*. Write `ad impression` for a serve event. Do not use the word for a perception. | The word means a counted event here and an opinion in ordinary English, and both readings occur in rationale text. |
| `STE-ADV-06` | Never write the bare word *traffic* or the bare word *organic*. Write `organic session` or `paid session`, with the measurement source. | *Traffic* silently merges sessions, users, clicks, and crawler hits, which have different denominators. |
| `STE-ADV-07` | Never write *rank* as a verb. Write `position` as a noun, with the query, the locale, the device, and the measurement date. | Position is a measurement with four required qualifiers. Without them the number is not comparable to any other number. |
| `STE-ADV-08` | State every monetary amount as a numeral, a currency code (ISO 4217), and a period. Write `EUR 400.00 per day`. | A budget without a period is not a budget. This is the field that turns a daily cap into a monthly one. |
| `STE-ADV-09` | Never write *pause* without stating whether serving stops and whether spend stops. Use `serving state` with an approved value. | *Pause* sounds temporary and reversible. The lost serving interval is neither. |
| `STE-ADV-10` | Never write the bare word *test*. Write `split test` for an experiment or `verify` for a check. | An A/B test measures an outcome. A verification checks a claim. `LAAS-OBL-IND-001` is about the second, and the word collision makes a record ambiguous about which one ran. |
| `STE-ADV-11` | State the identifiability of any uploaded audience data: `hashed identifiers`, `personal data`, or `aggregate only`. Name the destination platform. | `LAAS-OBL-VEN-001` requires vendor scope limits. An upload described as "the customer list" has no scope. |
| `STE-ADV-12` | Never write *conversion* alone. Write `conversion event` and name the event definition and the attribution model. | A conversion count is meaningless without its definition, and the definition is exactly what changes between reports. |

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/seo-adsense.json`](glossary/seo-adsense.json) is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`bid` is the verb; `bid amount` is the noun. `redirect` is the verb; `redirect rule` is the
noun.

### 3.1 Approved technical nouns

| Noun | Approved meaning |
|------|------------------|
| `ad account` | The billable account under which campaigns are run on one platform. |
| `ad creative` | One published combination of text, image, or video served as an advertisement. |
| `ad group` | A set of ad creatives and keywords that share a bid amount and a target audience. |
| `ad impression` | One counted event in which an ad creative was served. |
| `attribution model` | The stated rule that assigns credit for a conversion event to prior clicks or ad impressions. |
| `audience list` | A set of user identifiers uploaded to a platform for targeting or exclusion. |
| `bid amount` | The maximum amount offered for one click or for one thousand ad impressions. |
| `bid strategy` | The named automated rule that sets bids within an ad group or a campaign. |
| `budget cap` | The maximum spend permitted for a stated period, with a currency code. |
| `campaign` | The top-level container for ad groups, sharing a budget cap and a serving schedule. |
| `canonical tag` | The markup that declares the preferred URL for a set of duplicate pages. |
| `click` | One counted event in which a user selected an ad creative or a search result. |
| `conversion event` | One counted event that matches a named event definition on the advertiser's property. |
| `cost per click` | Total spend divided by clicks, for a stated period and a stated currency code. |
| `crawl budget` | The number of URLs a search engine crawler is observed to request from one origin per period. |
| `daily spend` | The amount spent in one calendar day, with a currency code and a time zone. |
| `destination URL` | The URL a user reaches after selecting an ad creative. |
| `disallow rule` | One line in a `robots.txt` file that requests that a crawler not request a matching path. |
| `indexed page` | A URL that a named search engine reports as present in its index on a stated date. |
| `keyword` | One targeting term, with a stated match type. |
| `landing page` | The page at a destination URL. |
| `match type` | The stated rule by which a keyword matches a search query. |
| `negative keyword` | A term that prevents an ad from serving against a matching search query. |
| `noindex directive` | The markup or header that requests that a search engine not index a URL. |
| `organic session` | A session that arrived from an unpaid search result, per a named measurement source. |
| `paid session` | A session that arrived from a paid click, per a named measurement source. |
| `placement` | The named site, application, or surface on which an ad creative is served. |
| `policy violation` | A platform's recorded finding that an ad creative or a property breaches its published policy. |
| `position` | The measured rank of a URL for one query, one locale, one device, and one date. |
| `publisher account` | The account under which a site owner receives revenue for ads served on their property. |
| `redirect rule` | A configured rule that directs requests from one URL to another, with a stated status code. |
| `remarketing tag` | The script that records a visit for later audience targeting. |
| `robots.txt file` | The file at the origin root that carries crawler directives. |
| `search query` | The text a user submitted to a search engine. |
| `serving state` | One of `serving`, `paused`, `removed`, `limited`, `under review`, `disapproved`. |
| `sitemap` | The file that lists URLs an origin offers for crawling. |
| `structured data markup` | The machine-readable annotation on a page that declares typed entities. |
| `target audience` | The stated set of users a campaign is configured to reach. |

### 3.2 Approved technical verbs

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `bid` | Set the maximum amount offered for one click or for one thousand ad impressions. | `bid` |
| `canonicalize` | Declare a preferred URL for a set of duplicate pages by setting a canonical tag. | `canonicalize` |
| `crawl` | Request URLs from an origin as an automated agent. | `crawl` |
| `deindex` | Cause a named search engine to remove a URL from its index. | `deindex` |
| `disallow` | Add a disallow rule to a `robots.txt` file. | `disallow` |
| `exclude` | Prevent an audience list or a placement from being served. | `exclude` |
| `index` | Cause a named search engine to add a URL to its index. | `index` |
| `publish` | Make content or an ad creative available to be served. This cannot be undone. | `publish` |
| `redirect` | Direct requests from one URL to another with a stated status code. | `redirect` |
| `resume` | Change a serving state from `paused` to `serving`. | `resume` |
| `restore` | Set a configuration value back to a stated prior value. This does not recover spend, publication, or indexation. | `restore` |
| `serve` | Deliver an ad creative in response to a request. | `serve` |
| `spend` | Consume budget against an ad account. This cannot be recovered. | `spend` |
| `submit` | Deliver a sitemap or a removal request to a named platform. | `submit` |
| `suspend` | Change a serving state to `paused` for a stated interval. | `suspend` |
| `target` | Configure a campaign or an ad group to reach a stated target audience. | `target` |
| `throttle` | Reduce a bid amount or a budget cap to a stated value to limit spend rate. | `throttle` |
| `upload` | Transfer an audience list or a data file to a named platform. | `upload` |
| `verify` | Compare a claim against an independent source and record the result. | `verify` |
| `split test` | Run an experiment that serves two variants and measures a stated outcome. | `split test` |

### 3.3 Forbidden terms

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *optimize*, *improve*, *boost* | Records a verdict about the agent's own work before an outcome exists (`STE-ADV-01`). | The parameter, the old value, and the new value |
| *revert*, *undo* | Implies that spend, publication, or indexation can be recovered (`STE-ADV-03`). | `restore`, plus a sentence on what is not restored |
| *impression* (bare) | A counted serve event, or an opinion. | `ad impression` |
| *traffic* (bare) | Merges sessions, users, clicks, and crawler hits. | `organic session` or `paid session`, with the source |
| *organic* (bare) | Unpaid search, or a food adjective, or "unforced". | `organic session` |
| *rank* (as a verb) | Asserts a change in position with no measurement qualifiers. | `position`, with query, locale, device, and date |
| *conversion* (bare) | Meaningless without an event definition and an attribution model. | `conversion event`, named |
| *test* (bare) | An experiment, or a verification (`STE-ADV-10`). | `split test` or `verify` |
| *pause* (bare) | Sounds temporary and free. Lost serving time is neither. | `serving state` with an approved value, plus the spend effect |
| *roll out* | An unstated scope and an unstated schedule. | `publish` with the count and the selection rule |
| *kill*, *nuke*, *tank* | Metaphor (`STE-C-12`) for an unstated destructive action. | The approved verb and the affected set |
| *tweak*, *minor change*, *quick fix* | Self-assessed consequence (core §3.2). | The `consequence` lattice value from `data.json:9` |
| *safe to deploy* | States a hope, not a property. | The measured property, or `undetermined` |
| *the site*, *the campaigns* | Unbounded scope (`STE-ADV-02`). | The count, the selection rule, and the platform |
| *best practice* | Cites an authority that is not named. | The named source and its date |
| *budget* (without a period) | A daily cap and a monthly cap differ by a factor of thirty (`STE-ADV-08`). | `budget cap` with currency code and period |

## 4. Decision-trace field templates

The templates use only approved terms.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <count> <object>.
The selection rule is <rule>.
The platform is <platform>. The property is <origin or ad account>.
The old value is <value>. The new value is <value>.
```

Filled:

```text
agent.seobot.v7 disallowed 1 path in the robots.txt file at https://example-retail.eu.
The selection rule is the literal path prefix /products/.
The platform is the example-retail.eu origin. The property is the production web origin.
The old value is no disallow rule for /products/. The new value is "Disallow: /products/".
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
<One sentence that states what a restore does not recover.>
Scope is <single|multi|org|public>. The effect reaches <named surfaces, counts, or audiences>.
Consequence is <none|low|material|high>. <One sentence that states the measured exposure.>
```

Filled:

```text
Reversibility is hard. Removing the disallow rule is immediate, but re-indexation depends on
the recrawl schedule of each search engine.
A restore does not recover the indexed pages, the positions held before deindexation, or the
organic sessions lost during the interval.
Scope is public. The effect reaches 48,210 indexed pages served to any requester.
Consequence is material. The 48,210 pages produced 1,284,000 organic sessions in the 30 days
to 2026-07-25, per the example-retail.eu analytics property.
```

The second sentence is mandatory in this profile.
It is where `STE-ADV-03` does its work, and it is the sentence a non-conforming record always
omits.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The rollback plan is: <step 1>. <step 2>. The named actor is <party>.
Recovery depends on <named third party>. The observed recovery interval is <interval>.
Recovery is not guaranteed.
```

Filled:

```text
agent.seobot.v7 disallowed the path prefix /products/ because the faceted-navigation
parameters under that prefix generated 2,100,000 crawled URLs against 48,210 canonical
product pages in the 7 days to 2026-07-25.
The measured residual error bound is 0.004 on the CT4 held-out adversarial crawl-directive
set, measured on 2026-06-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is above the tolerance.
The rollback plan is: the web platform team removes the disallow rule from the robots.txt
file. The team submits the product sitemap to each search engine. The named actor is the web
platform team.
Recovery depends on the recrawl schedule of each search engine. The observed recovery
interval for this origin is 21 to 60 days. Recovery is not guaranteed.
```

This filled example fails `LAAS-OBL-RES-001`: the measured bound of `0.004` is above the CT4
tolerance of `0.0` (`conformance/laas/data.json:15`).
It is shown failing on purpose.
The conforming outcome is not to soften the sentence — it is for the gate to block the
action and escalate.

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
VRF-ROBOTS-MATCH is a deterministic verifier.
The independence basis is different kind of checker.
VRF-ROBOTS-MATCH checked the proposed robots.txt file against the 48,210 canonical product
URLs and reported the count of URLs that the new disallow rule matches.
The verdict is fail.
The evidence is ev_robots_match_20260726.
```

A deterministic matcher is the right verifier class here.
The claim "this rule does not match the canonical product URLs" is exactly checkable, which
makes it a Bucket A claim and makes independence available at any tier
(`standard/LAAS.md:87`).
An agent asking a second language model whether a `robots.txt` change looks safe has not
obtained independence: two models of the same lineage fail the same way, and
`standard/LAAS.md:91` presumes them non-independent.

## 5. Mapping to LAAS obligations and tiers

### 5.1 Zero-Trust

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.

This domain's version of self-grading is not a false tier claim. It is vocabulary that
grades the outcome in advance.
*Optimize*, *improve*, and *boost* each assert a favourable result inside the verb.
A record that says "optimized the bid strategy across 340 ad groups" has recorded no
observable fact and one verdict, and the verdict is the agent's own.
`STE-ADV-01` removes the words. What remains is the parameter, the old value, and the new
value — three facts a verifier can check and an approver can dispute.

The second channel is the reversibility illusion described in §1.1.
Because the platform UI offers **Undo**, an agent can write a truthful sentence about the
configuration and a false impression about the consequence.
`STE-ADV-03` and the mandatory second sentence in §4.2 close it by requiring the record to
state what a restore does *not* recover.
That sentence is what keeps the prose from contradicting `gate_derived_ct`, which is exactly
the outcome `LAAS-OBL-SELF-001` protects for the structured field.

### 5.2 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5 without deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1` | Advisory |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

One domain note on volume.
This is the highest-volume domain of the three, and a blocking language check at CT3 will be
felt.
That pressure is the reason to keep CT2 at a warning: a check that fires constantly on
low-tier actions gets switched off, and a check that is switched off protects nothing.
The threshold is set where the record starts carrying an obligation that cannot be proven
without it.

A second note on aggregation.
Per §1.2, per-item changes aggregate.
Language conformance should be evaluated on the record for the **aggregate** action, not
separately on each of four thousand per-item records.
Evaluating per item is how a CT4 aggregate gets four thousand CT2 warnings and no block.

### 5.3 How language non-conformance should be treated

A language finding is a finding about the record, not about the action, and it enters the
same structure the policy already uses to separate `error_violations`
(`conformance/laas/laas.rego:199`) from `warning_violations`
(`conformance/laas/laas.rego:204`).

The checker must not rewrite the record (see [`ste-core.md`](ste-core.md) §5).
A rewrite is an append, not an edit (`LAAS-OBL-TRC-001`, `standard/LAAS.md:108-111`).

## 6. Worked example

**Action.** An SEO agent is asked to reduce crawl waste on a retail origin. Faceted
navigation under `/products/` has generated 2.1 million crawled URLs against 48,210
canonical product pages. The agent adds a disallow rule to `robots.txt`.

### 6.1 Non-conforming record

> Optimized the crawl budget by blocking the faceted URLs in robots.txt. This should improve
> indexation of the important pages and reduce server load. Organic traffic should benefit
> once Google recrawls. This is a minor config change and it's fully reversible — we can just
> revert the file if rankings drop.

The defects, and the rule each breaks:

| Text | Rule broken |
|------|-------------|
| "Optimized" | `STE-ADV-01` — a verdict about the agent's own work, before any outcome |
| No actor named | `STE-C-01` — unattributed actor |
| "the faceted URLs" | `STE-ADV-02` — no count, no selection rule; and this is where the error is |
| "should improve" | `STE-C-08`, `STE-C-10` — conditional, and no measurement |
| "the important pages" | `STE-ADV-02` — undefined set |
| "Organic traffic" | `STE-ADV-06` — sessions, users, or clicks? |
| "should benefit" | Core §3.2 — a hope |
| "once Google recrawls" | `STE-ADV-04` — third-party dependency stated as a certainty with no interval |
| "minor config change" | Forbidden — self-assessed consequence |
| "fully reversible" | `STE-ADV-03` — false. Deindexation recovery is external, slow, and not guaranteed |
| "just revert the file" | `STE-ADV-03` — restoring the file does not restore the index |
| "if rankings drop" | `STE-ADV-07` — no query, locale, device, or measurement date |

The load-bearing failure is "fully reversible".
The rule `Disallow: /products/` matches the faceted URLs **and** all 48,210 canonical product
pages, because they share the prefix.
The record asserts reversibility, so a reviewer tiers the action low, so no deterministic
matcher runs, so nobody counts what the rule matches.
The language defect and the technical defect are the same defect.

### 6.2 Conforming record

```text
ACTION
agent.seobot.v7 disallowed 1 path in the robots.txt file at https://example-retail.eu.
The selection rule is the literal path prefix /products/.
The platform is the example-retail.eu origin. The property is the production web origin.
The old value is no disallow rule for /products/. The new value is "Disallow: /products/".

EFFECT SURFACE
Reversibility is hard. Removing the disallow rule is immediate, but re-indexation depends on
the recrawl schedule of each search engine.
A restore does not recover the indexed pages, the positions held before deindexation, or the
organic sessions lost during the interval.
Scope is public. The effect reaches 48,210 indexed pages served to any requester.
Consequence is material. The 48,210 pages produced 1,284,000 organic sessions in the 30 days
to 2026-07-25, per the example-retail.eu analytics property.

RATIONALE AND RESIDUAL RISK
agent.seobot.v7 disallowed the path prefix /products/ because the faceted-navigation
parameters under that prefix generated 2,100,000 crawled URLs against 48,210 canonical
product pages in the 7 days to 2026-07-25.
The measured residual error bound is 0.004 on the CT4 held-out adversarial crawl-directive
set, measured on 2026-06-30.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is above the tolerance.
The rollback plan is: the web platform team removes the disallow rule from the robots.txt
file. The team submits the product sitemap to each search engine. The named actor is the web
platform team.
Recovery depends on the recrawl schedule of each search engine. The observed recovery
interval for this origin is 21 to 60 days. Recovery is not guaranteed.

VERIFIER FINDING
VRF-ROBOTS-MATCH is a deterministic verifier.
The independence basis is different kind of checker.
VRF-ROBOTS-MATCH checked the proposed robots.txt file against the 48,210 canonical product
URLs and reported the count of URLs that the new disallow rule matches.
The verdict is fail. The rule matches 48,210 of 48,210 canonical product URLs.
The evidence is ev_robots_match_20260726.
```

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42` the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `hard` ranks 3, `public` ranks 4, and `material`
ranks 3. The maximum is 4.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-ROBOTS-MATCH` runs before the file is deployed, not after. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic path matcher is a different *kind* of checker (`standard/LAAS.md:87`). A second language model reviewing the diff would be presumed non-independent (`standard/LAAS.md:91`). |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented claim-class coverage for path-prefix matching, a negative-test suite of known over-matching patterns it must catch, and a change-controlled version in the trace. |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0.0` (`data.json:15`). The measured `0.004` is above tolerance. |
| `LAAS-OBL-HUM-001` | A human approver approves before deployment, and `escalation_approved` is `true`. |
| `LAAS-OBL-AGG-001` | If this change is one of a sequence of crawl-directive edits in the window, the aggregate re-tiers the sequence (`standard/LAAS.md:59-60`). |

**Outcome: the action is blocked.**
Two obligations fail independently.
`LAAS-OBL-IRR-001` fails because the verifier verdict is `fail`.
`LAAS-OBL-RES-001` fails because `0.004` exceeds the CT4 tolerance of `0.0`.
The conformance predicate at `standard/LAAS.md:115-117` admits exactly one conforming path
for a failing verdict: the action is blocked and escalated.

**Language conformance: `LC-3`.**

The rewrite did not catch the over-matching rule — a deterministic matcher did.
What the rewrite did was make the tier honest.
In §6.1 the record says "fully reversible", which puts the action somewhere around CT1,
where no independent verifier is required and `VRF-ROBOTS-MATCH` never runs.
In §6.2 the record says `hard` and `public`, which puts it at CT4, where
`LAAS-OBL-IRR-001` makes the matcher mandatory.
The controlled language did not find the bug. It caused the control that finds the bug to be
invoked.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

Internet Engineering Task Force.
*RFC 9309: Robots Exclusion Protocol.*
Edited by Martijn Koster, Gary Illyes, Henner Zeller, and Lizzi Sassman.
Fremont, CA: IETF, 2022.

International Organization for Standardization.
*ISO 4217:2015, Codes for the representation of currencies.*
Geneva: ISO, 2015.

Interactive Advertising Bureau Technology Laboratory.
*Ad Verification Guidelines.*
New York: IAB Tech Lab, 2021.

Media Rating Council.
*Invalid Traffic Detection and Filtration Standards Addendum.*
New York: MRC, 2020.
