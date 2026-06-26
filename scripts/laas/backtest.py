#!/usr/bin/env python3
"""
LAAS v1.1 — Bucket-B backtest harness (reference implementation).

Measures the *escape rate* (residual undetected-error rate) for an open-world
(Bucket-B) agent-action claim class by backtesting a labeled set of agent actions
against ground-truth outcomes, and validates the estimate against the per-CT
tolerance declared in the conformance bundle's `escape_rate_tolerance_by_ct`.

Spec grounding (LAAS_proposal_v1.1.md):
  - §1.2 changelog: the metric formerly "integrity" is now the **escape rate**
    (residual undetected-error rate); integrity = 1 - escape_rate.
  - §5 "Two buckets and the escape-rate metric": Bucket B = bound / measure /
    control. MEASURE = estimate the escape rate by backtesting on a held-out,
    representative, adversarially-stressed set, *with a stated confidence interval*;
    re-measure on any model/prompt/tool/policy change.
  - §5: "Escape rate is the rate at which a wrong output passes every applicable
    check and is committed." -> an ESCAPE is an action whose verifier said "pass"
    but whose ground-truth label is "wrong". (A wrong action that the verifier
    caught is NOT an escape -- the check did its job.)
  - §7.1 obligation LAAS-OBL-IRR-001 residual_error.tolerance_by_ct mirrors
    data.json `escape_rate_tolerance_by_ct`; evidence: backtest_report_ref.
  - §7.2 conformance_predicate: ... residual_error_bound <= residual_tolerance.
    NOTE the predicate compares the BOUND, not the point estimate -> the pass/fail
    rule here is "upper CI bound <= tolerance", and the emitted
    `residual_error_bound` is the upper CI bound (what the policy consumes).
  - laas.rego: `residual_tolerance` is looked up by string CT key
    (sprintf("%d", [effective_ct])) against data.laas.escape_rate_tolerance_by_ct,
    and LAAS-OBL-RES-001 fires when input.residual_error_bound > residual_tolerance.
    This harness emits exactly that `residual_error_bound` field plus an evidence
    artifact whose id is referenceable from a decision trace's `evidence_refs`.

Statistical model
-----------------
The escape indicator is Bernoulli: each backtest sample either escaped (verifier
passed AND ground truth wrong) or did not. n samples, k escapes -> point estimate
p_hat = k/n. We report a one-sided upper confidence bound at level `confidence`
(default 0.95) and compare THAT bound (not p_hat) to the tolerance:

    PASS  iff  upper_ci_bound <= tolerance
    FAIL  iff  upper_ci_bound >  tolerance

Two interval methods, both pure-stdlib (no scipy):
  - "wilson"          : Wilson score upper bound (default; well-behaved at small k,
                        including k=0). Good general choice.
  - "clopper-pearson" : exact binomial (Clopper-Pearson) upper bound via an
                        in-house regularized incomplete beta. Strictly conservative;
                        REQUIRED interpretation when tolerance == 0 (e.g. CT4), where
                        only k=0 can possibly pass and even then the exact upper
                        bound is > 0 for any finite n -- see `tolerance == 0` handling.

Sample-size floor
-----------------
A tolerance of t can only be *demonstrated* if the achievable upper bound at k=0
can fall at or below t. We enforce a per-CT minimum n:
    n_min(t) = ceil( ln(1 - confidence) / ln(1 - t) )      (rule-of-three family)
i.e. the n at which the exact one-sided upper bound with zero observed escapes is
<= t. Below n_min the result is reported as INDETERMINATE (insufficient power),
never PASS. For t == 0 no finite n can demonstrate it by sampling alone; see below.

tolerance == 0 (e.g. CT4)
-------------------------
data.json sets CT4 tolerance to exactly 0. A binomial *upper bound* over any finite
sample is strictly > 0, so backtesting can never PASS a 0 tolerance on its own. This
mirrors the spec: CT4 is the deterministic/human-gated tier -- Bucket-B sampling does
not license a CT4 commit. The harness returns verdict INDETERMINATE with
disposition "requires_deterministic_or_human_gate" and sets residual_error_bound to
the achieved upper bound (so the rego LAAS-OBL-RES-001 check still fires if anyone
tries to treat it as a pass: any bound > 0 > tolerance 0).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# Field name the conformance policy consumes (laas.rego: input.residual_error_bound).
RESIDUAL_FIELD = "residual_error_bound"
TOLERANCE_MAP_KEY = "escape_rate_tolerance_by_ct"

# ---------------------------------------------------------------------------
# Statistics (pure stdlib)
# ---------------------------------------------------------------------------


# Inverse normal CDF (Acklam's rational approximation) -> z for a one-sided level.
def _z_for(confidence: float) -> float:
    """One-sided upper z-quantile, e.g. confidence=0.95 -> z(0.95) ~= 1.6449."""
    p = confidence
    if not (0.0 < p < 1.0):
        raise ValueError("confidence must be in (0,1)")
    # Coefficients for Acklam's algorithm.
    a = [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
    b = [
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    ]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
            * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
        )
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
        (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
    )


def wilson_upper_bound(k: int, n: int, confidence: float) -> float:
    """One-sided Wilson score UPPER bound for a binomial proportion."""
    if n == 0:
        return 1.0
    z = _z_for(confidence)
    p_hat = k / n
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
    return min(1.0, center + half)


# --- Regularized incomplete beta I_x(a,b), Lentz continued fraction (NR style) ---
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 200, 3.0e-12, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(ln_beta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def clopper_pearson_upper_bound(k: int, n: int, confidence: float) -> float:
    """
    Exact (Clopper-Pearson) one-sided UPPER bound at level `confidence`.
    Upper bound p_u solves  P(Bin(n,p_u) <= k) = 1 - confidence, i.e.
    p_u = BetaInv(confidence; k+1, n-k). We invert I_x via bisection on x.
    """
    if n == 0:
        return 1.0
    if k >= n:
        return 1.0
    alpha = 1.0 - confidence
    a, b = k + 1, n - k
    target = 1.0 - alpha  # the (1-alpha) quantile of Beta(k+1, n-k)
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _betai(a, b, mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


_INTERVAL_METHODS = {
    "wilson": wilson_upper_bound,
    "clopper-pearson": clopper_pearson_upper_bound,
}


def min_samples_for_tolerance(tolerance: float, confidence: float) -> Optional[int]:
    """
    Smallest n at which a zero-escape backtest yields an exact upper bound <= tolerance.
    Returns None when tolerance == 0 (no finite n suffices by sampling alone).
    Rule-of-three family: n_min = ceil( ln(alpha) / ln(1 - t) ).
    """
    if tolerance <= 0.0:
        return None
    alpha = 1.0 - confidence
    return math.ceil(math.log(alpha) / math.log(1.0 - tolerance))


# ---------------------------------------------------------------------------
# Tolerance lookup (tied to data.json keys)
# ---------------------------------------------------------------------------


class ToleranceLookupError(Exception):
    pass


def load_tolerance_map(data_json_path: Path) -> dict[str, float]:
    """Read escape_rate_tolerance_by_ct from the real conformance bundle data.json."""
    blob = json.loads(data_json_path.read_text())
    # data.json nests the bundle under "laas".
    cfg = blob.get("laas", blob)
    if TOLERANCE_MAP_KEY not in cfg:
        raise ToleranceLookupError(
            f"{data_json_path} has no '{TOLERANCE_MAP_KEY}' key under .laas"
        )
    return cfg[TOLERANCE_MAP_KEY]


def tolerance_for_ct(tol_map: dict[str, float], ct: int) -> float:
    """
    Look up the tolerance using the SAME string-key convention as laas.rego
    (sprintf("%d", [effective_ct])). If the CT has no entry, raise -- handled
    explicitly by the caller (a CT with no declared tolerance has no Bucket-B
    obligation defined and MUST NOT be silently treated as 0 or as pass).
    """
    key = str(int(ct))
    if key not in tol_map:
        raise ToleranceLookupError(
            f"CT {ct} (key '{key}') has no entry in {TOLERANCE_MAP_KEY}; "
            f"declared keys: {sorted(tol_map)}. A CT with no declared escape-rate "
            f"tolerance carries no Bucket-B residual obligation -- the harness "
            f"refuses to emit a pass/fail and the caller must handle it explicitly."
        )
    return float(tol_map[key])


# ---------------------------------------------------------------------------
# Dataset model
# ---------------------------------------------------------------------------


@dataclass
class Sample:
    """One backtested agent action."""

    action_id: str
    ct: int
    verifier_verdict: str  # "pass" | "fail" | "abstain" | "indeterminate"
    ground_truth: str  # "correct" | "wrong"

    def is_committed_pass(self) -> bool:
        # Only a "pass" verdict commits the action and can constitute an escape.
        return self.verifier_verdict == "pass"

    def is_escape(self) -> bool:
        # ESCAPE := verifier passed it AND ground truth is wrong (§5).
        return self.is_committed_pass() and self.ground_truth == "wrong"


def load_dataset(path: Path) -> list[Sample]:
    raw = json.loads(path.read_text())
    rows = raw["samples"] if isinstance(raw, dict) else raw
    out: list[Sample] = []
    for r in rows:
        out.append(
            Sample(
                action_id=str(r["action_id"]),
                ct=int(r["ct"]),
                verifier_verdict=str(r["verifier_verdict"]).lower(),
                ground_truth=str(r["ground_truth"]).lower(),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


@dataclass
class EvidenceArtifact:
    """
    Bucket-B backtest evidence artifact. Its `evidence_id` is what a decision
    trace lists in `evidence_refs` (§7.1 backtest_report_ref / §7.4 evidence_refs);
    `residual_error_bound` is the field the conformance policy (laas.rego
    LAAS-OBL-RES-001) consumes and compares to `residual_tolerance`.
    """

    schema: str = "laas.bucketB.backtest_evidence/v1"
    evidence_id: str = ""
    ct: int = 0
    bundle_id: str = ""
    tolerance_source: str = ""  # path to the data.json read
    n: int = 0
    committed_passes: int = 0  # denominator detail: passes among n
    escapes: int = 0
    escape_rate_point: float = 0.0  # k/n point estimate
    residual_error_bound: float = 0.0  # one-sided UPPER CI bound (policy-consumed)
    residual_tolerance: float = 0.0
    confidence: float = 0.95
    interval_method: str = "wilson"
    min_samples_required: Optional[int] = None
    verdict: str = ""  # pass | fail | indeterminate
    disposition: str = ""  # human-readable rule that fired
    integrity_metric: float = 0.0  # 1 - escape_rate_point (higher-is-better)
    dataset_sha256: str = ""
    measured_at: str = ""
    notes: list[str] = field(default_factory=list)


def measure(
    samples: list[Sample],
    ct: int,
    tol_map: dict[str, float],
    *,
    confidence: float = 0.95,
    interval_method: str = "wilson",
    bundle_id: str = "",
    tolerance_source: str = "",
    dataset_sha256: str = "",
) -> EvidenceArtifact:
    tolerance = tolerance_for_ct(tol_map, ct)  # raises if CT undeclared
    bound_fn = _INTERVAL_METHODS[interval_method]

    ct_samples = [s for s in samples if s.ct == ct]
    n = len(ct_samples)
    committed = sum(1 for s in ct_samples if s.is_committed_pass())
    escapes = sum(1 for s in ct_samples if s.is_escape())

    point = (escapes / n) if n else 0.0
    upper = bound_fn(escapes, n, confidence) if n else 1.0
    n_min = min_samples_for_tolerance(tolerance, confidence)

    art = EvidenceArtifact(
        evidence_id="",  # filled below from a content hash
        ct=ct,
        bundle_id=bundle_id,
        tolerance_source=tolerance_source,
        n=n,
        committed_passes=committed,
        escapes=escapes,
        escape_rate_point=round(point, 6),
        residual_error_bound=round(upper, 6),
        residual_tolerance=tolerance,
        confidence=confidence,
        interval_method=interval_method,
        min_samples_required=n_min,
        integrity_metric=round(1.0 - point, 6),
        dataset_sha256=dataset_sha256,
        measured_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
    )

    # Decision logic.
    if n == 0:
        art.verdict = "indeterminate"
        art.disposition = "no_samples_for_ct"
        art.notes.append(f"No backtest samples carry ct={ct}.")
    elif tolerance == 0.0:
        # CT with a zero tolerance (e.g. CT4): un-demonstrable by sampling.
        art.verdict = "indeterminate"
        art.disposition = "requires_deterministic_or_human_gate"
        art.notes.append(
            "Tolerance is 0; a binomial upper bound over finite n is strictly > 0, "
            "so Bucket-B sampling can never PASS. This CT must be gated by a "
            "deterministic/exact verifier or human (LAAS §5 / CT4)."
        )
    elif n_min is not None and n < n_min:
        art.verdict = "indeterminate"
        art.disposition = "insufficient_sample_size"
        art.notes.append(
            f"n={n} < n_min={n_min} required to demonstrate tolerance {tolerance} "
            f"at confidence {confidence}; underpowered -> never PASS."
        )
    elif upper <= tolerance:
        art.verdict = "pass"
        art.disposition = "upper_ci_bound_within_tolerance"
    else:
        art.verdict = "fail"
        art.disposition = "upper_ci_bound_exceeds_tolerance"

    # Content-addressed evidence id (stable, referenceable from a decision trace).
    digest_src = json.dumps(
        {
            k: v
            for k, v in asdict(art).items()
            if k not in ("evidence_id", "measured_at")
        },
        sort_keys=True,
    ).encode()
    art.evidence_id = "ev_backtest_" + hashlib.sha256(digest_src).hexdigest()[:16]
    return art


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="LAAS Bucket-B escape-rate backtest harness"
    )
    ap.add_argument("--dataset", required=True, type=Path, help="backtest dataset JSON")
    ap.add_argument(
        "--data-json",
        required=True,
        type=Path,
        help="conformance bundle data.json (source of escape_rate_tolerance_by_ct)",
    )
    ap.add_argument("--ct", required=True, type=int, help="Consequence Tier to measure")
    ap.add_argument("--confidence", type=float, default=0.95)
    ap.add_argument("--interval", choices=sorted(_INTERVAL_METHODS), default="wilson")
    ap.add_argument(
        "--out", type=Path, default=None, help="write evidence artifact JSON here"
    )
    args = ap.parse_args(argv)

    blob = json.loads(args.data_json.read_text())
    bundle_id = blob.get("laas", {}).get("bundle_id", "")
    tol_map = load_tolerance_map(args.data_json)
    samples = load_dataset(args.dataset)
    ds_hash = _sha256_file(args.dataset)

    try:
        art = measure(
            samples,
            args.ct,
            tol_map,
            confidence=args.confidence,
            interval_method=args.interval,
            bundle_id=bundle_id,
            tolerance_source=str(args.data_json),
            dataset_sha256=ds_hash,
        )
    except ToleranceLookupError as e:
        print(
            json.dumps({"error": "tolerance_lookup", "detail": str(e)}, indent=2),
            file=sys.stderr,
        )
        return 3

    payload = json.dumps(asdict(art), indent=2)
    if args.out:
        args.out.write_text(payload + "\n")
    print(payload)
    # Exit code mirrors the gate semantics: 0 pass, 1 fail, 2 indeterminate.
    return {"pass": 0, "fail": 1, "indeterminate": 2}[art.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
