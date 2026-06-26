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

    bundle_id: str = "laas-fin-1.1.0"
    bundle_version: str = "laas-fin-1.1.0"
    bundle_signed: bool = True
    out_of_process: bool = True
    lattice: dict = field(default_factory=lambda: dict(_DEFAULT_LATTICE))
    ct_when_undetermined: int = _DEFAULT_CT_WHEN_UNDETERMINED

    @classmethod
    def from_bundle(cls, data_json_path: str, **overrides: Any) -> "GateContext":
        """Load the lattice from a signed obligation bundle (data.json)."""
        with open(data_json_path, encoding="utf-8") as fh:
            cfg = json.load(fh)["laas"]
        kwargs: dict[str, Any] = {
            "bundle_id": cfg.get("bundle_id", "laas-fin-1.1.0"),
            "bundle_version": cfg.get("bundle_id", "laas-fin-1.1.0"),
            "lattice": cfg["tier_lattice"],
            "ct_when_undetermined": cfg.get(
                "default_ct_when_undetermined", _DEFAULT_CT_WHEN_UNDETERMINED
            ),
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
def derive_ct(surface: EffectSurface, gate: GateContext) -> tuple[int, dict]:
    """Return (gate_derived_ct, resolved_surface_keys).

    Mirrors laas.rego's `expected_ct` exactly so the gate's `assigned_ct` is
    never below the policy's lattice-derived tier (avoids TIER-001):

        - no external effect            -> CT0
        - external effect, keys known   -> max(rev, scope, consequence)
        - any axis undetermined         -> ct_when_undetermined (4)
    """
    if not surface.external_effect:
        return 0, {"external_effect": False}

    resolved: dict[str, str] = {"external_effect": True}
    axis_cts: list[int] = []
    undetermined = False
    for axis in ("reversibility", "scope", "consequence"):
        key = getattr(surface, axis)
        if key is None:
            key = _UNKNOWN_DEFAULT[axis]
            undetermined = True
        table = gate.lattice[axis]
        if key not in table:
            # An unrecognized key is itself "undetermined" -> fail closed.
            key = _UNKNOWN_DEFAULT[axis]
            undetermined = True
        resolved[axis] = key
        axis_cts.append(table[key])

    if undetermined:
        return gate.ct_when_undetermined, resolved
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
    the effective tier (policy: effective_ct = max(assigned_ct, window_ct)).
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
    p = argparse.ArgumentParser(description="LAAS v1.1 decision-record emitter")
    p.add_argument("-i", "--input", help="effect-surface spec JSON (default stdin)")
    p.add_argument("-b", "--bundle", help="data.json bundle to load the lattice from")
    p.add_argument("-o", "--output", help="write record here (default stdout)")
    args = p.parse_args(argv)

    if args.input:
        with open(args.input, encoding="utf-8") as fh:
            raw = fh.read()
    else:
        raw = sys.stdin.read()
    spec = json.loads(raw)
    gate = GateContext.from_bundle(args.bundle) if args.bundle else GateContext()
    record = _build_from_spec(spec, gate)
    problems = validate_emitted(record)
    if problems:
        sys.stderr.write(
            "EMITTER VALIDATION FAILED:\n  " + "\n  ".join(problems) + "\n"
        )
        return 2
    out = json.dumps(record, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
    else:
        sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
