# LAAS runtime-action conformance policy.
#
# package kellerai.laas.actions
#
# Evaluates ONE gate-produced decision record (input) against the obligation
# bundle (data.laas, from data.json). The gate -- not the agent -- supplies the
# observed effect surface and the assigned tier; this policy checks that the
# assignment, verification, and enforcement are correct.
#
# Entry points:
#   data.kellerai.laas.actions.violations  -> set of {obligation, severity, msg}
#   data.kellerai.laas.actions.summary     -> {expected_ct, effective_ct, errors, warnings, compliant}
#   data.kellerai.laas.actions.compliant   -> bool  (no error-severity violations)
#   data.kellerai.laas.actions.error_ids   -> set of strings  (obligation IDs with error-severity violations)
#
# Design note: every check derives the tier from the OBSERVED effect surface
# (LAAS v1.1 Sec 6.1 / finding 4.1). A self-reported tier can never lower it.

package kellerai.laas.actions

import rego.v1

cfg := data.laas

# ---------------------------------------------------------------------------
# Consequence Tier derivation (gate-side lattice; v1.1 Sec 6.1)
# Default-to-highest when the surface is undetermined (v1.1 Sec 6.2 / finding 3.3).
# ---------------------------------------------------------------------------

default expected_ct := 4

# read-only / sandboxed -> CT0
expected_ct := 0 if {
	not input.action.effect_surface.external_effect
}

# external effect with a fully-known surface -> lattice max of the three axes
expected_ct := m if {
	input.action.effect_surface.external_effect
	s := input.action.effect_surface
	rev := cfg.tier_lattice.reversibility[s.reversibility]
	scp := cfg.tier_lattice.scope[s.scope]
	con := cfg.tier_lattice.consequence[s.consequence]
	m := max([rev, scp, con])
}

# tier the gate must actually enforce: never below the cumulative window (v1.1 Sec 6.4)
effective_ct := max([input.gate.assigned_ct, _agg_ct])

_agg_ct := object.get(input, ["aggregate", "window_effect_ct"], 0)

# residual-escape tolerance for the effective tier, if one is defined
residual_tolerance := t if {
	t := cfg.escape_rate_tolerance_by_ct[sprintf("%d", [effective_ct])]
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

blocked if input.action_blocked == true

requires_independent_verification if effective_ct >= cfg.independent_verification_floor_ct

verifier_passed if input.verifier.verdict == "pass"

human_approved if input.human_approval.approved == true

vendor_ok if {
	input.vendor.attribution != null
	input.vendor.scope_limited == true
}

# Independence (v1.1 Sec 7.3 / finding 5.1): a different *kind* of checker,
# a distinct AND de-correlated model lineage, or a human.
independence_ok if input.verifier.type == "deterministic"

independence_ok if input.verifier.type == "human"

independence_ok if {
	input.verifier.type == "model"
	input.verifier.model_lineage != input.action.actor_model_lineage
	input.verifier.error_correlation <= cfg.max_error_correlation
}

obl(id, msg) := {"obligation": id, "severity": _severity(id), "msg": msg}

_severity(id) := s if {
	some o in cfg.obligations
	o.id == id
	s := o.severity
}

# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

# TIER-001: the gate-assigned tier must be at least the lattice-derived tier.
violations contains obl(
	"LAAS-OBL-TIER-001",
	sprintf("gate assigned_ct %d is below lattice-derived ct %d", [input.gate.assigned_ct, expected_ct]),
) if {
	input.gate.assigned_ct < expected_ct
}

# SELF-001 (warning): a self-reported tier below the gate tier is flagged; the gate prevails.
violations contains obl(
	"LAAS-OBL-SELF-001",
	sprintf("self_reported_ct %d is below gate ct %d (gate prevails)", [input.action.self_reported_ct, input.gate.assigned_ct]),
) if {
	input.action.self_reported_ct < input.gate.assigned_ct
}

# ENF-001: enforcement-plane integrity (v1.1 Sec 7.7 / finding 5.2).
violations contains obl("LAAS-OBL-ENF-001", "policy bundle is not signed") if {
	cfg.require_bundle_signed
	not input.gate.bundle_signed
}

violations contains obl("LAAS-OBL-ENF-001", "gate is not out-of-process") if {
	cfg.require_out_of_process_gate
	not input.gate.out_of_process
}

# TRC-001: append-only chained decision trace (v1.1 Sec 7.4).
violations contains obl("LAAS-OBL-TRC-001", "decision trace is not append-only") if {
	not input.trace.append_only
}

# AGG-001: the assigned tier must not be below the cumulative window (v1.1 Sec 6.4 / finding 4.3).
violations contains obl(
	"LAAS-OBL-AGG-001",
	sprintf("assigned_ct %d is below cumulative-window ct %d (structuring guard)", [input.gate.assigned_ct, _agg_ct]),
) if {
	input.gate.assigned_ct < _agg_ct
}

# INP-001: untrusted input must raise the tier to the floor, or be blocked (v1.1 Sec 8.3 / finding 4.5).
violations contains obl(
	"LAAS-OBL-INP-001",
	sprintf("untrusted input requires ct>=%d or a block", [cfg.untrusted_input_min_ct]),
) if {
	input.input.trusted == false
	effective_ct < cfg.untrusted_input_min_ct
	not blocked
}

# VEN-001: vendor dependencies need attribution + scope limits (v1.1 Sec 8.2 / finding 4.4).
violations contains obl("LAAS-OBL-VEN-001", "vendor dependency lacks attribution or scope limit") if {
	input.vendor.used == true
	not vendor_ok
}

# IRR-001: CT>=3 requires a passing independent pre-commit verifier, unless blocked (v1.1 Sec 7.1).
violations contains obl("LAAS-OBL-IRR-001", "CT>=3 action without a passing pre-commit verifier and not blocked") if {
	requires_independent_verification
	not blocked
	not verifier_passed
}

# IND-001: that verifier must be independent (v1.1 Sec 7.3 / finding 5.1).
violations contains obl("LAAS-OBL-IND-001", "verifier is not independent (same lineage or error-correlation too high)") if {
	requires_independent_verification
	not blocked
	verifier_passed
	not independence_ok
}

# VQ-001: that verifier must be qualified (v1.1 Sec 7.5 / finding 4.2).
violations contains obl("LAAS-OBL-VQ-001", "verifier is not qualified") if {
	requires_independent_verification
	not blocked
	verifier_passed
	not input.verifier.qualified
}

# HUM-001: CT4 also requires human approval, unless blocked (v1.1 Sec 6.3).
violations contains obl("LAAS-OBL-HUM-001", "CT4 action without human approval and not blocked") if {
	effective_ct >= cfg.human_approval_floor_ct
	not blocked
	not human_approved
}

# RES-001: the Bucket-B residual escape rate must be within tolerance (v1.1 Sec 5).
violations contains obl(
	"LAAS-OBL-RES-001",
	sprintf("residual escape rate %v exceeds tolerance %v for ct %d", [input.residual_error_bound, residual_tolerance, effective_ct]),
) if {
	# both sides are undefined-safe: if no tolerance exists for this tier, or no
	# residual bound was supplied (pure Bucket A), the comparison is undefined and
	# this violation simply does not fire.
	input.residual_error_bound > residual_tolerance
}

# ---------------------------------------------------------------------------
# Roll-ups
# ---------------------------------------------------------------------------

error_violations contains v if {
	some v in violations
	v.severity == "error"
}

warning_violations contains v if {
	some v in violations
	v.severity == "warning"
}

error_ids := {v.obligation | some v in error_violations}

default compliant := false

compliant if count(error_violations) == 0

summary := {
	"bundle": cfg.bundle_id,
	"expected_ct": expected_ct,
	"effective_ct": effective_ct,
	"errors": count(error_violations),
	"warnings": count(warning_violations),
	"compliant": compliant,
}
