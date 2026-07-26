# LAAS Controlled-Language Profile — Building Contracting, HVAC and Solar

**Designation:** LAAS-STE-CON-DRAFT-1.0
**Document type:** Industry controlled-language profile
**Source standard:** LLM-Agent Assurance Standard (LAAS) v1.1, `standard/LAAS.md`
**Machine source of truth:** `conformance/laas/data.json` (bundle `laas-fin-1.1.0`)
**Enforcing policy:** `conformance/laas/laas.rego`, package `kellerai.laas.actions`
**Base profile:** [`ste-core.md`](ste-core.md) (`LAAS-STE-CORE-DRAFT-1.0`)
**Derived glossary:** [`glossary/contracting.json`](glossary/contracting.json)
**Status:** Draft, not approved

> **Disclaimer:** This document is not an ASD publication and is not endorsed by the
> AeroSpace and Defence Industries Association of Europe.
> It adapts ASD-STE100 principles; it does not reproduce ASD rule text or the ASD
> controlled dictionary. The dictionary in section 3 is original work.
> This document is not an engineering standard, a code interpretation, or legal advice.
> Design, installation, and inspection are governed by the adopted code, the authority
> having jurisdiction, the equipment listing, and the responsible licensed party.

---

## 1. Domain purpose and risk context

### 1.1 Why controlled language matters here

The building trades are where ASD-STE100 came from, and the fit is almost exact.

ASD-STE100 was written because maintenance documentation for complex physical systems was
being read under time pressure by people who did not write it, in conditions where a
misreading damages equipment or kills someone. That is a field service call. It is a
rooftop unit at 40°C, a live service panel, a gas line, a roof edge.

Two properties make this domain distinctive.

**The vocabulary collides with itself more than in any other profile.**
*Panel* means an electrical panel, a photovoltaic module, a drywall sheet, or a control
panel — and on a solar retrofit, three of those four are on the same job on the same day.
*Load* means electrical load, structural load, cooling load, or heating load. *Service*
means the electrical supply to the building, a visit to the site, or the act of maintaining
equipment. *Charge* means the refrigerant mass in a system, the state of a battery, or the
amount billed to the customer. *Ground* is a noun, a verb, and a code term that must be
distinguished from *bond*.

These are not edge cases. They are the four or five most common words in the domain, and
each of them changes the meaning of a work instruction completely. An agent that writes
"panel is at capacity" has written a sentence that a solar designer, an electrician, and a
drywall estimator will each act on differently.

**Units carry silent factors of ten to a thousand.**
A kilowatt is not a kilowatt-hour: one is a rate, the other is an amount, and a solar
production estimate written in the wrong one is off by a factor of about 4,000 per year.
A ton is 12,000 BTU per hour of cooling capacity, not a weight. BTU is energy and BTU/h is
power. Natural gas manifold pressure is measured in inches of water column, and a figure
written in PSI is roughly 28 times larger — enough to convert a furnace into a hazard.

This is the same structural problem the healthcare profile addresses with its do-not-use
notation list, and it takes the same answer: the harm is caused by the notation itself and
does not scale with the size of the job, so the notation rules bind at every tier.

**A third property makes the paperwork as dangerous as the wiring.**
*Lien waiver* names four different instruments. A conditional waiver takes effect only when
payment clears; an unconditional one takes effect on signature whether or not it clears. A
partial waiver covers work through a date; a final waiver covers everything. Signing an
unconditional final waiver in exchange for a cheque that later bounces extinguishes the
right to recover, permanently, in a single signature. An agent that writes "signed the
waiver for the progress payment" has recorded none of the two axes that matter.

### 1.2 High-consequence agent actions

| Action | Reversibility | Scope | Consequence | Typical CT |
|--------|---------------|-------|-------------|------------|
| Sign an unconditional or final lien waiver | `irreversible` — the right is extinguished on signature | `org` | `high` | CT4 |
| Energize a service, a circuit, or a photovoltaic array | `reversible` in state, `irreversible` in exposure | `single` | `high` | CT4 |
| Certify that work is complete or code-compliant | `irreversible` — it starts warranty, retainage, and lien clocks | `org` | `high` | CT4 |
| Set a gas pressure, a refrigerant charge, or a torque value | `hard` | `single` | `high` | CT4 |
| Size equipment from a load calculation | `hard` — the error is found after installation | `single` | `material` to `high` | CT4 |
| Procure non-returnable or custom equipment | `irreversible` — no return right | `single` | `material` | CT4 |
| Submit a building permit application | `hard` — a withdrawal is on the record with the jurisdiction | `org` | `material` | CT3 |
| Approve a change order | `hard` — it amends the contract sum and the scope of work | `multi` | `material` | CT3 |
| Submit an interconnection agreement | `hard` | `org` | `material` | CT3 |
| Schedule an inspection | `reversible`, but a failed inspection is on the record | `single` | `low` to `material` | CT3 |
| Dispatch a crew to a site | `reversible`, but the travel cost is not | `single` | `low` | CT2 |
| Read a work order or an equipment schedule | `reversible` — read only | `single` | `none` | CT0 |

Three observations.

**Actions are gated, not projects.**
LAAS governs individual actions (`standard/LAAS.md:16-19`). A job is a long sequence of
separately tiered actions: sizing is CT4 on reversibility, procurement is CT4 on
reversibility, commissioning is CT4 on consequence, and dispatching a van is CT2. Tiering
"the job" as one thing is the mistake, and it always tiers down.

**Sequences aggregate.**
`LAAS-OBL-AGG-001` and `standard/LAAS.md:59-60` apply to a change-order sequence directly.
Eleven change orders at 4% each are not eleven CT3 actions; they are a 44% increase in the
contract sum, and the aggregate re-tiers the sequence.

**Safety-critical actions are `single` scope and still CT4.**
One occupied building is the smallest meaningful scope, and the `consequence` axis carries
it alone. This is the same shape as the healthcare profile, for the same reason: the harm is
to people, not to a portfolio.

## 2. Adapted STE writing rules

This profile adopts `STE-C-01` through `STE-C-12` from [`ste-core.md`](ste-core.md) in full.
The rules below are additional and specific to this domain.

| ID | Rule | Why it matters here |
|----|------|---------------------|
| `STE-CON-01` | State every physical quantity as a numeral, an approved unit symbol, and where a rate is possible, the time base. Write `48,000 BTU/h`, never `48,000 BTU`. | Energy and power are different quantities. See §3.3. |
| `STE-CON-02` | Never write the bare word *panel*. Write `electrical panel`, `photovoltaic module`, or the named assembly. | Three unrelated objects, often on one job. This is the domain's most frequent collision. |
| `STE-CON-03` | Never write the bare word *load*. Write `electrical load`, `structural load`, `cooling load`, or `heating load`. | Four quantities with four units and four calculation methods. |
| `STE-CON-04` | Never write the bare word *service*. Write `electrical service`, `service call`, or `maintain`. | The supply to the building, a visit, or an activity. |
| `STE-CON-05` | Never write the bare word *charge*. Write `refrigerant charge` with a mass, `battery state of charge` with a percentage, or `invoice` for billing. | A record that says "charge is low" does not say whether the customer or the system is the subject. |
| `STE-CON-06` | Distinguish `grounding` from `bonding` in every sentence that uses either. Never write the bare verb *ground*. | The adopted electrical code treats these as distinct requirements with distinct conductors. Conflating them is a defect an inspector will fail. |
| `STE-CON-07` | Write `terminate` only for making a conductor connection. Use `cancel` for ending a contract. | On a live job, "terminate the contract" and "terminate the conductor" are both plausible instructions. |
| `STE-CON-08` | State a lien waiver by both axes: `conditional` or `unconditional`, and `partial` or `final`. Never write the bare phrase *lien waiver*. | Four instruments, one name, and one of the four is unrecoverable. See §1.1. |
| `STE-CON-09` | Never write the bare word *complete* or *final*. Write `substantial completion`, `final inspection`, `final invoice`, or `final payment`, and name what the term triggers. | `substantial completion` is a contract term that starts retainage, warranty, and lien clocks. It is not a synonym for finished. |
| `STE-CON-10` | Never write *approved*, *up to code*, or the bare word *code*. Name the approving party, the approval date, the authority having jurisdiction, the adopted code edition and section, and the permit number. | *Approved* covers permit, inspection, engineer, and customer approval, and each fails independently. Code editions differ by jurisdiction and by year, so an unnamed edition is an unverifiable claim. |
| `STE-CON-11` | State a sizing result with the calculation method, the input assumptions, and the design conditions. Never state a capacity without its method. | `LAAS-OBL-VQ-001` requires claim-class coverage. A capacity with no stated method is a claim with no class. |
| `STE-CON-12` | State the isolation state before any energised work: the disconnect, the lockout identifier, and the verified absence of voltage. Never write "power is off". | This is the sentence that stands between a written instruction and an arc flash. It is verified by measurement, not by assertion. |

## 3. Approved technical nouns and technical verbs

The tables below are authoritative.
[`glossary/contracting.json`](glossary/contracting.json) is derived from them.

No term appears in both tables.
Where a domain concept has both a noun form and a verb form, the tables give them distinct
surface forms, because `STE-C-04` allows a term exactly one part of speech.
`charge` is the verb; `refrigerant charge` is the noun. `commission` is the verb;
`system commissioning` is the noun. `lock out` is the verb; `safety lockout` is the noun.

### 3.1 Approved technical nouns

| Noun | Approved meaning |
|------|------------------|
| `ampacity` | The current a conductor can carry continuously without exceeding its temperature rating, in amperes. |
| `authority having jurisdiction` | The named office that adopts the code, issues the permit, and performs the inspection. |
| `bonding conductor` | The conductor that connects metal parts together to establish electrical continuity. |
| `building permit` | The jurisdiction's written authorisation for stated work, identified by a permit number. |
| `change order` | A written amendment to the scope of work and the contract sum, signed by the parties. |
| `circuit` | The conductors and devices supplied by one overcurrent protective device. |
| `conductor` | One current-carrying wire, with a stated size, material, and insulation type. |
| `cooling load` | The rate at which heat must be removed from a space, in BTU/h, at stated design conditions. |
| `design temperature` | The outdoor temperature at which a load calculation is performed, with a location and a percentile. |
| `disconnect` | The device that isolates equipment from its supply, at a stated location. |
| `electrical load` | The current or power drawn by connected equipment, in amperes or watts. |
| `electrical panel` | The enclosure containing the overcurrent protective devices for a set of circuits. |
| `electrical service` | The conductors and equipment that deliver supply from the utility to the building. |
| `equipment schedule` | The document listing each specified item, its model number, and its rated performance. |
| `gas pressure` | The pressure of fuel gas at a stated point, in inches of water column or in kPa. |
| `grounding electrode` | The conductor or device that connects the system to earth. |
| `heating load` | The rate at which heat must be added to a space, in BTU/h, at stated design conditions. |
| `inspection result` | The jurisdiction's recorded outcome for one inspection, with a date and an inspector identifier. |
| `interconnection agreement` | The utility's written authorisation to connect a generating system to its network. |
| `inverter` | The device that converts direct current to alternating current, with a stated AC rating. |
| `lien waiver` | An instrument that gives up lien rights, stated as conditional or unconditional and partial or final. |
| `load calculation` | The documented computation of a heating load or a cooling load by a named method. |
| `nameplate rating` | The manufacturer's stated performance or electrical rating, as marked on the equipment. |
| `photovoltaic module` | One panel that converts light to direct current, with a stated DC rating in watts. |
| `photovoltaic string` | A set of photovoltaic modules connected in series to one input. |
| `production estimate` | The predicted energy a generating system will deliver over a stated period, in kWh. |
| `purchase order` | The document that commits the contractor to buy stated items from a named supplier. |
| `rated cooling capacity` | The cooling output of equipment at stated test conditions, in BTU/h. |
| `refrigerant charge` | The mass of refrigerant in a system, in kilograms or pounds, for a stated line length. |
| `retainage` | The portion of the contract sum withheld until stated completion conditions are met. |
| `rough-in inspection` | The inspection performed before concealed work is covered. |
| `safety lockout` | The applied device and tag that hold a disconnect open, with a named holder. |
| `scope of work` | The written statement of the work the contract requires. |
| `static pressure` | The resistance to airflow in a duct system, in inches of water column or in pascals. |
| `subcontractor` | A party engaged by the contractor to perform part of the scope of work. |
| `substantial completion` | The contract-defined point at which the work can be used for its intended purpose. It starts retainage, warranty, and lien periods. |
| `system commissioning` | The documented sequence of tests that places a system into service. |
| `voltage drop` | The reduction in voltage along a conductor under load, as a percentage of nominal voltage. |
| `warranty term` | The stated period and coverage of a warranty, with its start event. |
| `work order` | The record that authorises a stated task at a stated site. |

### 3.2 Approved technical verbs

| Verb | Approved meaning | Imperative form |
|------|------------------|-----------------|
| `certify` | Attest in writing that stated work meets a named standard or code section. | `certify` |
| `charge` | Add refrigerant to a system to a stated mass. | `charge` |
| `commission` | Place a system into service after a documented test sequence. | `commission` |
| `deenergize` | Remove supply from equipment and verify the absence of voltage by measurement. | `deenergize` |
| `energize` | Apply supply to equipment. | `energize` |
| `inspect` | Examine work against a named code section and record the result. | `inspect` |
| `install` | Place and connect equipment according to a named instruction or listing. | `install` |
| `invoice` | Bill a customer for a stated amount against a stated scope of work. | `invoice` |
| `lock out` | Apply a device and a tag that hold a disconnect open, with a named holder. | `lock out` |
| `pressure test` | Apply a stated pressure for a stated duration and record the result. | `pressure test` |
| `procure` | Issue a purchase order for stated items from a named supplier. | `procure` |
| `purge` | Displace air or gas from a system with a stated medium. | `purge` |
| `schedule` | Set a planned date and time for a task, an inspection, or a delivery. | `schedule` |
| `size` | Determine a required capacity or conductor by a named calculation method. | `size` |
| `subcontract` | Engage a subcontractor to perform a stated part of the scope of work. | `subcontract` |
| `submit` | Deliver a document to a named authority, utility, or party. | `submit` |
| `terminate` | Make a conductor connection at a stated point. This is not a contract action. | `terminate` |
| `torque` | Tighten a fastener to a stated value with a calibrated tool. | `torque` |
| `verify` | Compare a claim against an independent source or a measurement and record the result. | `verify` |
| `waive` | Give up a stated right by a written instrument. The right does not return. | `waive` |
| `withhold` | Retain retainage or a payment against a stated, itemised condition. | `withhold` |

### 3.3 Forbidden terms and notations

The first block is notation.
Every entry carries a silent factor between ten and several thousand.
These are forbidden without exception, at **every** tier, including CT0, because the harm is
caused by the notation itself and does not scale with the Consequence Tier.

| Forbidden notation | Why | Write instead |
|--------------------|-----|---------------|
| `BTU` for a rate | Energy, not power. A capacity is a rate. | `BTU/h` |
| `ton` (bare) | 12,000 BTU/h of cooling capacity, or a weight. | `rated cooling capacity` in BTU/h |
| `kW` and `kWh` interchanged | Power and energy. A yearly production estimate differs from system size by a factor of about 4,000. | `kW` for size, `kWh` for production, with the period |
| `kW` for a photovoltaic array without DC or AC | DC module rating and AC inverter rating differ by 10% to 30%. | `kW-DC` or `kW-AC` |
| `PSI` for fuel-gas manifold pressure | Manifold pressure is inches of water column. PSI is about 28 times larger. | `inches of water column`, or `kPa` |
| `amps` without voltage and phase | Current alone does not state power or conductor size. | The current, the voltage, and the phase |
| `3 phase` without a voltage | 208 V, 240 V, 480 V, and 600 V are all three-phase and are not interchangeable. | The voltage and the phase together |
| `gauge` (bare) | Wire gauge, sheet-metal gauge, or a pressure gauge. Wire and sheet gauges run opposite to size. | `AWG`, `sheet gauge`, or `pressure gauge` |
| Degrees without a scale | 20 °C and 20 °F are 47 degrees apart. | The numeral and `°C` or `°F` |
| `micron` and `inHg` interchanged | Two vacuum scales that run in opposite directions. | The numeral and the named scale |
| `CFM` and `FPM` interchanged | Volume flow and velocity. | The numeral and the named unit |

The second block is vocabulary.

| Forbidden | Why it is dangerous | Write instead |
|-----------|--------------------|---------------|
| *panel* (bare) | Electrical panel, photovoltaic module, drywall sheet, or control panel. | The named object (`STE-CON-02`) |
| *load* (bare) | Electrical, structural, cooling, or heating. | The named load (`STE-CON-03`) |
| *service* (bare) | The electrical supply, a site visit, or maintenance. | The named sense (`STE-CON-04`) |
| *charge* (bare) | Refrigerant mass, battery state, or a billed amount. | The named sense (`STE-CON-05`) |
| *ground* (bare verb) | Grounding and bonding are distinct code requirements. | `grounding electrode` or `bonding conductor` |
| *string* (bare) | A photovoltaic string, or an ordinary noun. | `photovoltaic string` |
| *return* (bare) | Return air, or returning a part to a supplier. | `return air duct`, or `return to the supplier` |
| *drop* (bare) | Voltage drop, a dropped ceiling, or a service drop. | `voltage drop`, or the named assembly |
| *final* (bare) | Final inspection, final invoice, or final payment. | The named event (`STE-CON-09`) |
| *complete* (bare) | `substantial completion` is a contract term with clocks attached. | `substantial completion`, or the finished task |
| *approved* (bare) | Permit, inspection, engineer, or customer approval. | The approving party and the date (`STE-CON-10`) |
| *code* (bare) | Building code, error code, or a code section. | The adopted code, its edition, and the section |
| *up to code* | A conclusion with no citation. | The code section and the inspection result |
| *terminate* (for contracts) | On a live job this reads as a conductor instruction (`STE-CON-07`). | `cancel` |
| *lien waiver* (bare) | Four instruments with one name (`STE-CON-08`). | `conditional partial`, `unconditional final`, and so on |
| *power is off* | An assertion, not a measurement. | The disconnect, the lockout identifier, and the verified absence of voltage |
| *tie in* | An unstated connection of unstated systems. | `terminate` or `install`, with the named points |
| *clear* (bare) | Clearance distance, or cleared to proceed. | The measured clearance, or the named approval |
| *order* (bare) | A purchase order, a work order, or a change order. | The named document, or the verb `procure` |
| *should be fine* | States a hope, not a property (core §3.2). | The measured value against the stated requirement |

## 4. Decision-trace field templates

The templates use only approved terms.
The effect-surface template uses the exact enum values from
`conformance/laas/data.json:7-9`.

### 4.1 Action description

```text
<actor_id> <approved verb> <object> for work order <id> at <site identifier>.
The permit number is <number>. The authority having jurisdiction is <named office>.
The equipment is <manufacturer and model number>. The rating is <numeral and unit>.
The calculation method is <named method>.
```

Filled:

```text
agent.fieldbot.v5 procured 1 equipment set for work order WO-2026-4417 at 218 Kestrel Lane,
parcel APN-112-806-004.
The permit number is MECH-2026-08812. The authority having jurisdiction is the Clearwater
County Building Department.
The equipment is a Harrowgate FG-96-060 condensing furnace and a Harrowgate AC-42 condenser
with a custom-width evaporator coil.
The rating is 60,000 BTU/h input heating and 42,000 BTU/h rated cooling capacity.
The calculation method is ACCA Manual J, eighth edition, whole-house.
```

### 4.2 Effect-surface summary

```text
Reversibility is <reversible|hard|irreversible|none>. <One sentence that states why.>
<One sentence that states what a cancellation does not recover.>
Scope is <single|multi|org|public>. The effect reaches <named site, systems, or parties>.
Consequence is <none|low|material|high>. <One sentence that states the stated exposure.>
```

Filled:

```text
Reversibility is irreversible. The evaporator coil is a custom width and the supplier states
it is non-returnable once the purchase order is released.
A cancellation stops the delivery. It does not recover the coil cost of USD 1,180.00 or the
25% restocking fee on the condenser.
Scope is single. The effect reaches work order WO-2026-4417 and the occupants of 218 Kestrel
Lane.
Consequence is material. The committed equipment cost is USD 7,940.00 against a contract sum
of USD 14,300.00.
```

The second sentence is mandatory in this profile whenever the action commits money or
material. It is the sentence a non-conforming record always omits.

### 4.3 Rationale and residual-risk statement

```text
<actor_id> <verb>ed the action because <one reason, one sentence>.
The calculation method is <named method>. The design conditions are <values with units>.
The computed result is <numeral and unit>. The selected rating is <numeral and unit>.
The measured residual error bound is <number> on <named evaluation set>, measured on <date>.
The tolerance for CT<n> is <number> from conformance/laas/data.json.
The residual bound is <at or below|above> the tolerance.
The rollback plan is: <step 1>. <step 2>. The named actor is <party>. The time bound is <duration>.
```

Filled:

```text
agent.fieldbot.v5 procured the equipment because the existing furnace failed a heat-exchanger
inspection on 2026-07-21 and the customer accepted change order CO-2026-4417-02.
The calculation method is ACCA Manual J, eighth edition, whole-house.
The design conditions are 99% winter design temperature -12 °C and 1% summer design
temperature 33 °C for Clearwater County.
The computed result is 51,400 BTU/h heating load and 38,900 BTU/h cooling load.
The selected rating is 60,000 BTU/h input heating and 42,000 BTU/h rated cooling capacity.
The electrical load added is 24.6 A at 240 V single phase. The existing electrical panel is
rated 200 A with 62 A of calculated load. The added load is within the panel rating.
The measured residual error bound is 0.003 on the CT4 held-out adversarial sizing set,
measured on 2026-06-18.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is above the tolerance.
The rollback plan is: the purchasing coordinator cancels purchase order PO-2026-9931 with the
supplier. The coordinator confirms the restocking terms in writing. The named actor is the
purchasing coordinator. The time bound is 4 hours from release.
Recovery does not include the custom evaporator coil.
```

This filled example fails `LAAS-OBL-RES-001`: the measured bound of `0.003` is above the CT4
tolerance of `0.0` (`conformance/laas/data.json:15`).
It is shown failing on purpose. The conforming outcome is not to soften the sentence — it is
for the gate to block the action and escalate.

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
VRF-MANUAL-J is a deterministic verifier.
The independence basis is different kind of checker.
VRF-MANUAL-J recomputed the heating load and the cooling load from the recorded building
inputs and design conditions, and compared the selected rating against the ACCA Manual S
selection bands.
The verdict is fail. The selected rated cooling capacity of 42,000 BTU/h is 108% of the
computed cooling load, which is above the 115% band ceiling only for variable-capacity
equipment; the selected unit is single-stage, for which the band ceiling is 100%.
The evidence is ev_manual_j_4417.
```

A deterministic recomputation is the correct verifier class for a sizing claim, and it is
available at any tier because it is a different *kind* of checker (`standard/LAAS.md:87`).
Asking a second language model whether the tonnage "looks about right" is not independence:
`standard/LAAS.md:91` presumes a shared-lineage verifier non-independent, and rule-of-thumb
sizing is precisely the heuristic both models learned.

## 5. Mapping to LAAS obligations and tiers

### 5.1 Zero-Trust

`standard/LAAS.md:33` forbids any control that lets the constrained party tier, grade, or
gate itself.

The domain's characteristic self-grading is the **unstated method**.
"Ran the load and went with a 4 ton unit" contains a number and no way to check it. There is
no method, no design condition, no input set, and therefore no claim a verifier can
recompute. The agent has reported a conclusion and withheld everything needed to contest it.

`STE-CON-11` is the fix, and it is the single rule with the most leverage in this profile.
Requiring the method, the inputs, and the design conditions converts an opinion into a
Bucket A claim — one that a deterministic checker can recompute exactly. That is what makes
`LAAS-OBL-IND-001` satisfiable here at all, because the deterministic class is independent at
any tier (`standard/LAAS.md:87`).

`LAAS-OBL-VQ-001` depends on the same rule. Verifier qualification requires documented
coverage of a **claim class** (`standard/LAAS.md:95-96`). "The unit is the right size" has no
class. "The heating load is 51,400 BTU/h by ACCA Manual J at -12 °C outdoor design" belongs
to a class a verifier can be qualified against, with a negative-test suite of known bad
sizings.

The unit rules serve the same end from the other direction. A capacity written as
`48,000 BTU` cannot be compared to a load written in `BTU/h`, so the comparison silently does
not happen.

### 5.2 When conformance is required

This profile adopts the gate policy at [`ste-core.md`](ste-core.md) §5, with one stated
deviation.

| Effective CT | Required level | Gate response |
|--------------|----------------|---------------|
| CT0–CT1 | `LC-1`, and the §3.3 notation block at every tier | Advisory, except notation |
| CT2 | `LC-2` | Warning |
| CT3 | `LC-2`, verifier report included | Block |
| CT4 | `LC-3` | Block, upstream of the human approver |

**Deviation — notation is blocking at every tier.**
The §3.3 first block is not a style preference. A gas pressure written in the wrong unit is
off by a factor of 28 whether the work order is CT0 or CT4.
This mirrors the healthcare profile's treatment of dose notation
([`healthcare.md`](healthcare.md) §5.2), and the real-estate profile's treatment of
occupant description ([`real-estate.md`](real-estate.md) §5.2), for the same structural
reason: some defects are caused by the notation rather than by the size of the action.

The deviation is more restrictive than the core profile. It changes no LAAS obligation, no
tier, and no threshold.

### 5.3 How language non-conformance should be treated

A language finding is a finding about the record, not about the action, and it enters the
same structure the policy already uses to separate `error_violations`
(`conformance/laas/laas.rego:199`) from `warning_violations`
(`conformance/laas/laas.rego:204`).

The checker must not rewrite the record (see [`ste-core.md`](ste-core.md) §5).
This matters acutely for units. A checker that "corrects" `48,000 BTU` to `48,000 BTU/h` has
guessed. If the agent actually meant a daily energy figure, the correction has manufactured a
capacity claim nobody made and the record now reads as verified. Reject and require the actor
to restate.

A rewrite is an append, not an edit (`LAAS-OBL-TRC-001`, `standard/LAAS.md:108-111`).
Both records stay in the chain. A pattern of unit defects from one actor is a fact about that
actor and about every job it has touched.

## 6. Worked example

**Action.** A field-service agent is asked to specify and order replacement heating and
cooling equipment after a failed heat-exchanger inspection, and to draft the change order.

### 6.1 Non-conforming record

> Ran the numbers on the house, existing unit is undersized. Going with a 4 ton unit and a
> 60,000 BTU furnace. Panel has capacity so we should be fine on the load. Gas pressure will
> be set to 3.5 PSI at the manifold per the nameplate. Ordered the equipment. Change order
> approved by the customer and we're up to code. Can cancel if anything changes.

The defects, and the rule each breaks:

| Text | Rule broken |
|------|-------------|
| "Ran the numbers" with no actor | `STE-C-01`, `STE-CON-11` — no actor, no method |
| "undersized" | `STE-C-10` — a conclusion with no measurement |
| "4 ton" | §3.3 — capacity or weight, and no BTU/h |
| "60,000 BTU" | §3.3, `STE-CON-01` — energy where a rate is meant |
| "Panel has capacity" | `STE-CON-02` — electrical panel or photovoltaic module? And no ampacity |
| "the load" | `STE-CON-03` — electrical, cooling, or heating? |
| "we should be fine" | Forbidden — states a hope |
| "3.5 PSI at the manifold" | §3.3 — **manifold pressure is inches of water column** |
| "Ordered" | `STE-CON-10`, forbidden *order* — and the irreversibility is unstated |
| "approved by the customer" | `STE-CON-10` — no date, no change-order number |
| "up to code" | `STE-CON-10` — no code edition, no section, no jurisdiction |
| "Can cancel if anything changes" | §4.2 — false. The custom coil is non-returnable |

Two defects here are live hazards rather than documentation faults.

`3.5 PSI` at the manifold is about 97 inches of water column. A residential furnace manifold
runs at roughly 3.5 **inches of water column**. The number is right and the unit is wrong by
a factor of about 28, and the sentence reads perfectly fluently. This is the contractor's
version of the trailing-zero problem in [`healthcare.md`](healthcare.md) §6.1: the notation
carries the error, not the reasoning.

"4 ton" with "should be fine on the load" is the self-grading failure. There is no method, no
design condition, and no computed load, so no verifier can contest the selection. As it
happens the selection is wrong — see §6.2.

### 6.2 Conforming record

```text
ACTION
agent.fieldbot.v5 procured 1 equipment set for work order WO-2026-4417 at 218 Kestrel Lane,
parcel APN-112-806-004.
The permit number is MECH-2026-08812. The authority having jurisdiction is the Clearwater
County Building Department.
The equipment is a Harrowgate FG-96-060 condensing furnace and a Harrowgate AC-42 condenser
with a custom-width evaporator coil.
The rating is 60,000 BTU/h input heating and 42,000 BTU/h rated cooling capacity.
The calculation method is ACCA Manual J, eighth edition, whole-house.

EFFECT SURFACE
Reversibility is irreversible. The evaporator coil is a custom width and the supplier states
it is non-returnable once the purchase order is released.
A cancellation stops the delivery. It does not recover the coil cost of USD 1,180.00 or the
25% restocking fee on the condenser.
Scope is single. The effect reaches work order WO-2026-4417 and the occupants of 218 Kestrel
Lane.
Consequence is material. The committed equipment cost is USD 7,940.00 against a contract sum
of USD 14,300.00.

RATIONALE AND RESIDUAL RISK
agent.fieldbot.v5 procured the equipment because the existing furnace failed a heat-exchanger
inspection on 2026-07-21 and the customer accepted change order CO-2026-4417-02 on
2026-07-24.
The calculation method is ACCA Manual J, eighth edition, whole-house.
The design conditions are 99% winter design temperature -12 °C and 1% summer design
temperature 33 °C for Clearwater County.
The computed result is 51,400 BTU/h heating load and 38,900 BTU/h cooling load.
The selected rating is 60,000 BTU/h input heating and 42,000 BTU/h rated cooling capacity.
The electrical load added is 24.6 A at 240 V single phase. The existing electrical panel is
rated 200 A with 62 A of calculated load. The added load is within the panel rating.
The manifold gas pressure specified on the nameplate is 3.5 inches of water column for
natural gas.
The adopted code is the 2021 International Mechanical Code as amended by Clearwater County
ordinance 2023-14.
The measured residual error bound is 0.003 on the CT4 held-out adversarial sizing set,
measured on 2026-06-18.
The tolerance for CT4 is 0.0 from conformance/laas/data.json.
The residual bound is above the tolerance.
The rollback plan is: the purchasing coordinator cancels purchase order PO-2026-9931 with the
supplier. The coordinator confirms the restocking terms in writing. The named actor is the
purchasing coordinator. The time bound is 4 hours from release.
Recovery does not include the custom evaporator coil.

VERIFIER FINDING
VRF-MANUAL-J is a deterministic verifier.
The independence basis is different kind of checker.
VRF-MANUAL-J recomputed the heating load and the cooling load from the recorded building
inputs and design conditions, and compared the selected rating against the ACCA Manual S
selection bands.
The verdict is fail. The selected rated cooling capacity of 42,000 BTU/h is 108% of the
computed cooling load of 38,900 BTU/h. The selected condenser is single-stage, for which the
band ceiling is 100%.
The evidence is ev_manual_j_4417.
```

### 6.3 Tier and required checks

**Consequence Tier: CT4.**
By `standard/LAAS.md:42` the tier is the maximum across the three axes.
Using `conformance/laas/data.json:7-9`: `irreversible` ranks 4, `single` ranks 1, and
`material` ranks 3. The maximum is 4.

The tier is carried by reversibility alone, as in [`banking.md`](banking.md), but by a
different mechanism: not settlement finality, a supplier's return policy on a custom part.
Note also that scope is `single` — one house — and the action is still CT4. Job size is not
the tier.

Required independent checks at CT4:

| Obligation | What it requires here |
|------------|----------------------|
| `LAAS-OBL-IRR-001` | Independent pre-commit verification. `VRF-MANUAL-J` runs before the purchase order is released. After release the coil is unrecoverable. |
| `LAAS-OBL-IND-001` | The verifier is independent. Basis: a deterministic recomputation is a different *kind* of checker (`standard/LAAS.md:87`). A second language model estimating tonnage would be presumed non-independent (`standard/LAAS.md:91`). |
| `LAAS-OBL-VQ-001` | The verifier is qualified: documented claim-class coverage for Manual J load computation and Manual S selection, a negative-test suite of known oversizing errors it must catch, and a change-controlled version in the trace. |
| `LAAS-OBL-RES-001` | Measured residual bound at or below `escape_rate_tolerance_by_ct["4"]`, which is `0.0` (`data.json:15`). The measured `0.003` is above tolerance. |
| `LAAS-OBL-HUM-001` | The responsible licensed mechanical contractor approves before release, and `escalation_approved` is `true`. |
| `LAAS-OBL-VEN-001` | The supplier's non-return terms are a vendor scope limit. The record names the supplier and states the terms rather than writing "may not be returnable". |

**Outcome: the action is blocked.**
Two obligations fail independently.
`LAAS-OBL-IRR-001` fails because the verifier verdict is `fail`.
`LAAS-OBL-RES-001` fails because `0.003` exceeds the CT4 tolerance of `0.0`.
The conformance predicate at `standard/LAAS.md:115-117` admits exactly one conforming path
for a failing verdict: the action is blocked and escalated.

**Language conformance: `LC-3`**, with the §3.3 notation block applying unconditionally.

Both defects are caught, and by different mechanisms.
The gas-pressure unit error is caught by the notation block, at every tier, without any
verifier running — a term matcher knows manifold pressure is not measured in PSI.
The oversizing is caught by `VRF-MANUAL-J`, which could only run because `STE-CON-11` forced
the record to state a method, an input set, and design conditions.

In §6.1 neither is findable. "3.5 PSI at the manifold" reads as a specification, and
"4 ton, should be fine on the load" offers a verifier nothing to check.

## Annex A (informative): Bibliography

AeroSpace and Defence Industries Association of Europe.
*ASD-STE100: Simplified Technical English, Specification for the preparation of technical
documentation in a controlled language.*
Issue 8. Brussels: ASD, 2021.

Air Conditioning Contractors of America.
*ANSI/ACCA Manual J: Residential Load Calculation.*
8th edition. Arlington, VA: ACCA, 2016.

Air Conditioning Contractors of America.
*ANSI/ACCA Manual S: Residential Equipment Selection.*
2nd edition. Arlington, VA: ACCA, 2014.

International Code Council.
*2021 International Mechanical Code.*
Washington, DC: ICC, 2020.

National Fire Protection Association.
*NFPA 70: National Electrical Code.*
Quincy, MA: NFPA, 2023.

National Fire Protection Association.
*NFPA 70E: Standard for Electrical Safety in the Workplace.*
Quincy, MA: NFPA, 2024.

Occupational Safety and Health Administration.
*Control of Hazardous Energy (Lockout/Tagout).*
29 C.F.R. § 1910.147. Washington, DC: OSHA.
