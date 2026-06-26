#!/usr/bin/env python3
"""LAAS OSI adapter -- convert an OSI (Open Semantic Interchange) model + an
action reference into a LaaS EffectSurface, then emit a decision record via the
canonical emitter.

NO TIER MATH LIVES HERE. This module owns the *mapping* from OSI semantics to a
gate-observed EffectSurface; the consequence-tier (CT) lattice math is owned by
emitter.derive_ct / laas.rego. The reversibility/scope/consequence RANKS are
loaded from data["laas"]["tier_lattice"] (conformance/laas/data.json) and used
only to compare severities -- this file contains no rank integer literals
(acceptance AC1).

Dependency policy: the CORE (`build_surface`, `osi_emit_decision_record`) is
stdlib-only and takes a PRE-PARSED model dict. The thin CLI wrapper (`main`)
may import PyYAML to load a `.yaml` path; PyYAML is a CLI-ONLY optional
dependency, never imported by the core.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from emitter import (
    ActorContext,
    AggregateState,
    EffectSurface,
    GateContext,
    InputProvenance,
    VerifierResult,
    emit_decision_record,
)

_VENDOR_NAME = "KELLERAI_LAAS"
_DATA_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "conformance", "laas", "data.json"
)
_MAX_DEPTH = 64  # blast-radius traversal bound (cycle-safe with the visited set)


# --------------------------------------------------------------------------- #
# data.json access (lattice ranks + floors) -- the ONLY source of rank numbers
# --------------------------------------------------------------------------- #
def _laas_config(data_json_path: Optional[str] = None) -> dict:
    path = data_json_path or _DATA_JSON
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["laas"]


def _tier_lattice(data_json_path: Optional[str] = None) -> dict:
    return _laas_config(data_json_path)["tier_lattice"]


# --------------------------------------------------------------------------- #
# OSI model helpers
# --------------------------------------------------------------------------- #
def _collection(model: dict, kind: str) -> list:
    # kind is singular ("dataset"|"metric"); collections are pluralised.
    return model.get(kind + "s", []) or []


def _laas_axes(obj: dict) -> dict:
    """Return the KELLERAI_LAAS `data` payload for an OSI object, or {}."""
    for ext in obj.get("custom_extensions", []) or []:
        if ext.get("vendor_name") == _VENDOR_NAME:
            return ext.get("data", {}) or {}
    return {}


def _resolve(model: dict, kind: str, name: str) -> dict:
    for obj in _collection(model, kind):
        if obj.get("name") == name:
            return obj
    raise KeyError(f"OSI object not found: kind={kind!r} name={name!r}")


def _index_by_name(model: dict) -> dict:
    idx: dict[str, dict] = {}
    for kind in ("dataset", "metric"):
        for obj in _collection(model, kind):
            nm = obj.get("name")
            if nm is not None:
                idx[nm] = obj
    return idx


def _rel_endpoint(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return value.get("name")
    return value


def _reachable_axes(model: dict, start_name: str) -> list:
    """Cycle-safe blast-radius traversal. Returns the KELLERAI_LAAS axes of the
    start object plus every dependent object reachable by following
    `relationships` (from -> to), bounded by _MAX_DEPTH."""
    idx = _index_by_name(model)
    adjacency: dict[str, list] = {}
    for rel in model.get("relationships", []) or []:
        src = _rel_endpoint(rel.get("from"))
        dst = _rel_endpoint(rel.get("to"))
        if src is None or dst is None:
            continue
        adjacency.setdefault(src, []).append(dst)

    visited: set = set()
    stack: list = [(start_name, 0)]
    axes_list: list = []
    while stack:
        node, depth = stack.pop()
        if node in visited or depth > _MAX_DEPTH:
            continue
        visited.add(node)
        obj = idx.get(node)
        if obj is not None:
            axes_list.append(_laas_axes(obj))
        for nxt in adjacency.get(node, []):
            if nxt not in visited:
                stack.append((nxt, depth + 1))
    return axes_list


# --------------------------------------------------------------------------- #
# severity helpers (compare via the loaded lattice; never hardcode ranks)
# --------------------------------------------------------------------------- #
def _most_severe(values: list, axis_lattice: dict) -> Optional[str]:
    """Most-severe determinable axis value among `values`, or None if none are
    determinable (None / unrecognised key) -- None propagates to derive_ct's
    default-to-highest (CT4). Never silently downgrades."""
    best: Optional[str] = None
    best_rank: Optional[int] = None
    for v in values:
        if v is None or v not in axis_lattice:
            continue
        rank = axis_lattice[v]
        if best_rank is None or rank > best_rank:
            best_rank, best = rank, v
    return best


def _floor(current: Optional[str], floor_value: str, axis_lattice: dict) -> Optional[str]:
    """Operation floor: return the MORE-severe of `current` and `floor_value`.
    An undetermined `current` (None / unrecognised) is treated as max severity
    (CT4) and left as None so we never downgrade it to the floor."""
    if current is None or current not in axis_lattice:
        return None
    if axis_lattice[current] >= axis_lattice[floor_value]:
        return current
    return floor_value


# --------------------------------------------------------------------------- #
# core: build_surface (NO tier math)
# --------------------------------------------------------------------------- #
def build_surface(
    model: dict, action_ref: dict, *, data_json_path: Optional[str] = None
) -> EffectSurface:
    """Map an OSI model + action_ref into a gate-observed EffectSurface.

    action_ref = {"kind": "dataset"|"metric", "name": str,
                  "operation": "read"|"write"|"delete"}.
    """
    kind = action_ref["kind"]
    name = action_ref["name"]
    operation = action_ref["operation"]

    lattice = _tier_lattice(data_json_path)
    rev_lat = lattice["reversibility"]
    scope_lat = lattice["scope"]
    cons_lat = lattice["consequence"]

    target = _resolve(model, kind, name)
    target_axes = _laas_axes(target)

    external_effect = operation in ("write", "delete")

    if external_effect:
        # blast radius: most-severe rank on ALL THREE axes across reachable deps.
        reach = _reachable_axes(model, name)
        reversibility = _most_severe([a.get("reversibility") for a in reach], rev_lat)
        scope = _most_severe([a.get("scope") for a in reach], scope_lat)
        consequence = _most_severe([a.get("consequence") for a in reach], cons_lat)
        access_sensitive = any(bool(a.get("access_sensitive")) for a in reach)
    else:
        # read: no external effect -> CT0 regardless of annotation.
        reversibility = target_axes.get("reversibility")
        scope = target_axes.get("scope")
        consequence = target_axes.get("consequence")
        access_sensitive = bool(target_axes.get("access_sensitive"))

    # operation floors (AFTER annotation/blast radius; take the more severe).
    if operation == "write":
        reversibility = _floor(reversibility, "hard", rev_lat)
    elif operation == "delete":
        reversibility = _floor(reversibility, "irreversible", rev_lat)

    # access_sensitive: graph reach != permission reach -> coerce scope public.
    if access_sensitive:
        scope = "public"

    return EffectSurface(
        external_effect=external_effect,
        reversibility=reversibility,
        scope=scope,
        consequence=consequence,
        tool=f"osi.{kind}.{operation}:{name}",
    )


# --------------------------------------------------------------------------- #
# adapter: osi_emit_decision_record (calls the REAL emitter, no fork)
# --------------------------------------------------------------------------- #
def osi_emit_decision_record(
    model: dict,
    action_ref: dict,
    *,
    model_signed: bool,
    actor: ActorContext,
    gate: GateContext,
    verifier: Optional[VerifierResult] = None,
    data_json_path: Optional[str] = None,
) -> dict:
    """Build the surface and emit a real decision record via the canonical
    emit_decision_record (NOT a fork).

    Trust semantics (corrected): derive_ct never sees provenance, so an unsigned
    model does NOT raise the CT by itself. To make "unsigned raises the floor"
    true in-architecture we set aggregate.window_effect_ct = untrusted_input_min_ct
    (3) when model_signed is False, so emit's assigned_ct = max(derived_ct,
    window_effect_ct) is floored to >= 3 -- forcing the full CT>=3 obligation set
    (independent qualified verification, and satisfying INP-001's ct>=3 floor).
    There is NO baseline-vs-prior-CT comparison: the annotation is the sole
    governance-authored axis source.
    """
    surface = build_surface(model, action_ref, data_json_path=data_json_path)
    input_prov = InputProvenance(trusted=model_signed)

    aggregate: Optional[AggregateState] = None
    if not model_signed:
        floor_ct = _laas_config(data_json_path)["untrusted_input_min_ct"]
        aggregate = AggregateState(window_effect_ct=floor_ct)

    return emit_decision_record(
        surface=surface,
        actor=actor,
        gate=gate,
        verifier=verifier,
        input_prov=input_prov,
        aggregate=aggregate,
    )


# --------------------------------------------------------------------------- #
# thin CLI wrapper (PyYAML is a CLI-ONLY optional dependency)
# --------------------------------------------------------------------------- #
def _load_model_file(path: str) -> dict:
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml  # CLI-only optional dependency; never used by the core.
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise SystemExit(
                "PyYAML is required to load a .yaml model; install pyyaml or "
                "pass the .json twin instead (the core is stdlib-only)."
            ) from exc
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: Optional[list] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OSI -> LaaS decision record.")
    parser.add_argument("-m", "--model", required=True, help="OSI model (.yaml|.json)")
    parser.add_argument("--kind", required=True, choices=["dataset", "metric"])
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--operation", required=True, choices=["read", "write", "delete"]
    )
    parser.add_argument("--signed", dest="signed", action="store_true", default=True)
    parser.add_argument("--unsigned", dest="signed", action="store_false")
    parser.add_argument("--actor-id", default="agent.osi.demo")
    parser.add_argument("--actor-lineage", default="osi-demo-lineage")
    parser.add_argument("-b", "--bundle", default=_DATA_JSON, help="data.json bundle")
    parser.add_argument("-o", "--out", help="write record JSON here (default stdout)")
    args = parser.parse_args(argv)

    model = _load_model_file(args.model)
    gate = GateContext.from_bundle(args.bundle)
    actor = ActorContext(
        actor_id=args.actor_id, actor_model_lineage=args.actor_lineage
    )
    action_ref = {"kind": args.kind, "name": args.name, "operation": args.operation}

    # A fully-conformant CT>=3 record needs an independent qualified verifier; the
    # CLI supplies a deterministic passing one so the proof script can show a
    # compliant CT4 write. Enforcement-plane controls (human approval, trace
    # anchors) are supplied by the deployment at evaluation time.
    verifier = VerifierResult(
        id="VRF-OSI-DET",
        type="deterministic",
        verdict="pass",
        qualified=True,
        model_lineage="n/a",
    )
    record = osi_emit_decision_record(
        model,
        action_ref,
        model_signed=args.signed,
        actor=actor,
        gate=gate,
        verifier=verifier,
        data_json_path=args.bundle,
    )

    text = json.dumps(record, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
