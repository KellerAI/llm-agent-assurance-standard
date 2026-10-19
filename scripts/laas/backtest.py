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
    and LAAS-OBL-RES-001 fires when the valid residual_error_bound (`_valid_bound`,
    laas.rego:345) > residual_tolerance. At a zero tolerance (CT4) that comparison
    is skipped for a Bucket-A or human-gated action (laas.rego:318-346).
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
data.json sets CT4 tolerance to exactly 0. measure() routes tolerance == 0 to
INDETERMINATE before the bound is ever compared, so backtesting never PASSes it. This
mirrors the spec: CT4 is the deterministic/human-gated tier -- Bucket-B sampling does
not license a CT4 commit. The verdict is INDETERMINATE with disposition
"requires_deterministic_or_human_gate"; residual_error_bound, the achieved bound to 6
places, is stored as 0.0 if tiny; below confidence 0.5 Wilson can store -0.0. The rego
LAAS-OBL-RES-001 check fires on a stored bound > 0 only for a trace neither Bucket A nor
human-gated. For those two the deterministic or human gate is the control
(standard/LAAS.md:108-114), and the bound is evidence, not a pass condition.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import sys
from dataclasses import dataclass, field, asdict
from fractions import Fraction
from pathlib import Path
from typing import NoReturn, Optional

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
    Returns 1 when tolerance == 1, where the formula would take ln(0): every upper
    bound is <= 1 (the zero-escape exact bound is 1 - alpha**(1/n)), so one sample
    demonstrates it. This is the formula's limit, as n_min(t) == 1 for 1-alpha <= t < 1.

    ln(1 - t) is computed as log1p(-t): for t <= ~5e-17, 1.0 - t rounds to 1.0 and
    log(1.0 - t) is 0. For t below ~1e-308 the float quotient overflows to inf, so
    it is redone exactly on the two floats' rational values. Either way n_min is a
    finite, very large int: any t in (0, 1] is demonstrable in principle, and a
    backtest smaller than n_min is INDETERMINATE, not an input error.
    """
    if tolerance <= 0.0:
        return None
    if tolerance >= 1.0:
        return 1
    alpha = 1.0 - confidence
    ln_alpha, ln_one_minus_t = math.log(alpha), math.log1p(-tolerance)
    quotient = ln_alpha / ln_one_minus_t
    if math.isfinite(quotient):
        return math.ceil(quotient)
    return math.ceil(Fraction(ln_alpha) / Fraction(ln_one_minus_t))


# ---------------------------------------------------------------------------
# Tolerance lookup (tied to data.json keys)
# ---------------------------------------------------------------------------


class ToleranceLookupError(Exception):
    pass


class BacktestInputError(Exception):
    """An input file is unreadable, not valid JSON, lacks a required key, or holds
    a tolerance that is not a number in [0, 1] or a bundle_id that is not a string.

    The CLI exits 3 on it (the harness's error code, never a verdict code), so
    malformed input can never read as pass, fail, or indeterminate.
    """


def _read_json(path: Path) -> object:
    """Parse `path` as JSON; raise BacktestInputError naming the file."""
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError) as e:
        reason = getattr(e, "strerror", None) or e
        raise BacktestInputError(f"{path}: cannot read file: {reason}") from e
    try:
        return json.loads(text)
    except (json.JSONDecodeError, RecursionError) as e:
        # RecursionError: nesting too deep for the parser.
        raise BacktestInputError(f"{path}: invalid JSON: {e}") from e
    except ValueError as e:
        # An integer literal over Python's int digit limit (sys.int_info).
        if "integer string conversion" not in str(e):
            raise
        raise BacktestInputError(f"{path}: invalid JSON: {e}") from e


def load_bundle(data_json_path: Path) -> dict:
    """Read the conformance bundle data.json; it must be a JSON object."""
    blob = _read_json(data_json_path)
    if not isinstance(blob, dict):
        raise BacktestInputError(
            f"{data_json_path}: expected a JSON object, got {type(blob).__name__}"
        )
    return blob


def load_tolerance_map(data_json_path: Path) -> dict[str, float]:
    """Read escape_rate_tolerance_by_ct from the real conformance bundle data.json."""
    blob = load_bundle(data_json_path)
    # data.json nests the bundle under "laas".
    cfg = blob.get("laas", blob)
    if TOLERANCE_MAP_KEY not in cfg:
        raise ToleranceLookupError(
            f"{data_json_path} has no '{TOLERANCE_MAP_KEY}' key under .laas"
        )
    tol_map = cfg[TOLERANCE_MAP_KEY]
    if not isinstance(tol_map, dict):
        raise BacktestInputError(
            f"{data_json_path}: {TOLERANCE_MAP_KEY} must be a JSON object, "
            f"got {type(tol_map).__name__}"
        )
    # Validate every entry, not only the CT being measured: a bundle with any
    # malformed tolerance is malformed input, never a verdict.
    return {
        key: _tolerance_value(f"{data_json_path}: {TOLERANCE_MAP_KEY}", key, value)
        for key, value in tol_map.items()
    }


def _tolerance_value(where: str, key: str, value: object) -> float:
    """Return `value` as a float if it is a finite JSON number t with 0 <= t <= 1.

    bool is rejected (JSON true/false are not numbers), and so are numeric strings.
    The range test runs before isfinite: comparing a huge int to 0 and 1 is exact,
    while isfinite would convert it to float and raise OverflowError.
    """
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= 1
        or not math.isfinite(value)
    ):
        raise BacktestInputError(
            f"{where}['{key}'] must be a finite number in [0, 1], "
            f"got {json.dumps(value, default=repr)}"
        )
    return float(value)


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
    return _tolerance_value(TOLERANCE_MAP_KEY, key, tol_map[key])


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
    raw = _read_json(path)
    if isinstance(raw, dict):
        if "samples" not in raw:
            raise BacktestInputError(f"{path}: missing key 'samples'")
        rows = raw["samples"]
    else:
        rows = raw
    if not isinstance(rows, list):
        raise BacktestInputError(
            f"{path}: samples must be a JSON array, got {type(rows).__name__}"
        )
    out: list[Sample] = []
    for i, r in enumerate(rows):
        try:
            out.append(
                Sample(
                    action_id=str(r["action_id"]),
                    ct=int(r["ct"]),
                    verifier_verdict=str(r["verifier_verdict"]).lower(),
                    ground_truth=str(r["ground_truth"]).lower(),
                )
            )
        except KeyError as e:
            raise BacktestInputError(f"{path}: sample {i}: missing key {e}") from e
        except (TypeError, ValueError, OverflowError) as e:
            # OverflowError: int() of an infinite ct (Infinity, 1e999).
            raise BacktestInputError(f"{path}: sample {i}: malformed: {e}") from e
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
            "Tolerance is 0; this branch runs before any bound comparison, "
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


def _split_usage_error(message: str) -> tuple[str, str]:
    """Split an argparse error message into (argument, reason), on one line."""
    message = " ".join(message.splitlines())
    for prefix, reason in (
        ("the following arguments are required: ", "required argument missing"),
        ("unrecognized arguments: ", "unrecognized argument"),
    ):
        if message.startswith(prefix):
            return message[len(prefix) :], reason
    for prefix, sep in (("argument ", ": "), ("ambiguous option: ", " ")):
        if message.startswith(prefix):
            arg, found, reason = message[len(prefix) :].partition(sep)
            if found:
                return arg, reason
    return "command line", message


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser whose usage errors exit 3 with one BACKTEST INPUT ERROR line.

    argparse's own error() prints the usage block and exits 2, which is the
    indeterminate verdict code. --help still prints help and exits 0.
    """

    def error(self, message: str) -> NoReturn:
        arg, reason = _split_usage_error(message)
        self.exit(3, f"BACKTEST INPUT ERROR: {arg}: {reason}\n")


def main(argv: Optional[list[str]] = None) -> int:
    ap = _ArgumentParser(description="LAAS Bucket-B escape-rate backtest harness")
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

    try:
        c = args.confidence
        # alpha = 1.0 - c, as in clopper_pearson_upper_bound and
        # min_samples_for_tolerance; alpha == 1.0 would make n_min 0.
        if not (math.isfinite(c) and 0.0 < c < 1.0 and 1.0 - c < 1.0):
            raise BacktestInputError(
                "--confidence: must be a finite number with 0 < c < 1 and "
                f"1 - c < 1 in float (c > 2**-54), got {c}"
            )
        blob = load_bundle(args.data_json)
        laas_cfg = blob.get("laas", {})
        if not isinstance(laas_cfg, dict):
            raise BacktestInputError(f"{args.data_json}: .laas must be a JSON object")
        bundle_id = laas_cfg.get("bundle_id", "")
        if not isinstance(bundle_id, str):
            # Type name only: repr of a deeply nested list would recurse.
            raise BacktestInputError(
                f"{args.data_json}: bundle_id must be a JSON string, "
                f"got {type(bundle_id).__name__}"
            )
        tol_map = load_tolerance_map(args.data_json)
        samples = load_dataset(args.dataset)
        ds_hash = _sha256_file(args.dataset)
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
    except BacktestInputError as e:
        # One line on stderr; exit 3 is the harness's error code, never a verdict.
        print(f"BACKTEST INPUT ERROR: {e}", file=sys.stderr)
        return 3
    except ToleranceLookupError as e:
        print(
            json.dumps({"error": "tolerance_lookup", "detail": str(e)}, indent=2),
            file=sys.stderr,
        )
        return 3

    payload = json.dumps(asdict(art), indent=2)
    if args.out:
        # Write before printing, so a failed write leaves stdout empty.
        try:
            args.out.write_text(payload + "\n")
        except OSError as e:
            print(f"BACKTEST INPUT ERROR: --out: {e.strerror or e}", file=sys.stderr)
            return 3
    print(payload)
    # Exit code mirrors the gate semantics: 0 pass, 1 fail, 2 indeterminate.
    return {"pass": 0, "fail": 1, "indeterminate": 2}[art.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
