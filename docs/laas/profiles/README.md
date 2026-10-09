# LAAS Controlled-Language Profiles

Industry controlled-language profiles for LAAS decision traces, adapted from the principles
of ASD-STE100 Simplified Technical English.

These profiles constrain the **free-text** parts of a decision record — the effect-surface
description, the rationale, the residual-risk statement, the verifier finding, and the
human-approval package — so that language becomes part of the assurance apparatus instead of
an unaudited channel inside it.

## Why

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.
The structured fields of a decision record already resist self-grading: the gate derives
`gate_derived_ct` from the observed effect surface, and `LAAS-OBL-SELF-001` stops a
self-reported tier from lowering it.

Prose is the channel that remains.
An agent that writes "this should be safe to roll back" has made a claim no verifier can
refute and every approver can misread.
`LAAS-OBL-IND-001` and `LAAS-OBL-HUM-001` both act on text the agent wrote.
Controlled language does not add an obligation — it removes the interpretive slack that lets
an existing obligation be satisfied in form and missed in fact.

## Contents

| File | What it is |
|------|------------|
| [`ste-core.md`](ste-core.md) | The shared rule base. Twelve core rules, the hedge ban list, the `LC-0`–`LC-3` conformance levels, the recommended gate policy, and the mapping to the twelve LAAS obligations. |
| [`banking.md`](banking.md) | Banking and financial services (`LAAS-STE-BANK-DRAFT-1.0`) |
| [`healthcare.md`](healthcare.md) | Healthcare, clinical and patient-related systems (`LAAS-STE-HLTH-DRAFT-1.0`) |
| [`seo-adsense.md`](seo-adsense.md) | SEO, AdSense and digital advertising (`LAAS-STE-ADV-DRAFT-1.0`) |
| [`real-estate.md`](real-estate.md) | Real estate (`LAAS-STE-RE-DRAFT-1.0`) |
| [`contracting.md`](contracting.md) | Building contracting, HVAC and solar (`LAAS-STE-CON-DRAFT-1.0`) |
| [`legal.md`](legal.md) | Legal and contracts (`LAAS-STE-LEGAL-DRAFT-1.0`) |
| [`insurance.md`](insurance.md) | Insurance (claims and policy administration) (`LAAS-STE-INS-DRAFT-1.0`) |
| [`software-docs.md`](software-docs.md) | Software and SaaS documentation (runbooks, API docs, incident comms) (`LAAS-STE-SWD-DRAFT-1.0`) |
| [`education.md`](education.md) | Education and academic (syllabi, assignment briefs, student-facing instructions) (`LAAS-STE-EDU-DRAFT-1.0`) |
| [`glossary/`](glossary/) | Machine-readable dictionaries derived from each profile's section 3 |

Read `ste-core.md` first. Each industry profile adopts it in full and adds only the rules,
vocabulary, and templates its domain needs.

## Status

These profiles are **informative**. They define no obligation, no Consequence Tier, and no
threshold.
Nothing here changes `standard/LAAS.md`, `conformance/laas/data.json`, or
`conformance/laas/laas.rego`.
No reference checker for `LC-2` ships with these profiles ([`ste-core.md`](ste-core.md) §4).

**Precedence.**
Where a profile and `standard/LAAS.md` conflict, the standard takes precedence.
Where a profile and `conformance/laas/data.json` conflict on a threshold value, `data.json`
is the machine source of truth.
Where an industry profile and `ste-core.md` conflict, the industry profile takes precedence
within its domain and must state the deviation explicitly.

Four profiles currently deviate from the core gate policy ([`ste-core.md`](ste-core.md) §5),
and all four deviate in the same direction — a class of defect that is blocking at **every**
tier, including CT0, because its harm is caused by the text itself and does not scale with
the Consequence Tier:

| Profile | Blocking at every tier | Deviation |
|---------|------------------------|-----------|
| [`healthcare.md`](healthcare.md) §5.2 | Dose and abbreviation notation | Also requires `LC-3` at CT3 rather than `LC-2` |
| [`real-estate.md`](real-estate.md) §5.2 | Occupant-description language | — |
| [`contracting.md`](contracting.md) §5.2 | Unit and quantity notation | — |
| [`software-docs.md`](software-docs.md) §5.2 | Identifier notation, version notation, and credential redaction (`STE-SWD-01`, `STE-SWD-02`, `STE-SWD-10`) | — |

A deviation from the core **rule base** is a separate matter and is not listed here.
[`legal.md`](legal.md) §2.1, for example, states two rule-base deviations and adopts the gate
policy without deviation (`docs/laas/profiles/legal.md:471-472`).

## Recommended gate policy

Defined in [`ste-core.md`](ste-core.md) §5 and adopted by all nine industry profiles, four of
them with the deviation in the table above.

| Effective CT | Required level | Gate response to language non-conformance |
|--------------|----------------|-------------------------------------------|
| CT0–CT1 | `LC-1` | Advisory |
| CT2 | `LC-2` | Warning — recorded in the trace, the action proceeds |
| CT3 | `LC-2` | Block — the record must be rewritten and re-checked |
| CT4 | `LC-3` | Block, upstream of the human approver |

Two constraints apply at every tier.
A checker reports findings and blocks; it never rewrites the record, because a checker that
repairs prose has authored a claim the actor did not make.
A rewrite is an **append**, not an edit — `LAAS-OBL-TRC-001` requires an append-only trace
(`standard/LAAS.md:108-111`), and the sequence of a hedged draft followed by a conforming
rewrite is itself an audit signal.

## Glossary file shape

Each file under [`glossary/`](glossary/) is derived from its profile's section 3 tables.
The markdown is authoritative; the JSON is derived, in the same relationship
`conformance/laas/data.json` holds to `standard/LAAS.md`.

```json
{
  "profile_id": "laas-ste-bank",
  "designation": "LAAS-STE-BANK-DRAFT-1.0",
  "version": "1.0.0",
  "domain": "Banking and financial services",
  "base": "docs/laas/profiles/ste-core.md",
  "source_document": "docs/laas/profiles/banking.md",
  "description": "...",
  "nouns":     [{ "term": "...", "meaning": "...", "enum": ["..."] }],
  "verbs":     [{ "term": "...", "meaning": "...", "part_of_speech": "verb", "imperative_form": "..." }],
  "forbidden": [{ "term": "...", "variants": ["..."], "class": "...", "reason": "...", "replacement": "..." }]
}
```

Field notes:

- `enum` appears only on a noun whose approved meaning is a closed value set.
- `variants` lists the other surface forms a forbidden entry covers. It is optional, and an
  entry can carry it as an empty array. `banking.json` omits it on every entry.
  `education.json`, `insurance.json`, and `legal.json` carry it only on entries with other
  surface forms, never empty. `contracting.json` carries it on every entry, always empty;
  the other four files carry it on every entry, sometimes empty.
- `class` groups forbidden entries where a profile treats two groups differently:
  `notation` and `vocabulary` in `healthcare.json`, `contracting.json`, and
  `software-docs.json`; `occupant-description` and `ambiguity` in `real-estate.json`.
  Entries in the `notation` and `occupant-description` classes are blocking at every tier,
  including CT0. `banking.json`, `seo-adsense.json`, `legal.json`, `insurance.json`, and
  `education.json` have a single group and omit the field.
- No term appears in both `nouns` and `verbs` in any profile. `STE-C-04` allows a term
  exactly one part of speech, so a domain concept with both forms gets two distinct surface
  forms — `post` and `posting date`, `bid` and `bid amount`.

There is no JSON Schema for these files, matching `conformance/laas/data.json`, which is
also a plain object validated by use rather than by schema.

## Adding a profile

A new profile registers in five places: the profile `.md` file, its `glossary/*.json` file,
the Contents table above, the Adopted profiles table in [`ste-core.md`](ste-core.md) §8, and
`CHANGELOG.md`.
A profile that introduces new load-bearing vocabulary also adds it to
`docs/agents/glossary.md` (step 6).
The Pages index needs no change: it links this README, not individual profiles
(`.github/workflows/pages.yml:48`), so a new profile reaches Pages through the Contents
table.

1. Create `docs/laas/profiles/<name>.md`, copying the section order from
   [`ste-core.md`](ste-core.md) §7. It is fixed so the profiles stay interchangeable.
2. Adopt `STE-C-01` through `STE-C-12` in full. Add domain rules with a `STE-<PREFIX>-NN` ID
   and a one-sentence justification tied to a named obligation.
3. Write section 3 as markdown tables first, then derive `glossary/<name>.json` from them.
4. State any deviation from the core gate policy explicitly, with its justification.
5. Add a row to the table in [`ste-core.md`](ste-core.md) §8 and to the Contents table above.
6. Add any new load-bearing vocabulary to `docs/agents/glossary.md` in the same pull request
   (`docs/agents/glossary.md:142`).
7. Record the profile in `CHANGELOG.md`.

## Changing an approved term

An approved term keeps one meaning for the life of a profile designation.
A record written under that meaning must keep it when the glossary changes
([`ste-core.md`](ste-core.md) §6, `LAAS-OBL-TRC-001`).
To change a meaning, add a new approved term.
Move the old term to the forbidden table, with the new term as its replacement.
Then bump the profile designation and the glossary `version`, and record the change in
`CHANGELOG.md`.

## Reference

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

These profiles adapt ASD-STE100 principles. They do not reproduce its rule text or its
controlled dictionary, and they are not endorsed by ASD. The domain dictionaries are original
work.
