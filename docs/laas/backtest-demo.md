# Bucket-B Backtest Harness — Runnable Demonstration

Run from `scripts/laas/`. `DATA` is the **canonical** conformance bundle `data.json`;
`LAAS_DIR` holds the policy it is read against.

```bash
cd scripts/laas
DATA=../../conformance/laas/data.json
LAAS_DIR=../../conformance/laas
```

Tolerances read live from `data.json` → `escape_rate_tolerance_by_ct = { "2": 0.02, "3": 0.005, "4": 0 }`.

## Fixture

`fixtures/fixture_backtest.json` — 1240 synthetic samples (`laas.bucketB.backtest_dataset/v1`), claim class `agent.payment_action.fraud_screen`:

| CT | total | committed passes | escapes (pass + wrong) | designed verdict |
| --- | --- | --- | --- | --- |
| 2 | 420 | 400 | 2 | PASS |
| 3 | 615 | 600 | 9 | FAIL |
| 4 | 205 | 200 | 0 | INDETERMINATE (zero tolerance) |

## Run

```bash
python3 backtest.py --dataset fixtures/fixture_backtest.json --data-json "$DATA" --ct 2   # exit 0  PASS
python3 backtest.py --dataset fixtures/fixture_backtest.json --data-json "$DATA" --ct 3   # exit 1  FAIL
python3 backtest.py --dataset fixtures/fixture_backtest.json --data-json "$DATA" --ct 4   # exit 2  INDETERMINATE
python3 backtest.py --dataset fixtures/fixture_backtest.json --data-json "$DATA" --ct 0   # exit 3  ToleranceLookupError (CT0 undeclared)
python3 backtest.py --dataset fixtures/fixture_backtest.json --data-json "$DATA" --ct 3 --interval clopper-pearson # exact-interval cross-check
```

## Results

| CT | n | escapes | point | residual_error_bound (Wilson, upper 95%) | tolerance | verdict | exit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 420 | 2 | 0.004762 | **0.014286** | 0.02 | **pass** | 0 |
| 3 | 615 | 9 | 0.014634 | **0.024987** | 0.005 | **fail** | 1 |
| 4 | 205 | 0 | 0.000000 | 0.013026 | 0 | **indeterminate** (`requires_deterministic_or_human_gate`) | 2 |
| 0 | — | — | — | — | (none) | error: `ToleranceLookupError` | 3 |

Clopper–Pearson cross-check, CT3: bound 0.025398 (vs Wilson 0.024987) — exact interval is slightly more conservative, same `fail`.

## Policy cross-check (real `laas.rego`, opa 1.14.1)

The emitted `residual_error_bound` + `evidence_id` are dropped into a minimal CT3 decision-trace input (all other obligations satisfied) and evaluated against the real policy:

```bash
opa eval -d "$LAAS_DIR/laas.rego" -d "$DATA" -i "$TRACE_CT3" \
  'data.kellerai.laas.actions.violations' --format pretty
```

→ fires exactly:

```json
{ "obligation": "LAAS-OBL-RES-001", "severity": "error",
  "msg": "residual escape rate 0.024987 exceeds tolerance 0.005 for ct 3" }
```

and `summary.compliant == false`. The CT2 PASS bound (0.014286 ≤ 0.02) produces **zero** RES violations and `compliant: true`.

This proves the evidence artifact is consumable by the policy's `evidence_refs` / `residual_error_bound` mechanism, and the harness's PASS/FAIL agrees with the policy's `LAAS-OBL-RES-001` on both sides of the tolerance.
