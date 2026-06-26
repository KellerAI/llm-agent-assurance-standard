# opa test suite for kellerai.laas.actions
# Run: opa test conformance/laas/ -v
#
# Each test injects a hermetic config (_cfg) and a decision record (input),
# then asserts on summary.compliant and the set of error obligation IDs.

package kellerai.laas.actions

import rego.v1

# --------------------------- hermetic config ---------------------------

_cfg := {
	"version": "1.1.0",
	"bundle_id": "laas-test-1.1.0",
	"tier_lattice": {
		"reversibility": {"reversible": 1, "hard": 3, "irreversible": 4, "none": 4},
		"scope": {"single": 1, "multi": 2, "org": 3, "public": 4},
		"consequence": {"none": 0, "low": 1, "material": 3, "high": 4},
	},
	"default_ct_when_undetermined": 4,
	"independent_verification_floor_ct": 3,
	"human_approval_floor_ct": 4,
	"max_error_correlation": 0.2,
	"escape_rate_tolerance_by_ct": {"2": 0.02, "3": 0.005, "4": 0},
	"require_bundle_signed": true,
	"require_out_of_process_gate": true,
	"untrusted_input_min_ct": 3,
	"obligations": [
		{"id": "LAAS-OBL-TIER-001", "severity": "error"},
		{"id": "LAAS-OBL-SELF-001", "severity": "warning"},
		{"id": "LAAS-OBL-ENF-001", "severity": "error"},
		{"id": "LAAS-OBL-TRC-001", "severity": "error"},
		{"id": "LAAS-OBL-AGG-001", "severity": "error"},
		{"id": "LAAS-OBL-INP-001", "severity": "error"},
		{"id": "LAAS-OBL-VEN-001", "severity": "error"},
		{"id": "LAAS-OBL-IRR-001", "severity": "error"},
		{"id": "LAAS-OBL-IND-001", "severity": "error"},
		{"id": "LAAS-OBL-VQ-001", "severity": "error"},
		{"id": "LAAS-OBL-RES-001", "severity": "error"},
		{"id": "LAAS-OBL-HUM-001", "severity": "error"},
	],
}

# --------------------------- reusable fixtures ---------------------------

_surface_ct4 := {"external_effect": true, "reversibility": "irreversible", "scope": "public", "consequence": "high"}

_surface_ct3 := {"external_effect": true, "reversibility": "hard", "scope": "single", "consequence": "material"}

_surface_ct1 := {"external_effect": true, "reversibility": "reversible", "scope": "single", "consequence": "low"}

_surface_ro := {"external_effect": false}

_gate(ct) := {"assigned_ct": ct, "bundle_version": "laas-test-1.1.0", "bundle_signed": true, "out_of_process": true}

_verifier_det := {"id": "v", "type": "deterministic", "model_lineage": "na", "qualified": true, "verdict": "pass"}

_trace := {"append_only": true, "actor_chain_prev_hash": "h", "merkle_anchor": "m"}

# A fully-conformant CT4 decision record (gate-derived CT4, deterministic verifier, human-approved).
_base_ct4 := {
	"action": {"id": "a", "actor_model_lineage": "L", "self_reported_ct": 4, "effect_surface": _surface_ct4},
	"gate": _gate(4),
	"verifier": _verifier_det,
	"residual_error_bound": 0,
	"human_approval": {"approved": true},
	"aggregate": {"window_effect_ct": 4},
	"input": {"trusted": true},
	"vendor": {"used": false},
	"trace": _trace,
	"action_blocked": false,
	"escalation_approved": true,
}

# --------------------------- happy paths ---------------------------

test_pass_ct4_compliant if {
	s := summary with input as _base_ct4 with data.laas as _cfg
	s.compliant == true
	s.errors == 0
	s.expected_ct == 4
}

test_block_ct4_compliant if {
	# CT4 action, verifier abstains, but the action is blocked -> conformant via the block path.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/verifier/verdict", "value": "abstain"},
		{"op": "replace", "path": "/action_blocked", "value": true},
	])
	s := summary with input as inp with data.laas as _cfg
	s.compliant == true
}

test_pass_ct0_readonly if {
	inp := {
		"action": {"id": "a", "actor_model_lineage": "L", "self_reported_ct": 0, "effect_surface": _surface_ro},
		"gate": _gate(0),
		"input": {"trusted": true},
		"vendor": {"used": false},
		"trace": _trace,
		"action_blocked": false,
	}
	s := summary with input as inp with data.laas as _cfg
	s.expected_ct == 0
	s.compliant == true
}

# --------------------------- the gameability case (finding 4.1) ---------------------------

test_fail_gate_underclassifies if {
	# Effect surface implies CT4, but the gate assigned CT1 -> TIER-001 error.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/gate", "value": _gate(1)},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 1},
		{"op": "replace", "path": "/action/self_reported_ct", "value": 1},
	])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-TIER-001" in ids
	not compliant with input as inp with data.laas as _cfg
}

test_warn_self_underreport_still_compliant if {
	# Gate tier is correct (CT4); agent self-reported CT1 -> SELF-001 WARNING only, still compliant.
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/action/self_reported_ct", "value": 1}])
	s := summary with input as inp with data.laas as _cfg
	s.warnings >= 1
	s.compliant == true
}

# --------------------------- verifier obligations (CT3) ---------------------------

test_fail_no_independence if {
	# CT3 model verifier with the SAME lineage as the actor -> IND-001.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/action/effect_surface", "value": _surface_ct3},
		{"op": "replace", "path": "/gate", "value": _gate(3)},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 3},
		{"op": "replace", "path": "/action/self_reported_ct", "value": 3},
		{"op": "replace", "path": "/verifier", "value": {"id": "v", "type": "model", "model_lineage": "L", "qualified": true, "error_correlation": 0.0, "verdict": "pass"}},
	])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-IND-001" in ids
}

test_fail_correlated_verifier if {
	# CT3 model verifier, distinct lineage but error-correlation 0.5 > 0.2 -> IND-001.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/action/effect_surface", "value": _surface_ct3},
		{"op": "replace", "path": "/gate", "value": _gate(3)},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 3},
		{"op": "replace", "path": "/action/self_reported_ct", "value": 3},
		{"op": "replace", "path": "/verifier", "value": {"id": "v", "type": "model", "model_lineage": "M", "qualified": true, "error_correlation": 0.5, "verdict": "pass"}},
	])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-IND-001" in ids
}

test_fail_unqualified_verifier if {
	# CT3, deterministic verifier (independent) but not qualified -> VQ-001.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/action/effect_surface", "value": _surface_ct3},
		{"op": "replace", "path": "/gate", "value": _gate(3)},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 3},
		{"op": "replace", "path": "/action/self_reported_ct", "value": 3},
		{"op": "replace", "path": "/verifier/qualified", "value": false},
	])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-VQ-001" in ids
}

# --------------------------- residual escape rate (Bucket B) ---------------------------

test_fail_residual_exceeds if {
	# CT3 tolerance is 0.005; bound 0.01 -> RES-001.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/action/effect_surface", "value": _surface_ct3},
		{"op": "replace", "path": "/gate", "value": _gate(3)},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 3},
		{"op": "replace", "path": "/action/self_reported_ct", "value": 3},
		{"op": "replace", "path": "/residual_error_bound", "value": 0.01},
	])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-RES-001" in ids
}

# --------------------------- enforcement plane (finding 5.2) ---------------------------

test_fail_enforcement_unsigned if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/gate/bundle_signed", "value": false}])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-ENF-001" in ids
	not compliant with input as inp with data.laas as _cfg
}

test_fail_in_process_gate if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/gate/out_of_process", "value": false}])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-ENF-001" in ids
}

test_fail_trace_not_append_only if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/trace/append_only", "value": false}])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-TRC-001" in ids
}

# --------------------------- aggregation / structuring (finding 4.3) ---------------------------

test_fail_aggregate_retier if {
	# Each action looks CT1, but the cumulative window is CT4 -> AGG-001 (structuring guard).
	# Verifier + human approval are valid so AGG-001 is the only error.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/action/effect_surface", "value": _surface_ct1},
		{"op": "replace", "path": "/gate", "value": _gate(1)},
		{"op": "replace", "path": "/action/self_reported_ct", "value": 1},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 4},
	])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-AGG-001" in ids
}

# --------------------------- vendor / supply chain (finding 4.4) ---------------------------

test_fail_vendor_no_attribution if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/vendor", "value": {"used": true, "attribution": null, "scope_limited": false}}])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-VEN-001" in ids
}

# --------------------------- untrusted input / injection (finding 4.5) ---------------------------

test_fail_untrusted_input_low_ct if {
	# Untrusted input but the action is only CT1 and not blocked -> INP-001.
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/action/effect_surface", "value": _surface_ct1},
		{"op": "replace", "path": "/gate", "value": _gate(1)},
		{"op": "replace", "path": "/action/self_reported_ct", "value": 1},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 1},
		{"op": "replace", "path": "/input/trusted", "value": false},
	])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-INP-001" in ids
}

# --------------------------------------------------------------------------- #
# OSI adapter golden cases (scripts/laas/osi_to_surface.py, finding: OSI->LaaS)
#
# _osi_ct4 is the VERBATIM output of:
#   python3 scripts/laas/osi_to_surface.py -m scripts/laas/osi/example.semantic.json \
#     --kind metric --name net_settlement_amount --operation write --signed
# (a CT4 net_settlement_amount write). Regenerate with that command if the
# adapter or the example model changes.
# --------------------------------------------------------------------------- #

_osi_ct4 := {
	"action": {
		"id": "act_unknown",
		"actor_id": "agent.osi.demo",
		"actor_model_lineage": "osi-demo-lineage",
		"self_reported_ct": 4,
		"effect_surface": {
			"external_effect": true,
			"tool": "osi.metric.write:net_settlement_amount",
			"reversibility": "irreversible",
			"scope": "org",
			"consequence": "high",
		},
	},
	"gate": {"assigned_ct": 4, "bundle_version": "laas-fin-1.1.0", "bundle_signed": true, "out_of_process": true},
	"aggregate": {"window_effect_ct": 0},
	"human_approval": {"approved": false},
	"vendor": {"used": false, "attribution": null, "scope_limited": false},
	"input": {"trusted": true},
	"trace": {"append_only": true, "actor_chain_prev_hash": null, "merkle_anchor": null},
	"residual_error_bound": null,
	"action_blocked": false,
	"escalation_approved": false,
	"verifier": {"id": "VRF-OSI-DET", "type": "deterministic", "model_lineage": "n/a", "qualified": true, "verdict": "pass"},
}

# CT4 write, full enforcement controls (human approval + append-only trace anchors) -> compliant.
test_osi_ct4_full_controls_compliant if {
	inp := json.patch(_osi_ct4, [
		{"op": "replace", "path": "/human_approval/approved", "value": true},
		{"op": "replace", "path": "/trace", "value": {"append_only": true, "actor_chain_prev_hash": "sha256:osi", "merkle_anchor": "sha256:osi"}},
	])
	s := summary with input as inp with data.laas as _cfg
	s.expected_ct == 4
	s.compliant == true
	s.errors == 0
}

# CT4 write committed (not blocked), enforcement controls absent -> non-compliant (HUM-001).
test_osi_ct4_controls_absent_committed_noncompliant if {
	ids := error_ids with input as _osi_ct4 with data.laas as _cfg
	"LAAS-OBL-HUM-001" in ids
	not compliant with input as _osi_ct4 with data.laas as _cfg
}

# CT4 write blocked -> compliant via the block path.
test_osi_ct4_blocked_compliant if {
	inp := json.patch(_osi_ct4, [{"op": "replace", "path": "/action_blocked", "value": true}])
	compliant with input as inp with data.laas as _cfg
}

# Unsigned OSI model / untrusted input: INP-001 drives a block when the untrusted
# action is low-CT and not blocked; blocking clears it. Asserts the rego behavior,
# NOT a derive_ct CT change. (The adapter's unsigned floor sets
# window_effect_ct=untrusted_input_min_ct so a real unsigned action is raised to
# >=CT3 and satisfies INP-001's ct>=3 floor; here we exhibit the underlying block.)
_osi_untrusted_lowct := {
	"action": {
		"id": "act_unknown",
		"actor_id": "agent.osi.demo",
		"actor_model_lineage": "osi-demo-lineage",
		"self_reported_ct": 1,
		"effect_surface": {"external_effect": true, "tool": "osi.dataset.write:customers", "reversibility": "reversible", "scope": "single", "consequence": "low"},
	},
	"gate": {"assigned_ct": 1, "bundle_version": "laas-fin-1.1.0", "bundle_signed": true, "out_of_process": true},
	"aggregate": {"window_effect_ct": 1},
	"human_approval": {"approved": true},
	"vendor": {"used": false, "attribution": null, "scope_limited": false},
	"input": {"trusted": false},
	"trace": {"append_only": true, "actor_chain_prev_hash": "h", "merkle_anchor": "m"},
	"residual_error_bound": null,
	"action_blocked": false,
	"escalation_approved": false,
	"verifier": {"id": "VRF-OSI-DET", "type": "deterministic", "model_lineage": "n/a", "qualified": true, "verdict": "pass"},
}

test_osi_unsigned_inp001_block if {
	# untrusted + low CT + not blocked -> INP-001 fires.
	ids := error_ids with input as _osi_untrusted_lowct with data.laas as _cfg
	"LAAS-OBL-INP-001" in ids
	not compliant with input as _osi_untrusted_lowct with data.laas as _cfg

	# blocking clears the violation -> compliant via the block path.
	blocked := json.patch(_osi_untrusted_lowct, [{"op": "replace", "path": "/action_blocked", "value": true}])
	compliant with input as blocked with data.laas as _cfg
}
