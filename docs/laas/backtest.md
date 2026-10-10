# Bucket-B Backtest Harness — Design

**Standard:** LLM-Agent Assurance Standard (LAAS) v1.1
**Component:** Bucket-B residual escape-rate measurement + tolerance validation
**Conformance bundle:** `laas-fin-2.0.0` (`conformance/laas/data.json`, `conformance/laas/laas.rego`)

- **Obligation served:** `LAAS-OBL-RES-001` — "Bounded residual escape rate (Bucket B)" (`ct_floor: 2`, severity `error`, reference `v1.1 §5`).
- **Spec anchors:** changelog item 1.2 (metric rename), §5 (two buckets + escape-rate metric), §7.2 (`LAAS-OBL-IRR-001` `residual_error` and `conformance_predicate`), §7.4 (decision-trace `evidence_refs`).
- **Section numbers:** every `§N` in this document refers to the design proposal [`docs/laas/proposal-v1.1.md`](proposal-v1.1.md), not to `standard/LAAS.md`. The normative escape-rate text is `standard/LAAS.md` §4.3 "Escape rate (normative)" (`standard/LAAS.md:98-114`).

---

## 1. What an "escape" is

Per §5 (`proposal-v1.1.md:144`): *"**Escape rate** is the governing metric: the rate at which a wrong output passes every applicable check and is committed."*

An **escape** is one backtested agent action for which **both** hold:

1. the verifier returned `verdict == "pass"` (the action was committed — not blocked, abstained, or flagged indeterminate); **and**
2. the ground-truth label is `wrong`.

A wrong action that the verifier **caught** (`fail` / `abstain` / `indeterminate`) is **not** an escape — the check did its job. A correct action that passed is not an escape. The escape rate is therefore the *residual undetected-error rate*: errors that survived every applicable check and were acted upon. (Changelog item 1.2: the metric formerly called "integrity" is now the **escape rate**; `integrity = 1 − escape_rate`, reported as the higher-is-better complement `integrity_metric`.)

This is the open-world (Bucket-B) metric: no exact oracle exists for the claim class, so the escape rate cannot be driven to ~0 by a sound deterministic verifier (that is Bucket A, §5). Instead it is **bounded, measured, and controlled**.

---

## 2. Measurement model

### Inputs

- A **labeled backtest set**: a held-out, representative, adversarially-stressed collection of agent actions, each carrying its Consequence Tier (CT), the verifier's verdict on that action, and a ground-truth outcome label (`correct` / `wrong`). §5 requires this set be held-out and adversarial. §7.5 requires the verifier to carry a negative-test suite (known-bad inputs the verifier must catch); the backtest set is intended to include those inputs.
- A **CT** to measure (the harness measures one claim class at one tier per run).
- The **conformance bundle** `conformance/laas/data.json`, the live source of `escape_rate_tolerance_by_ct`.

### Command line

`scripts/laas/backtest.py` takes these flags (`python3 scripts/laas/backtest.py --help`; argparse at `scripts/laas/backtest.py:591-604`):

| Flag | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--dataset` | yes | — | backtest dataset JSON |
| `--data-json` | yes | — | conformance bundle `data.json` (source of `escape_rate_tolerance_by_ct`) |
| `--ct` | yes | — | Consequence Tier to measure |
| `--confidence` | no | `0.95` | confidence level of the upper bound; must be finite with 0 < c < 1 and `1 - c < 1` in float (`c > 2**-54`), else exit 3 (`:608-615`) |
| `--interval` | no | `wilson` | interval method: `clopper-pearson` or `wilson` |
| `--out` | no | none | also write the evidence artifact JSON to this path |

The artifact is always printed to stdout; `--out` writes the same JSON to a file as well (`scripts/laas/backtest.py:651-659`). The file is written before stdout is printed. If the write fails, stdout stays empty, stderr gets `BACKTEST INPUT ERROR: --out: <reason>`, and the exit code is 3 (`:652-658`). For worked invocations, see [`backtest-demo.md`](backtest-demo.md).

### Estimator (binomial)

Each sample at the target CT is a Bernoulli trial — it either escaped or it did not. With `n` samples and `k` escapes:

- point estimate `p̂ = k / n`;
- a **one-sided upper confidence bound** at level `confidence` (default 0.95).

The upper bound — not the point estimate — is what we validate (see §3). Two pure-stdlib interval methods are provided:

| Method (`--interval`) | Use | Property |
| --- | --- | --- |
| **Wilson** (`wilson`, default) | general | well-behaved at small `k` including `k = 0`; no scipy |
| **Clopper–Pearson** (`clopper-pearson`) | conservative / audit | exact binomial via in-house regularized incomplete beta; usually ≥ Wilson, but not at every confidence level (at 0.99, `n = 20`, `k = 0`: Wilson 0.212967, Clopper–Pearson 0.205672) |

The method names map to functions at `scripts/laas/backtest.py:238-241`. On the demonstration fixture the two are close (CT3: Wilson 0.024987, Clopper–Pearson 0.025398); Clopper–Pearson is slightly more conservative there.

### Sample-size floor

A tolerance `t` is only *demonstrable* if the achievable upper bound at zero observed escapes can fall at or below `t`. The harness enforces a per-CT minimum (`min_samples_for_tolerance`, `scripts/laas/backtest.py:244-268`):

```text
n_min(t) = ceil( ln(1 − confidence) / ln(1 − t) )      (rule-of-three family)
```

At `t = 1` the formula would take `ln(0)`, so the function returns `n_min = 1`: with zero escapes the exact upper bound is at most 1 for any `n ≥ 1` (`scripts/laas/backtest.py:249-251`, `:261-262`). For `t = 0` it returns `None` (no finite `n` suffices; `:259-260`).

For a tiny `t` the function computes `ln(1 − t)` as `log1p(-t)`, because for `t` ≲ 5e-17 `1.0 − t` rounds to `1.0` and `log(1.0 − t)` is 0 (`:253-254`, `:264`). Below about 1e-308 the float quotient overflows, and the function redoes the division exactly on the two floats' rational values (`:255-256`, `:265-268`). Either way `n_min` is a finite, very large integer, so a valid tolerance down to `5e-324` no longer crashes the harness. A backtest smaller than that `n_min` is **INDETERMINATE** (`insufficient_sample_size`, exit 2), not an input error (`:257`, `:525-531`). The artifact's `min_samples_required` can therefore be an integer of about 324 digits. For small `t`, the naive `log(1 − t)` formula can give a noticeably larger `n_min` than `log1p`, because `1.0 − t` loses precision as `t` shrinks. For example, at confidence 0.9236 and `t` = 1.29e-14 the naive result is 199693690441779 and the `log1p` result is 199362215721678; the value `−ln(1 − c) / t` is about 199362215721679.2, so the `log1p` value is the more accurate one. The fixture floors below (149, 598) are unchanged.

Below `n_min` the result is **INDETERMINATE — insufficient sample size**, never PASS. Worked floors at 95% confidence: CT2 (t=0.02) → 149; CT3 (t=0.005) → 598.

### Re-measurement cadence

§5 requires re-measurement *"on any model/prompt/tool/policy change"* (`proposal-v1.1.md:142`), and §9 item 5 says *"re-backtest escape rate on any change (SR 11-7 ongoing monitoring)"* (`proposal-v1.1.md:339`). The evidence artifact pins `dataset_sha256`, `bundle_id`, and `measured_at` so a decision trace can prove the backtest is current for the bundle version it ran under; a stale artifact is detectable by hash/version mismatch. (Cadence ownership → Open Questions §6.)

---

## 3. Comparison to `escape_rate_tolerance_by_ct` and the pass/fail rule

**Tolerance source of truth.** `data.json.laas.escape_rate_tolerance_by_ct` — observed values (`conformance/laas/data.json:15`):

```json
{ "2": 0.02, "3": 0.005, "4": 0 }
```

Keys are **strings** and the map is **sparse** — CT0 and CT1 have no entry.

**Lookup convention (must match the policy).** `laas.rego` looks the tolerance up by string key (`conformance/laas/laas.rego:53-55`, verbatim except that the source's tab indent is shown as spaces):

```rego
residual_tolerance := t if {
    t := cfg.escape_rate_tolerance_by_ct[sprintf("%d", [effective_ct])]
}
```

The harness uses the identical convention: `key = str(int(ct))`, then `tol_map[key]` (`tolerance_for_ct`, `scripts/laas/backtest.py:361-377`). **If the CT has no entry, the harness raises `ToleranceLookupError` (exit 3) — it does not silently treat the absence as 0 or as pass.** A CT with no declared escape-rate tolerance carries no Bucket-B residual obligation; that is a caller decision, not a default. (The map declares no key for CT0, the read-only tier (`conformance/laas/laas.rego:33`), or for CT1, the lowest external-effect tier; the regime table first requires a bounded residual at CT2 (`standard/LAAS.md:55`).)

**Pass/fail rule — bound vs tolerance, not point vs tolerance.** §7.2's `conformance_predicate` reads (`proposal-v1.1.md:264`):

```text
… AND (residual_error_bound == null OR residual_error_bound <= residual_tolerance) …
```

and `laas.rego LAAS-OBL-RES-001` fires when a valid bound exceeds the tolerance, `_valid_bound > residual_tolerance` (`conformance/laas/laas.rego:185-194`, `:345`), except at a zero tolerance for a Bucket-A or human-gated action (`conformance/laas/laas.rego:318-356`), where a bound of exactly 0 on a non-blocked, non-Bucket-A action fires RES-001 instead (`:348-356`). It also fires when the record is `not blocked` and the effective tier has a numeric `residual_tolerance` (CT>=2) and either a numeric bound lacks non-empty `evidence_refs` (`:249-254`) or a non-Bucket-A action has no numeric bound (`:256-261`), or, at any CT, when the bound is not `null` and not a number >= 0 (`:286-301`). The policy compares the **bound**. So the harness:

- **PASS** iff `upper_ci_bound ≤ tolerance`
- **FAIL** iff `upper_ci_bound > tolerance`

and emits `residual_error_bound = upper_ci_bound` — the exact field, with the exact semantics, the policy consumes. Validating the *point estimate* would be unsound (it ignores sampling error and would pass underpowered sets); the spec's choice of the bound is deliberate and the harness honors it.

**`tolerance == 0` (CT4).** `measure()` routes a zero tolerance to **INDETERMINATE** before any bound comparison (`scripts/laas/backtest.py:516-524` precedes `:532`), so backtesting can **never** PASS a 0 tolerance. The disposition is `requires_deterministic_or_human_gate`, and the artifact still carries the achieved bound rounded to 6 places, so a small bound is stored as `0.0`; at confidence below 0.5, Wilson's cancellation can make the stored value `-0.0` (at `n = 598`, `k = 0`, confidence 0.3 the raw bound is about `-2.7e-20`) (`:501`). This is correct on both ends: it matches the tier regime — CT4 is the deterministic/human-gated tier (§6.3 adds human approval at CT4, `proposal-v1.1.md:182`; §7.3 permits model-lineage independence only up to CT3, `proposal-v1.1.md:277`), so Bucket-B sampling does not license a CT4 commit — and if anyone wired the artifact into a trace as if it passed, `LAAS-OBL-RES-001` would still fire for a trace that is neither Bucket A nor human-gated (`conformance/laas/laas.rego:185-194`, `:345`); for those two, the deterministic or human gate is the control (`standard/LAAS.md:108-114`).

| Condition | Verdict | Exit |
| --- | --- | --- |
| no samples at CT | `indeterminate` (`no_samples_for_ct`) | 2 |
| tolerance == 0 | `indeterminate` (`requires_deterministic_or_human_gate`) | 2 |
| `n < n_min` | `indeterminate` (`insufficient_sample_size`) | 2 |
| `upper_bound ≤ tolerance` | `pass` | 0 |
| `upper_bound > tolerance` | `fail` | 1 |
| CT not in tolerance map | error (`ToleranceLookupError`; JSON `{"error": "tolerance_lookup", ...}` on stderr) | 3 |

Exit codes: `scripts/laas/backtest.py:661` maps `pass`/`fail`/`indeterminate` to 0/1/2. Exit 3 comes from four paths:

- A missing `escape_rate_tolerance_by_ct` map or a missing CT key raises `ToleranceLookupError`. The harness prints the multi-line JSON `{"error": "tolerance_lookup", ...}` on stderr and returns 3 (`:644-649`).
- Malformed or unreadable input (dataset or `data.json`), or a malformed tolerance map or value, raises `BacktestInputError`. The harness prints one line `BACKTEST INPUT ERROR: <path>: <reason>` on stderr and returns 3 (`:640-643`).
- A failed `--out` write prints `BACKTEST INPUT ERROR: --out: <reason>` and returns 3 (`:652-658`).
- A command-line usage error exits 3 through `_ArgumentParser.error` (`:585-587`); see the usage-error item in the list below.

Exit 3 covers these input errors:

- JSON nested too deeply for the parser (`RecursionError`), or an integer literal over Python's 4300-digit limit, in `data.json` or the dataset; both count as invalid JSON (`_read_json`, `:289-305`).
- A `data.json` whose bundle is not a JSON object (`:311-315`), or whose tolerance map is not a JSON object (`:328-332`).
- A `laas.bundle_id` in `data.json` that is not a JSON string: `BACKTEST INPUT ERROR: <data.json path>: bundle_id must be a JSON string, got <type>` (`:621-626`).
- A tolerance that is not an int or float (not a bool), not finite, or outside 0 ≤ t ≤ 1 (`_tolerance_value`, `:341-358`). An oversized-integer tolerance is rejected too: the range check runs before `isfinite`, so no `OverflowError` escapes (`:345-346`, `:351-352`). `load_tolerance_map` (`:318-338`) checks every entry, not only the CT being measured. A bad value reads `BACKTEST INPUT ERROR: <data.json path>: escape_rate_tolerance_by_ct['<k>'] must be a finite number in [0, 1], got <v>`.
- A dataset row whose `ct` is infinite (`Infinity`, or `1e999`, which raises `OverflowError` in `int()`) (`:427-429`).
- `--confidence` that is not finite, not strictly between 0 and 1, or so small that `1 - c` rounds to `1.0` in float (`c <= 2**-54`). The harness prints one stderr line, `BACKTEST INPUT ERROR: --confidence: must be a finite number with 0 < c < 1 and 1 - c < 1 in float (c > 2**-54), got <v>`, and exits 3 (`:608-615`).
- Command-line usage errors: a bad value, unknown flag, missing required flag, bad choice, or ambiguous abbreviation. They print `BACKTEST INPUT ERROR: <arg>: <reason>` and exit 3 (`_ArgumentParser.error`, `:561-587`). Stock argparse would exit 2, which is the indeterminate verdict code, so the harness overrides it. `--help` still prints help and exits 0 (`:581-582`).

---

## 4. Evidence artifact (decision-trace consumable)

The harness emits one JSON **evidence artifact** per measurement (`schema: "laas.bucketB.backtest_evidence/v1"`, `scripts/laas/backtest.py:447`). It is the `backtest_report_ref` of the §7.2 `residual_error` block (`proposal-v1.1.md:222`) and is referenceable from a decision trace's §7.4 `evidence_refs` array.

### Trace-consumable contract

- `evidence_id` — content-addressed (`ev_backtest_<sha256[:16]>` over every field except `evidence_id` and `measured_at`, `scripts/laas/backtest.py:540-548`), stable, and **goes verbatim into the trace's `evidence_refs`** (mirrors §7.4's `["ev_ledger_diff_001"]` opaque-id convention). The policy checks only the array's shape: a non-empty `evidence_refs` array of non-empty strings (`conformance/laas/laas.rego:235-242`). The missing-evidence `LAAS-OBL-RES-001` rule fires when the tier has a numeric `residual_tolerance`, the action is not blocked, the bound is numeric (`conformance/laas/laas.rego:233`), and that shape check fails (`conformance/laas/laas.rego:249-254`); it does not check that the array contains this artifact ID, and blocked records are exempt from it (`not blocked`, `:251`). `LAAS-OBL-RES-001` also fires, independently of evidence shape, when a valid bound exceeds the tolerance (`conformance/laas/laas.rego:185-194`) or when a supplied non-null bound is not a number >= 0 (`conformance/laas/laas.rego:297-301`).
- `residual_error_bound` — the **upper CI bound**; the trace copies this into its own `residual_error_bound` field, which `laas.rego LAAS-OBL-RES-001` reads. At a zero tolerance the copied bound is not compared for a Bucket-A or human-gated action (`conformance/laas/laas.rego:331-346`).
- `residual_tolerance` — the value looked up from `data.json`, so the artifact is self-describing and the trace's `residual_tolerance` can be cross-checked against the bundle.
- Identification fields: `schema` (`laas.bucketB.backtest_evidence/v1`), `ct` (the measured tier), and `tolerance_source` (the `--data-json` path the tolerance was read from).
- Supporting fields for audit/re-inspection (§7.4 "tamper-evidently re-inspectable"): `n`, `committed_passes`, `escapes`, `escape_rate_point`, `confidence`, `interval_method`, `min_samples_required`, `integrity_metric`, `dataset_sha256`, `bundle_id`, `measured_at`, `verdict`, `disposition`, `notes`.

The fields are declared in the `EvidenceArtifact` dataclass (`scripts/laas/backtest.py:438-466`). Emitted key order, from a real CT2 run on the fixture: `schema evidence_id ct bundle_id tolerance_source n committed_passes escapes escape_rate_point residual_error_bound residual_tolerance confidence interval_method min_samples_required verdict disposition integrity_metric dataset_sha256 measured_at notes`.

**Verified end-to-end** (see [`backtest-demo.md`](backtest-demo.md)): feeding the CT3 artifact's `residual_error_bound` (0.024987) and `evidence_id` into a synthetic CT3 decision trace fires `LAAS-OBL-RES-001` against the real `laas.rego` with the message *"residual escape rate 0.024987 exceeds tolerance 0.005 for ct 3"* and `compliant: false`; the CT2 PASS bound (0.014286 ≤ 0.02) produces zero violations and `compliant: true`.

---

## 5. Components

| File | Role |
| --- | --- |
| `scripts/laas/backtest.py` | reference implementation: estimator, intervals, tolerance lookup, decision logic, evidence emission, CLI |
| `scripts/laas/fixtures/fixture_backtest.json` | synthetic held-out backtest set (CT2 PASS, CT3 FAIL, CT4 INDETERMINATE) |
| *(generated)* `evidence_ct{2,3,4}.json` | evidence artifacts emitted when you run the demo — produced by `backtest.py`, not committed |
| [`backtest-demo.md`](backtest-demo.md) | runnable demonstration + the opa cross-check |

---

## 6. Open questions

1. **Dataset provenance & labeling.** Who produces the ground-truth `wrong`/`correct` labels, and by what process? Human adjudication, a higher-authority oracle, or post-hoc incident review each carry different bias and latency. Labels must be independent of the verifier under test (§7.3 independence) — otherwise the backtest measures agreement, not escape. The adversarial-stress requirement (§5) needs an explicit threat-derivation method so "representative" is auditable, not asserted.
2. **Ownership of the backtest set.** §13 self-check (changelog 2.1) makes Bucket-B conformance *"gated on a backtest the operator must supply."* Who owns it — the deploying operator, an independent auditor (per the §10.1 "Governing metric" table's "mandatory independent audit of the eval set", `proposal-v1.1.md:359`), or a shared registry per claim class? Operator-owned sets invite teaching-to-the-test; the spec's independent-audit posture suggests the eval set itself needs qualification (a §7.5 DO-330 analogue applied to the dataset, not just the verifier).
3. **Drift / re-measurement cadence.** §5 and §9 item 5 mandate re-backtesting on *any* model/prompt/tool/policy change (`proposal-v1.1.md:142`, `:337`), but not *who triggers it* or *how staleness blocks commits*. Should the gate refuse to honor an evidence artifact whose `bundle_id`/`dataset_sha256` predates the current deployed configuration? A change-detection hook (config hash → required re-measure) closes the loop; absent it, a stale-but-passing artifact silently licenses commits under a changed system.
4. **Confidence level & interval choice as policy.** `confidence` (0.95) and the interval method are harness defaults, not bundle-declared. For parity with the tolerance being in `data.json`, both arguably belong in the bundle so the assurance level is itself change-controlled and not a per-run knob.
5. **Multi-class / correlated escapes.** The binomial model assumes independent trials. Correlated failure modes (one prompt-injection family causing a burst of escapes) violate that and would make the CI optimistic. `data.json.max_error_correlation` (0.2) governs verifier independence; an analogous bound on *intra-dataset* escape correlation may be needed.
