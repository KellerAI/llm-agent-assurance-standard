#!/usr/bin/env python3
"""LAAS v1.1 ActionDescriptor / decision-record emitter (reference implementation).

The runtime component that translates a live agent's *observed effect surface*
into the decision-record JSON evaluated by package `kellerai.laas.actions`
(conformance/laas/laas.rego).

GOVERNING INVARIANT (LAAS v1.1 §0.1, §8.1): the gate -- never the actor --
derives the Consequence Tier from the OBSERVED effect surface. This module is
the gate-side emitter. Nothing here ever reads a tier the agent proposes and
uses it to lower the assigned tier. `self_reported_ct` is carried for the
SELF-001 warning ONLY; it is informational and can never reduce `assigned_ct`.

Output contract is fixed by laas.rego + examples/action.ct4-blocked.json.
Every field the policy reads is sourced here from the effect surface or from
gate-controlled configuration. A field the emitter cannot yet source from a
real harness is emitted as a conservative (fail-closed) default and called out
as a TODO in DESIGN.md -- never fabricated to make a record pass.

Stdlib only (json, argparse, hashlib, datetime, sys). No third-party deps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

# ---------------------------------------------------------------------------
# CT lattice -- MUST mirror data.laas.tier_lattice in data.json.
# Loaded from the (signed) bundle at runtime; duplicated here only as the
# fallback / self-check default. The gate is the authority, so we read the
# bundle when one is supplied (see GateContext.from_bundle).
# ---------------------------------------------------------------------------
_DEFAULT_LATTICE = {
    "reversibility": {"reversible": 1, "hard": 3, "irreversible": 4, "none": 4},
    "scope": {"single": 1, "multi": 2, "org": 3, "public": 4},
    "consequence": {"none": 0, "low": 1, "material": 3, "high": 4},
}
# §6.2 default-to-highest: an undetermined axis resolves to its worst key.
_UNKNOWN_DEFAULT = {
    "reversibility": "none",  # unknown -> treat as irreversible (CT4)
    "scope": "public",  # unknown -> public (CT4)
    "consequence": "high",  # unknown -> high (CT4)
}
_DEFAULT_CT_WHEN_UNDETERMINED = 4
_VALID_VERDICTS = {"pass", "fail", "abstain", "indeterminate"}
_VALID_VERIFIER_TYPES = {"deterministic", "model", "human"}


class EmitterInputError(ValueError):
    """An input file (spec or bundle) is unreadable, malformed, or incomplete.

    Raised instead of falling back to defaults: a bad bundle fails closed.
    """


def _int_digit_error(e: ValueError, where: str) -> EmitterInputError:
    """Map json's integer digit-limit ValueError to an invalid-JSON error.

    json.loads raises a plain ValueError, not JSONDecodeError, for an integer
    longer than sys.get_int_max_str_digits(). Any other ValueError re-raises.
    """
    if type(e) is not ValueError or "integer string conversion" not in str(e):
        raise e
    return EmitterInputError(f"{where}: invalid JSON: {e}")


def _object_at(parent: dict, key: str, where: str, prefix: str = "") -> dict:
    """Return `parent[key]`; raise EmitterInputError unless it is a JSON object.

    `where` names the input ("bundle <path>" / "spec <path>"); `prefix` is the
    dotted path of `parent`, so messages name the full key.
    """
    if key not in parent:
        raise EmitterInputError(f"{where}: missing key '{prefix}{key}'")
    value = parent[key]
    if not isinstance(value, dict):
        raise EmitterInputError(
            f"{where}: {prefix}{key} must be a JSON object, got {type(value).__name__}"
        )
    return value


def _is_number(value: Any) -> bool:
    """True for a JSON number or boolean: anything max() can compare to a CT.

    Range and bool are deliberately not checked here; validate_emitted owns
    the 0..4 check on the emitted tier.
    """
    return isinstance(value, (int, float))


def _check_bundle(blob: Any, where: str) -> dict:
    """Return the bundle's `laas` object; raise EmitterInputError unless the
    top level and `laas` are objects and `laas.tier_lattice` is present.

    Only the keys every run reads are checked here. The lattice's shape and
    values and `laas.default_ct_when_undetermined` are checked by derive_ct
    where it reads them, so a bad entry the spec never reaches still emits.
    """
    if not isinstance(blob, dict):
        raise EmitterInputError(
            f"{where}: expected a JSON object, got {type(blob).__name__}"
        )
    cfg = _object_at(blob, "laas", where)
    if "tier_lattice" not in cfg:
        raise EmitterInputError(f"{where}: missing key 'tier_lattice'")
    return cfg


# ---------------------------------------------------------------------------
# Inputs: the live agent's effect surface + the gate's side-channels.
# ---------------------------------------------------------------------------
@dataclass
class EffectSurface:
    """The OBSERVED effect surface of one proposed action -- what the gate sees
    on the wire (the tool/API + its arguments), NOT what the agent claims.

    `external_effect` is True for any write/side-effect that escapes the
    sandbox: file writes outside scratch, shell commands with effects, network
    calls, git/ledger mutations. A read-only / sandboxed action is False -> CT0.

    The three axis keys are gate-classified from the resolved call. Pass None
    for an axis the gate could not determine; it resolves to the §6.2 worst-key.
    """

    external_effect: bool
    reversibility: Optional[str] = None  # reversible|hard|irreversible|none
    scope: Optional[str] = None  # single|multi|org|public
    consequence: Optional[str] = None  # none|low|material|high
    tool: Optional[str] = None  # provenance only (e.g. payments.transfer)


@dataclass
class GateContext:
    """Gate-controlled configuration and enforcement-plane attestations.

    These are properties of the GATE, sourced from the deployment, never from
    the agent: the signed bundle id/version, whether the bundle signature
    verified, and whether this gate runs out-of-process (§7.7).
    """

    bundle_id: str = "laas-fin-2.0.0"
    bundle_version: str = "laas-fin-2.0.0"
    bundle_signed: bool = True
    out_of_process: bool = True
    lattice: dict = field(default_factory=lambda: dict(_DEFAULT_LATTICE))
    ct_when_undetermined: int = _DEFAULT_CT_WHEN_UNDETERMINED
    # The data.json the lattice came from; names it in derive_ct's errors.
    bundle_path: Optional[str] = None

    @classmethod
    def from_bundle(cls, data_json_path: str, **overrides: Any) -> "GateContext":
        """Load the lattice from a signed obligation bundle (data.json).

        Raises EmitterInputError (naming the file) if the bundle cannot be
        read, is not UTF-8, is not valid JSON, or lacks the keys
        _check_bundle checks. derive_ct checks the lattice entries it reads.
        """
        try:
            with open(data_json_path, encoding="utf-8") as fh:
                blob = json.load(fh)
        except (OSError, UnicodeDecodeError) as e:
            reason = getattr(e, "strerror", None) or e
            raise EmitterInputError(
                f"cannot read bundle {data_json_path}: {reason}"
            ) from e
        except (json.JSONDecodeError, RecursionError) as e:
            raise EmitterInputError(
                f"bundle {data_json_path}: invalid JSON: {e}"
            ) from e
        except ValueError as e:
            raise _int_digit_error(e, f"bundle {data_json_path}") from e
        cfg = _check_bundle(blob, f"bundle {data_json_path}")
        lattice = cfg["tier_lattice"]
        kwargs: dict[str, Any] = {
            "bundle_id": cfg.get("bundle_id", "laas-fin-2.0.0"),
            "bundle_version": cfg.get("bundle_id", "laas-fin-2.0.0"),
            "lattice": lattice,
            "ct_when_undetermined": cfg.get(
                "default_ct_when_undetermined", _DEFAULT_CT_WHEN_UNDETERMINED
            ),
            "bundle_path": data_json_path,
        }
        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class VerifierResult:
    """The result of the gate-invoked pre-commit verifier (§7.1/§7.3/§7.5).

    The gate -- not the agent -- selects and runs the verifier. `verdict`,
    `type`, `model_lineage`, `error_correlation`, `qualified` are reported by
    the gate's verifier registry, not self-asserted by the actor.
    """

    id: str
    type: str  # deterministic|model|human
    verdict: str  # pass|fail|abstain|indeterminate
    qualified: bool = False
    model_lineage: str = "n/a"  # for model verifiers; "n/a" otherwise
    error_correlation: Optional[float] = None  # vs actor lineage; model only
    qualification_ref: Optional[str] = None
    input_hash: Optional[str] = None


@dataclass
class ActorContext:
    actor_id: str
    actor_model_lineage: str
    # Informational ONLY (SELF-001). NEVER used to lower the gate tier.
    self_reported_ct: Optional[int] = None


@dataclass
class AggregateState:
    """Windowed cumulative blast radius for this principal/session/effect-class
    (§6.4). Maintained by the gate; sourced from the gate's aggregation store.
    """

    window_effect_ct: int = 0


@dataclass
class VendorInfo:
    used: bool = False
    attribution: Optional[str] = None
    scope_limited: bool = False


@dataclass
class InputProvenance:
    """§8.3: was this action driven by untrusted input (web/email/3p data)?
    Untrusted input is a tier-raising signal; the gate sources this from the
    provenance tag on the inbound context, not from the agent."""

    trusted: bool = True


@dataclass
class TraceAnchor:
    """Append-only chained-trace integrity fields (§7.4/§7.7). Supplied by the
    gate's append-only sink, which the actor cannot rewrite."""

    append_only: bool = True
    actor_chain_prev_hash: Optional[str] = None
    merkle_anchor: Optional[str] = None


# ---------------------------------------------------------------------------
# CT derivation (gate-side; §6.1). This is the ungameable core.
# ---------------------------------------------------------------------------
def _gate_where(gate: GateContext) -> str:
    """Name the lattice's source in an EmitterInputError message."""
    return f"bundle {gate.bundle_path}" if gate.bundle_path else "gate lattice"


def derive_ct(surface: EffectSurface, gate: GateContext) -> tuple[int, dict]:
    """Return (gate_derived_ct, resolved_surface_keys).

    Matches laas.rego's `expected_ct` (laas.rego:30-45) for a boolean
    `external_effect` only when `gate.lattice` equals the policy bundle's
    `tier_lattice` (data.json:7-9) and `gate.ct_when_undetermined` is 4
    (laas.rego:30). Both are the GateContext defaults; overriding either
    can put `assigned_ct` below the policy's tier (TIER-001):

        - external_effect False         -> CT0
        - external effect, keys known   -> max(rev, scope, consequence)
        - any axis undetermined         -> ct_when_undetermined (4)

    Callers must pass a real bool for `external_effect`. For a non-boolean
    value this function diverges from the policy: a falsy one (e.g. None)
    returns CT0 while the policy returns CT4 (laas.rego:30), and a truthy
    one takes the lattice path while the policy also returns CT4. The
    policy mismatch is tracked as a follow-up; fail-closed emitter
    behaviour is not implemented here.

    Raises EmitterInputError (naming the bundle and the dotted key) when an
    external effect reaches a lattice entry that would crash it: a lattice
    or axis that is not an object, an absent axis, an absent §6.2 worst key
    it falls back to, a non-number default CT it returns, or a non-number
    lattice value it compares. Entries it does not reach are not checked.
    """
    if not surface.external_effect:
        return 0, {"external_effect": False}

    where = _gate_where(gate)
    lattice = gate.lattice
    if not isinstance(lattice, dict):
        raise EmitterInputError(
            f"{where}: laas.tier_lattice must be a JSON object, "
            f"got {type(lattice).__name__}"
        )
    resolved: dict[str, Any] = {"external_effect": True}
    axis_cts: list[int] = []
    undetermined = False
    axes = ("reversibility", "scope", "consequence")
    for axis in axes:
        key = getattr(surface, axis)
        if key is None:
            key = _UNKNOWN_DEFAULT[axis]
            undetermined = True
        table = _object_at(lattice, axis, where, "laas.tier_lattice.")
        if key not in table:
            # An unrecognized key is itself "undetermined" -> fail closed.
            key = _UNKNOWN_DEFAULT[axis]
            undetermined = True
            if key not in table:
                raise EmitterInputError(
                    f"{where}: laas.tier_lattice.{axis} must include {key!r}"
                )
        resolved[axis] = key
        axis_cts.append(table[key])

    if undetermined:
        # The axis values are not compared on this path; only the default is.
        ct = gate.ct_when_undetermined
        if not _is_number(ct):
            raise EmitterInputError(
                f"{where}: laas.default_ct_when_undetermined must be a number, "
                f"got {ct!r}"
            )
        return ct, resolved
    for axis, ct in zip(axes, axis_cts):
        if not _is_number(ct):
            raise EmitterInputError(
                f"{where}: laas.tier_lattice.{axis}.{resolved[axis]} must be "
                f"a number, got {ct!r}"
            )
    return max(axis_cts), resolved


def _surface_hash(resolved: dict) -> str:
    canonical = json.dumps(resolved, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Emit the policy-ready decision record.
# ---------------------------------------------------------------------------
def emit_decision_record(
    *,
    surface: EffectSurface,
    actor: ActorContext,
    gate: GateContext,
    verifier: Optional[VerifierResult] = None,
    human_approved: bool = False,
    aggregate: Optional[AggregateState] = None,
    vendor: Optional[VendorInfo] = None,
    input_prov: Optional[InputProvenance] = None,
    trace: Optional[TraceAnchor] = None,
    residual_error_bound: Optional[float] = None,
    action_blocked: bool = False,
    escalation_approved: bool = False,
    action_id: Optional[str] = None,
) -> dict:
    """Build a decision record matching the laas.rego input contract exactly.

    GATE-DERIVED, NOT AGENT-ASSERTED: `gate.assigned_ct` is computed here from
    the observed surface via derive_ct(). The aggregate window can only RAISE
    the effective tier (policy: effective_ct = max(gate ct, window_ct); gate ct = assigned_ct, or the lattice ct when absent or not an integer 0..4).
    """
    aggregate = aggregate or AggregateState()
    vendor = vendor or VendorInfo()
    input_prov = input_prov or InputProvenance()
    trace = trace or TraceAnchor()

    gate_derived_ct, resolved = derive_ct(surface, gate)
    # §6.4 structuring guard: the gate must assign at least the cumulative
    # window tier. We surface the per-action lattice tier as assigned_ct and
    # let the policy re-tier via window_effect_ct, but we also fold the window
    # in here so a single record is never below the window (AGG-001 safe).
    assigned_ct = max(gate_derived_ct, aggregate.window_effect_ct)

    effect_surface_obj: dict[str, Any] = {"external_effect": surface.external_effect}
    if surface.tool is not None:
        effect_surface_obj["tool"] = surface.tool
    if surface.external_effect:
        effect_surface_obj["reversibility"] = resolved["reversibility"]
        effect_surface_obj["scope"] = resolved["scope"]
        effect_surface_obj["consequence"] = resolved["consequence"]

    # --- the policy-read object graph (input.*) ---
    record: dict[str, Any] = {
        "action": {
            "id": action_id or "act_unknown",
            "actor_id": actor.actor_id,
            "actor_model_lineage": actor.actor_model_lineage,
            # informational; SELF-001 fires if below assigned_ct, never lowers it
            "self_reported_ct": (
                actor.self_reported_ct
                if actor.self_reported_ct is not None
                else assigned_ct
            ),
            "effect_surface": effect_surface_obj,
        },
        "gate": {
            "assigned_ct": assigned_ct,  # GATE-DERIVED (§6.1)
            "bundle_version": gate.bundle_version,
            "bundle_signed": gate.bundle_signed,  # §7.7
            "out_of_process": gate.out_of_process,  # §7.7
        },
        "aggregate": {"window_effect_ct": aggregate.window_effect_ct},  # §6.4
        "human_approval": {"approved": human_approved},
        "vendor": {
            "used": vendor.used,
            "attribution": vendor.attribution,  # null when unknown -> VEN-001
            "scope_limited": vendor.scope_limited,
        },
        "input": {"trusted": input_prov.trusted},  # §8.3
        "trace": {
            "append_only": trace.append_only,  # §7.4 / TRC-001
            "actor_chain_prev_hash": trace.actor_chain_prev_hash,
            "merkle_anchor": trace.merkle_anchor,
        },
        # null for pure Bucket A; <= tolerance for Bucket B (§5 / RES-001)
        "residual_error_bound": residual_error_bound,
        "action_blocked": action_blocked,
        "escalation_approved": escalation_approved,
    }

    # Verifier block: required by the policy whenever effective_ct >= 3
    # (IRR/IND/VQ-001). For CT<3 a verifier may be absent; we emit an
    # abstaining placeholder so verifier_passed is simply false (harmless).
    if verifier is not None:
        v: dict[str, Any] = {
            "id": verifier.id,
            "type": verifier.type,
            "model_lineage": verifier.model_lineage,
            "qualified": verifier.qualified,
            "verdict": verifier.verdict,
        }
        if verifier.error_correlation is not None:
            v["error_correlation"] = verifier.error_correlation
        record["verifier"] = v
    else:
        record["verifier"] = {
            "id": "none",
            "type": "deterministic",
            "model_lineage": "n/a",
            "qualified": False,
            "verdict": "indeterminate",
        }

    return record


def validate_emitted(record: dict) -> list[str]:
    """Cheap pre-flight: catch malformed records before opa sees them.
    These mirror enum/shape constraints the policy assumes (not the
    obligations themselves -- those are the policy's job)."""
    problems: list[str] = []
    v = record.get("verifier", {})
    if v.get("verdict") not in _VALID_VERDICTS:
        problems.append(
            f"verifier.verdict {v.get('verdict')!r} not in {_VALID_VERDICTS}"
        )
    if v.get("type") not in _VALID_VERIFIER_TYPES:
        problems.append(
            f"verifier.type {v.get('type')!r} not in {_VALID_VERIFIER_TYPES}"
        )
    ct = record["gate"]["assigned_ct"]
    if not isinstance(ct, int) or not (0 <= ct <= 4):
        problems.append(f"gate.assigned_ct {ct!r} not an int in 0..4")
    return problems


# ---------------------------------------------------------------------------
# CLI: read an effect-surface description (JSON) on stdin/-i, emit a record.
# ---------------------------------------------------------------------------
_SPEC_OBJECT_KEYS = (
    "actor",
    "aggregate",
    "vendor",
    "input",
    "trace",
    "human_approval",
    "action",
)


def _require_scalar(value: Any, name: str, where: str) -> None:
    """Reject a JSON array/object where the emitter needs a hashable value."""
    if isinstance(value, (list, dict)):
        raise EmitterInputError(
            f"{where}: {name} must be a JSON scalar, got {type(value).__name__}"
        )


def _read_spec(path: Optional[str]) -> Any:
    """Read and parse the spec from `path` (or stdin when None).

    A spec that is unreadable, not UTF-8 or not valid JSON raises
    EmitterInputError. The spec is read as the original emitter read it --
    a file in text mode (CR and CRLF reach json.loads as LF), stdin through
    sys.stdin -- so an invalid-JSON message reports the same line, column
    and offset.
    """
    where = f"spec {path or '<stdin>'}"
    try:
        if path:
            with open(path, encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except OSError as e:
        raise EmitterInputError(f"cannot read {where}: {e.strerror}") from e
    except UnicodeDecodeError as e:
        raise EmitterInputError(f"cannot read {where}: {e}") from e
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, RecursionError) as e:
        raise EmitterInputError(f"{where}: invalid JSON: {e}") from e
    except ValueError as e:
        raise _int_digit_error(e, where) from e


def _check_spec(spec: Any, where: str) -> dict:
    """Check every spec key _build_from_spec reads; raise EmitterInputError
    on the first one whose shape would otherwise crash it (fail closed).

    `effect_surface.external_effect` is required but its type is not checked
    (see derive_ct); an unrecognized axis scalar resolves to the worst key.
    The axes must be scalars only when `external_effect` is truthy: derive_ct
    does not read them otherwise.
    """
    if not isinstance(spec, dict):
        raise EmitterInputError(
            f"{where}: expected a JSON object, got {type(spec).__name__}"
        )
    surface = _object_at(spec, "effect_surface", where)
    if "external_effect" not in surface:
        raise EmitterInputError(
            f"{where}: missing key 'effect_surface.external_effect'"
        )
    if surface["external_effect"]:
        for axis in _UNKNOWN_DEFAULT:
            _require_scalar(surface.get(axis), f"effect_surface.{axis}", where)
    for key in _SPEC_OBJECT_KEYS:
        if key in spec:
            _object_at(spec, key, where)
    window = spec.get("aggregate", {}).get("window_effect_ct", 0)
    if not _is_number(window):
        raise EmitterInputError(
            f"{where}: aggregate.window_effect_ct must be a number, got {window!r}"
        )
    # A falsy verifier (null, {}, [], 0, "", false) means "no verifier": the
    # placeholder is emitted. Only a non-empty non-object one is rejected.
    verifier = spec.get("verifier")
    if verifier and not isinstance(verifier, dict):
        raise EmitterInputError(
            f"{where}: verifier must be a JSON object, got {type(verifier).__name__}"
        )
    if verifier:
        for key in ("id", "type", "verdict"):
            if key not in verifier:
                raise EmitterInputError(f"{where}: missing key 'verifier.{key}'")
        for key in ("type", "verdict"):
            _require_scalar(verifier[key], f"verifier.{key}", where)
    return spec


def _build_from_spec(spec: dict, gate: GateContext) -> dict:
    """Map a flat effect-surface spec (what a harness adapter would hand us)
    into the dataclass inputs and emit the record."""
    s = spec["effect_surface"]
    surface = EffectSurface(
        external_effect=s["external_effect"],
        reversibility=s.get("reversibility"),
        scope=s.get("scope"),
        consequence=s.get("consequence"),
        tool=s.get("tool"),
    )
    a = spec.get("actor", {})
    actor = ActorContext(
        actor_id=a.get("actor_id", "agent.unknown"),
        actor_model_lineage=a.get("actor_model_lineage", "unknown-lineage"),
        self_reported_ct=a.get("self_reported_ct"),
    )
    ver_spec = spec.get("verifier")
    verifier = (
        VerifierResult(
            id=ver_spec["id"],
            type=ver_spec["type"],
            verdict=ver_spec["verdict"],
            qualified=ver_spec.get("qualified", False),
            model_lineage=ver_spec.get("model_lineage", "n/a"),
            error_correlation=ver_spec.get("error_correlation"),
            qualification_ref=ver_spec.get("qualification_ref"),
        )
        if ver_spec
        else None
    )
    agg = spec.get("aggregate", {})
    ven = spec.get("vendor", {})
    inp = spec.get("input", {})
    tr = spec.get("trace", {})
    return emit_decision_record(
        surface=surface,
        actor=actor,
        gate=gate,
        verifier=verifier,
        human_approved=spec.get("human_approval", {}).get("approved", False),
        aggregate=AggregateState(window_effect_ct=agg.get("window_effect_ct", 0)),
        vendor=VendorInfo(
            used=ven.get("used", False),
            attribution=ven.get("attribution"),
            scope_limited=ven.get("scope_limited", False),
        ),
        input_prov=InputProvenance(trusted=inp.get("trusted", True)),
        trace=TraceAnchor(
            append_only=tr.get("append_only", True),
            actor_chain_prev_hash=tr.get("actor_chain_prev_hash"),
            merkle_anchor=tr.get("merkle_anchor"),
        ),
        residual_error_bound=spec.get("residual_error_bound"),
        action_blocked=spec.get("action_blocked", False),
        escalation_approved=spec.get("escalation_approved", False),
        action_id=spec.get("action", {}).get("id") or spec.get("id"),
    )


def main(argv: Optional[list[str]] = None) -> int:
    """Run the emitter CLI.

    Exit codes: 0 record emitted; 2 bad input -- argparse usage error,
    unreadable/malformed/wrong-shape bundle, a bundle lattice entry or
    default CT that derive_ct reaches in the wrong shape, or an
    unreadable/non-UTF-8/malformed/wrong-shape spec, or a spec value too
    deeply nested to serialise (one-line
    "EMITTER INPUT ERROR:" on stderr), or an emitted record that fails
    validate_emitted ("EMITTER VALIDATION FAILED:" on stderr).

    Inputs are checked in the original emitter's order: spec JSON, then
    the bundle, then the spec's keys, then derive_ct's lattice reads.
    """
    p = argparse.ArgumentParser(description="LAAS v1.1 decision-record emitter")
    p.add_argument("-i", "--input", help="effect-surface spec JSON (default stdin)")
    p.add_argument("-b", "--bundle", help="data.json bundle to load the lattice from")
    p.add_argument("-o", "--output", help="write record here (default stdout)")
    args = p.parse_args(argv)

    try:
        raw_spec = _read_spec(args.input)
        gate = GateContext.from_bundle(args.bundle) if args.bundle else GateContext()
        spec = _check_spec(raw_spec, f"spec {args.input or '<stdin>'}")
        record = _build_from_spec(spec, gate)
    except EmitterInputError as e:
        sys.stderr.write(f"EMITTER INPUT ERROR: {e}\n")
        return 2
    problems = validate_emitted(record)
    if problems:
        sys.stderr.write(
            "EMITTER VALIDATION FAILED:\n  " + "\n  ".join(problems) + "\n"
        )
        return 2
    try:
        out = json.dumps(record, indent=2)
    except RecursionError as e:
        # Only spec values sit deeper in the record than in their input
        # (effect_surface.tool, top-level id), so the spec is the cause.
        source = args.input or "<stdin>"
        sys.stderr.write(
            f"EMITTER INPUT ERROR: spec {source}: "
            f"too deeply nested to serialise the record: {e}\n"
        )
        return 2
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
    else:
        sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
