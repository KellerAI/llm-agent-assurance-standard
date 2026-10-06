# opa test suite for kellerai.laas.actions
# Run: opa test conformance/laas/ -v
#
# Each test injects a hermetic config (_cfg) and a decision record (input),
# then asserts on summary.compliant and the set of error obligation IDs.

package kellerai.laas.actions

import rego.v1

# --------------------------- hermetic config ---------------------------

_cfg := {
	"version": "1.1.1",
	"bundle_id": "laas-test-1.1.1",
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

_gate(ct) := {"assigned_ct": ct, "bundle_version": "laas-test-1.1.1", "bundle_signed": true, "out_of_process": true}

_verifier_det := {"id": "v", "type": "deterministic", "model_lineage": "na", "qualified": true, "verdict": "pass"}

_trace := {"append_only": true, "actor_chain_prev_hash": "h", "merkle_anchor": "m"}

# A fully-conformant CT4 decision record (gate-derived CT4, deterministic verifier, human-approved).
_base_ct4 := {
	"action": {"id": "a", "actor_model_lineage": "L", "self_reported_ct": 4, "effect_surface": _surface_ct4},
	"gate": _gate(4),
	"verifier": _verifier_det,
	"residual_error_bound": 0,
	"evidence_refs": ["ev_test_0001"],
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
	"gate": {"assigned_ct": 4, "bundle_version": "laas-fin-1.1.2", "bundle_signed": true, "out_of_process": true},
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
	"gate": {"assigned_ct": 1, "bundle_version": "laas-fin-1.1.2", "bundle_signed": true, "out_of_process": true},
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

# --------------------------------------------------------------------------- #
# laas-yju rulings (TDD: written before the laas.rego change)
# --------------------------------------------------------------------------- #

_surface_ct2 := {"external_effect": true, "reversibility": "reversible", "scope": "multi", "consequence": "low"}

_verifier_model_indep := {"id": "v", "type": "model", "model_lineage": "M", "qualified": true, "error_correlation": 0.0, "verdict": "pass"}

_retier(ct, surface) := [
	{"op": "replace", "path": "/action/effect_surface", "value": surface},
	{"op": "replace", "path": "/gate", "value": _gate(ct)},
	{"op": "replace", "path": "/aggregate/window_effect_ct", "value": ct},
	{"op": "replace", "path": "/action/self_reported_ct", "value": ct},
]

# compliant CT2 record: deterministic verifier, bound 0.01 within tolerance 0.02, evidence present.
_base_ct2 := json.patch(_base_ct4, array.concat(_retier(2, _surface_ct2), [{"op": "replace", "path": "/residual_error_bound", "value": 0.01}]))

_has_msg(inp, id, m) if {
	vs := violations with input as inp with data.laas as _cfg
	some v in vs
	v.obligation == id
	v.msg == m
}

_has_msg_containing(inp, id, frag) if {
	vs := violations with input as inp with data.laas as _cfg
	some v in vs
	v.obligation == id
	contains(v.msg, frag)
}

# ---- SD-1: expected_ct is 0 only for external_effect == false (boolean) ----

test_sd1_effect_surface_absent_is_ct4 if {
	inp := json.patch(_base_ct4, [{"op": "remove", "path": "/action/effect_surface"}])
	ct := expected_ct with input as inp with data.laas as _cfg
	ct == 4
}

test_sd1_external_effect_null_is_ct4 if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/action/effect_surface", "value": {"external_effect": null}}])
	ct := expected_ct with input as inp with data.laas as _cfg
	ct == 4
}

test_sd1_external_effect_string_false_is_ct4 if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/action/effect_surface", "value": {"external_effect": "false"}}])
	ct := expected_ct with input as inp with data.laas as _cfg
	ct == 4
}

test_sd1_external_effect_string_false_full_surface_is_ct4 if {
	# non-boolean external_effect must not enter the lattice branch (would give CT1).
	surface := object.union(_surface_ct1, {"external_effect": "false"})
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/action/effect_surface", "value": surface}])
	ct := expected_ct with input as inp with data.laas as _cfg
	ct == 4
}

test_sd1_external_effect_null_full_surface_is_ct4 if {
	surface := object.union(_surface_ct1, {"external_effect": null})
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/action/effect_surface", "value": surface}])
	ct := expected_ct with input as inp with data.laas as _cfg
	ct == 4
}

test_sd1_external_effect_false_is_ct0 if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/action/effect_surface", "value": _surface_ro}])
	ct := expected_ct with input as inp with data.laas as _cfg
	ct == 0
}

# ---- SD-2: at CT4 a model-lineage verifier is never independent, even with human approval -> IND-001 ----

test_sd2_ct4_model_verifier_ind001 if {
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/verifier", "value": _verifier_model_indep}])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-IND-001" in ids
	not compliant with input as inp with data.laas as _cfg
}

test_sd2_ct3_model_verifier_no_ind001 if {
	inp := json.patch(_base_ct4, array.concat(_retier(3, _surface_ct3), [{"op": "replace", "path": "/verifier", "value": _verifier_model_indep}]))
	ids := error_ids with input as inp with data.laas as _cfg
	not "LAAS-OBL-IND-001" in ids
}

test_sd2_ct4_deterministic_no_ind001 if {
	ids := error_ids with input as _base_ct4 with data.laas as _cfg
	not "LAAS-OBL-IND-001" in ids
}

test_sd2_ct4_model_verifier_failed_noncompliant if {
	# not blocked (action_blocked false) -> IRR-001 fires.
	v := object.union(_verifier_model_indep, {"verdict": "fail"})
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/verifier", "value": v}])
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-IRR-001" in ids
	not compliant with input as inp with data.laas as _cfg
}

# ---- SD-3a: residual bound needs evidence_refs in the trace ----

_sd3a_msg := "residual_error_bound supplied at ct 2 without evidence_refs in the trace"

test_sd3a_bound_evidence_absent if {
	inp := json.patch(_base_ct2, [{"op": "remove", "path": "/evidence_refs"}])
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3a_msg)
}

test_sd3a_bound_evidence_empty if {
	inp := json.patch(_base_ct2, [{"op": "replace", "path": "/evidence_refs", "value": []}])
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3a_msg)
}

test_sd3a_bound_evidence_empty_string if {
	inp := json.patch(_base_ct2, [{"op": "replace", "path": "/evidence_refs", "value": [""]}])
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3a_msg)
}

test_sd3a_bound_with_evidence_no_res001 if {
	inp := json.patch(_base_ct2, [{"op": "replace", "path": "/evidence_refs", "value": ["ev1"]}])
	ids := error_ids with input as inp with data.laas as _cfg
	not "LAAS-OBL-RES-001" in ids
	compliant with input as inp with data.laas as _cfg
}

test_sd3a_blocked_ct4_no_evidence_message if {
	inp := json.patch(_base_ct4, [
		{"op": "remove", "path": "/evidence_refs"},
		{"op": "replace", "path": "/action_blocked", "value": true},
	])
	not _has_msg_containing(inp, "LAAS-OBL-RES-001", "without evidence_refs")
}

# ---- SD-3b: Bucket-B actions must supply a residual bound ----

_sd3b_msg := "Bucket-B action at ct 2 lacks a numeric residual_error_bound"

_ct2_nobound := json.patch(_base_ct2, [
	{"op": "remove", "path": "/residual_error_bound"},
	{"op": "remove", "path": "/evidence_refs"},
])

test_sd3b_ct2_model_verifier_no_bound if {
	inp := json.patch(_ct2_nobound, [{"op": "replace", "path": "/verifier", "value": _verifier_model_indep}])
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3b_msg)
}

test_sd3b_ct2_deterministic_no_bound_bucket_a if {
	not _has_msg_containing(_ct2_nobound, "LAAS-OBL-RES-001", "Bucket-B")
}

test_sd3b_ct1_no_res001 if {
	inp := json.patch(_base_ct4, array.concat(_retier(1, _surface_ct1), [
		{"op": "remove", "path": "/residual_error_bound"},
		{"op": "remove", "path": "/evidence_refs"},
	]))
	ids := error_ids with input as inp with data.laas as _cfg
	not "LAAS-OBL-RES-001" in ids
}

test_sd3b_ct2_deterministic_failed_no_bound if {
	# failed verifier does not set action_blocked -> not blocked -> Bucket B.
	inp := json.patch(_ct2_nobound, [{"op": "replace", "path": "/verifier/verdict", "value": "fail"}])
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3b_msg)
}

# ---- guard pins (mutation-tested against laas.rego:227-257) ----

_sd2_msg := "model-lineage verifier is not independent at CT4; a deterministic or human verifier is required"

test_sd2_guard_blocked_no_ind001 if {
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/verifier", "value": _verifier_model_indep},
		{"op": "replace", "path": "/action_blocked", "value": true},
	])
	not _has_msg(inp, "LAAS-OBL-IND-001", _sd2_msg)
}

test_sd2_guard_verifier_failed_no_ind001 if {
	v := object.union(_verifier_model_indep, {"verdict": "fail"})
	inp := json.patch(_base_ct4, [{"op": "replace", "path": "/verifier", "value": v}])
	not _has_msg(inp, "LAAS-OBL-IND-001", _sd2_msg)
}

test_sd3_guard_evidence_refs_not_array if {
	# a string alone does not pin is_array (every over a string is not satisfied);
	# a non-empty object with string values does.
	inp := json.patch(_base_ct2, [{"op": "replace", "path": "/evidence_refs", "value": {"k": "ev1"}}])
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3a_msg)
}

test_sd3_guard_evidence_refs_non_string_element if {
	inp := json.patch(_base_ct2, [{"op": "replace", "path": "/evidence_refs", "value": [1]}])
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3a_msg)
}

test_sd3_guard_ct1_bound_no_evidence_no_3a if {
	inp := json.patch(_base_ct4, array.concat(_retier(1, _surface_ct1), [
		{"op": "replace", "path": "/residual_error_bound", "value": 0.5},
		{"op": "remove", "path": "/evidence_refs"},
	]))
	not _has_msg_containing(inp, "LAAS-OBL-RES-001", "without evidence_refs")
}

test_sd3_guard_blocked_bucket_b_no_3b if {
	inp := json.patch(_ct2_nobound, [
		{"op": "replace", "path": "/verifier", "value": _verifier_model_indep},
		{"op": "replace", "path": "/action_blocked", "value": true},
	])
	not _has_msg_containing(inp, "LAAS-OBL-RES-001", "Bucket-B")
}

# --------------------------------------------------------------------------- #
# laas-szm rulings R1/R2 (TDD: written before the laas.rego change)
# A gate.assigned_ct that is not an integer in 0..4 is handled exactly like an
# absent one: the gate tier falls back to the lattice, effective_ct is
# max([expected_ct, _agg_ct]), and a single TIER-001 fires.
# --------------------------------------------------------------------------- #

# GATE-4 probe: CT4 surface, model verifier passed, no bound, no evidence, no assigned_ct.
_szm_probe := {
	"action": {"id": "act_7c31", "actor_model_lineage": "vendorX-llm-2026q1", "self_reported_ct": 4, "effect_surface": _surface_ct4},
	"gate": {"bundle_version": "laas-fin-1.1.2", "bundle_signed": true, "out_of_process": true},
	"verifier": {"id": "VRF-MODEL-PROBE", "type": "model", "model_lineage": "vendorY-llm-2026q2", "error_correlation": 0.1, "qualified": true, "verdict": "pass"},
	"human_approval": {"approved": false},
	"aggregate": {"window_effect_ct": 4},
	"input": {"trusted": true},
	"vendor": {"used": true, "attribution": "vendorX-llm-2026q1", "scope_limited": true},
	"trace": _trace,
	"action_blocked": false,
	"escalation_approved": false,
}

_szm_msg(ct) := sprintf("gate did not record an integer assigned_ct in 0..4; enforcing lattice ct %d", [ct])

_szm_with_ct(v) := json.patch(_szm_probe, [{"op": "add", "path": "/gate/assigned_ct", "value": v}])

_szm_tier_count(inp) := count({v |
	vs := violations with input as inp with data.laas as _cfg
	some v in vs
	v.obligation == "LAAS-OBL-TIER-001"
})

# invalid value -> exactly one TIER-001 carrying the fallback message, effective_ct 4.
_szm_invalid_single_fire(val) if {
	inp := _szm_with_ct(val)
	ct := effective_ct with input as inp with data.laas as _cfg
	ct == 4
	_szm_tier_count(inp) == 1
	_has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(4))
}

test_szm_probe_absent_assigned_ct_fails_closed if {
	ct := effective_ct with input as _szm_probe with data.laas as _cfg
	ct == 4
	ids := error_ids with input as _szm_probe with data.laas as _cfg
	"LAAS-OBL-TIER-001" in ids
	"LAAS-OBL-HUM-001" in ids
	"LAAS-OBL-IND-001" in ids
	"LAAS-OBL-RES-001" in ids
	_has_msg(_szm_probe, "LAAS-OBL-TIER-001", _szm_msg(4))
	s := summary with input as _szm_probe with data.laas as _cfg
	s.effective_ct == 4
	s.compliant == false
	not compliant with input as _szm_probe with data.laas as _cfg
}

test_szm_invalid_null_single_tier001 if _szm_invalid_single_fire(null)

test_szm_invalid_string_single_tier001 if _szm_invalid_single_fire("4")

test_szm_invalid_fraction_single_tier001 if _szm_invalid_single_fire(4.5)

test_szm_invalid_negative_single_tier001 if _szm_invalid_single_fire(-1)

test_szm_invalid_above_range_single_tier001 if _szm_invalid_single_fire(5)

test_szm_negative_no_below_lattice_message if {
	inp := _szm_with_ct(-1)
	_has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(4))
	not _has_msg(inp, "LAAS-OBL-TIER-001", "gate assigned_ct -1 is below lattice-derived ct 4")
}

test_szm_above_range_res001_fires if {
	inp := _szm_with_ct(5)
	ct := effective_ct with input as inp with data.laas as _cfg
	ct == 4
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-RES-001" in ids
}

test_szm_absent_aggregate_raises_lattice_ct2 if {
	inp := json.patch(_szm_probe, [{"op": "replace", "path": "/action/effect_surface", "value": _surface_ct2}])
	ct := effective_ct with input as inp with data.laas as _cfg
	ct == 4
	_has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(2))
	ids := error_ids with input as inp with data.laas as _cfg
	not "LAAS-OBL-AGG-001" in ids
}

test_szm_absent_low_tier_still_tier001 if {
	inp := json.patch(_base_ct4, [
		{"op": "remove", "path": "/gate/assigned_ct"},
		{"op": "replace", "path": "/action/effect_surface", "value": _surface_ro},
		{"op": "remove", "path": "/aggregate"},
	])
	ct := effective_ct with input as inp with data.laas as _cfg
	ct == 0
	_has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(0))
	not compliant with input as inp with data.laas as _cfg
}

test_szm_string_no_format_garbage if {
	inp := _szm_with_ct("4")
	vs := violations with input as inp with data.laas as _cfg
	_has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(4))
	count([v | some v in vs; contains(v.msg, "%!")]) == 0
}

# ---- regression pins: valid assigned_ct behaviour is unchanged ----

test_szm_regression_valid_ct4_compliant if {
	s := summary with input as _base_ct4 with data.laas as _cfg
	s.compliant == true
	s.effective_ct == 4
	ids := error_ids with input as _base_ct4 with data.laas as _cfg
	not "LAAS-OBL-TIER-001" in ids
}

test_szm_regression_valid_below_lattice_single_fire if {
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/gate", "value": _gate(2)},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 2},
	])
	_szm_tier_count(inp) == 1
	_has_msg(inp, "LAAS-OBL-TIER-001", "gate assigned_ct 2 is below lattice-derived ct 4")
	not _has_msg_containing(inp, "LAAS-OBL-TIER-001", "did not record")
}

test_szm_regression_valid_agg001 if {
	inp := json.patch(_base_ct4, array.concat(_retier(3, _surface_ct3), [{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 4}]))
	_has_msg(inp, "LAAS-OBL-AGG-001", "assigned_ct 3 is below cumulative-window ct 4 (structuring guard)")
}

# ---- mutation-survivor pins (SELF-001/AGG-001 with invalid input, integral check) ----

_szm_obl_count(inp, id) := count({v |
	vs := violations with input as inp with data.laas as _cfg
	some v in vs
	v.obligation == id
})

test_szm_self001_invalid_ct_no_garbage if {
	inp := json.patch(_szm_with_ct("4"), [{"op": "replace", "path": "/action/self_reported_ct", "value": 0}])
	_has_msg(inp, "LAAS-OBL-SELF-001", "self_reported_ct 0 is below gate ct 4 (gate prevails)")
}

test_szm_self001_string_ct_no_spurious_warning if {
	inp := _szm_with_ct("4")
	_szm_obl_count(inp, "LAAS-OBL-SELF-001") == 0
	_has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(4))
}

test_szm_null_ct_no_agg001 if {
	inp := _szm_with_ct(null)
	_szm_obl_count(inp, "LAAS-OBL-AGG-001") == 0
	ct := effective_ct with input as inp with data.laas as _cfg
	ct == 4
	_has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(4))
}

test_szm_invalid_fraction_in_range_single_tier001 if {
	_szm_invalid_single_fire(3.5)
	vs := violations with input as _szm_with_ct(3.5) with data.laas as _cfg
	count([v | some v in vs; contains(v.msg, "%!")]) == 0
}

# --------------------------------------------------------------------------- #
# laas-szm ruling R3 (TDD: written before the laas.rego change)
# residual_error_bound must be a number >= 0. A non-number or negative bound
# fires RES-001 with an explicit invalid-bound message and no "%!" garbage.
# Ruling R3a: null means absent, same as a missing key.
# Fixture: _base_ct2 (Bucket-A deterministic verifier, tolerance 0.02), so the
# Bucket-B "lacks a numeric residual_error_bound" rule cannot mask the result.
# --------------------------------------------------------------------------- #

_r3_phrase := "residual_error_bound must be a number >= 0"

_r3_with_bound(v) := json.patch(_base_ct2, [{"op": "replace", "path": "/residual_error_bound", "value": v}])

_r3_invalid(v) if {
	inp := _r3_with_bound(v)
	ids := error_ids with input as inp with data.laas as _cfg
	"LAAS-OBL-RES-001" in ids
	_has_msg_containing(inp, "LAAS-OBL-RES-001", _r3_phrase)
	vs := violations with input as inp with data.laas as _cfg
	count([v | some v in vs; contains(v.msg, "%!")]) == 0
	not compliant with input as inp with data.laas as _cfg
}

test_szm_r3_negative_bound_invalid if _r3_invalid(-0.01)

test_szm_r3_string_bound_invalid if _r3_invalid("0.01")

test_szm_r3_object_bound_invalid if _r3_invalid({})

test_szm_r3_array_bound_invalid if _r3_invalid([])

# ruling R3a: a null bound is absent, exactly like a missing key.
test_szm_r3_null_bound_is_absent if {
	inp := _r3_with_bound(null)
	absent := json.remove(_base_ct2, ["/residual_error_bound"])
	not _has_msg_containing(inp, "LAAS-OBL-RES-001", _r3_phrase)
	vn := violations with input as inp with data.laas as _cfg
	va := violations with input as absent with data.laas as _cfg
	vn == va
	sn := summary with input as inp with data.laas as _cfg
	sa := summary with input as absent with data.laas as _cfg
	sn == sa
}

test_szm_r3_bool_bound_invalid if _r3_invalid(false)

# ---- regression pins: valid bounds keep today's behaviour ----

test_szm_r3_regression_zero_bound_valid if {
	inp := _r3_with_bound(0)
	ids := error_ids with input as inp with data.laas as _cfg
	not "LAAS-OBL-RES-001" in ids
	compliant with input as inp with data.laas as _cfg
}

test_szm_r3_regression_fraction_bound_valid if {
	inp := _r3_with_bound(0.01)
	ids := error_ids with input as inp with data.laas as _cfg
	not "LAAS-OBL-RES-001" in ids
	compliant with input as inp with data.laas as _cfg
}

test_szm_r3_regression_ct4_compliant_unchanged if {
	s := summary with input as _base_ct4 with data.laas as _cfg
	s.compliant == true
	not _has_msg_containing(_base_ct4, "LAAS-OBL-RES-001", _r3_phrase)
}

# --------------------------------------------------------------------------- #
# laas-szm rulings R2a and R3c (TDD: written before the laas.rego change)
# R2a: an integral-float assigned_ct in 0..4 (e.g. 2.0) is valid and must
# behave exactly like the integer: effective_ct, the tolerance lookup, and
# every %d message. Floats are built with json.unmarshal("N.0") so formatting
# cannot normalise them; test_szm_r2a_float_sentinel proves they stay floats.
# R3c: the invalid-bound RES-001 fires on a blocked record and at CT0.
# --------------------------------------------------------------------------- #

_r2a_f(n) := json.unmarshal(sprintf("%d.0", [n]))

# float inputs carry an extra inert key: 2.0 == 2 as Rego terms, so without it
# OPA may reuse results cached for the integer twin (observed while writing
# these tests) and the comparison would be vacuous.
_r2a_float_ct(inp, n) := json.patch(inp, [
	{"op": "replace", "path": "/gate/assigned_ct", "value": _r2a_f(n)},
	{"op": "add", "path": "/r2a_float_marker", "value": true},
])

_r2a_set_ct(inp, ct) := json.patch(inp, [{"op": "replace", "path": "/gate/assigned_ct", "value": ct}])

# window ct 0: max([2.0, 2]) returns the int 2 and would mask D1, so the
# cumulative window must sit below the assigned tier for the float to reach
# effective_ct.
_r2a_agg0(inp) := json.patch(inp, [{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 0}])

_r2a_no_garbage(inp) if {
	vs := violations with input as inp with data.laas as _cfg
	count([v | some v in vs; contains(v.msg, "%!")]) == 0
}

_r2a_no_fallback(inp) if {
	not _has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(2))
	not _has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(3))
	not _has_msg(inp, "LAAS-OBL-TIER-001", _szm_msg(4))
}

# guard: the fixture value really is a float (a %d render is garbage).
test_szm_r2a_float_sentinel if {
	sprintf("%d", [_r2a_f(2)]) != "2"
	_r2a_f(2) == 2
}

test_szm_r2a_ct2_float_exceeds_tolerance if {
	base := _r2a_agg0(json.patch(_base_ct2, [{"op": "replace", "path": "/residual_error_bound", "value": 0.03}]))
	inp := _r2a_float_ct(base, 2)
	_has_msg(inp, "LAAS-OBL-RES-001", "residual escape rate 0.03 exceeds tolerance 0.02 for ct 2")
	s := summary with input as inp with data.laas as _cfg
	s.effective_ct == 2
	si := summary with input as _r2a_set_ct(base, 2) with data.laas as _cfg
	s == si
	_r2a_no_fallback(inp)
	_r2a_no_garbage(inp)
}

test_szm_r2a_ct2_float_bucket_b_no_bound if {
	base := _r2a_agg0(json.patch(_ct2_nobound, [{"op": "replace", "path": "/verifier", "value": _verifier_model_indep}]))
	inp := _r2a_float_ct(base, 2)
	_has_msg(inp, "LAAS-OBL-RES-001", _sd3b_msg)
	_r2a_no_garbage(inp)
}

test_szm_r2a_float_below_lattice_message if {
	m := "gate assigned_ct 1 is below lattice-derived ct 2"
	_has_msg(_r2a_set_ct(_base_ct2, 1), "LAAS-OBL-TIER-001", m)
	inp := _r2a_float_ct(_base_ct2, 1)
	_has_msg(inp, "LAAS-OBL-TIER-001", m)
	_r2a_no_garbage(inp)
}

test_szm_r2a_float_agg001_message if {
	base := json.patch(_base_ct2, [
		{"op": "replace", "path": "/action/effect_surface/scope", "value": "org"},
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 4},
	])
	m := "assigned_ct 3 is below cumulative-window ct 4 (structuring guard)"
	_has_msg(_r2a_set_ct(base, 3), "LAAS-OBL-AGG-001", m)
	inp := _r2a_float_ct(base, 3)
	_has_msg(inp, "LAAS-OBL-AGG-001", m)
	_r2a_no_garbage(inp)
}

test_szm_r2a_float_self001_message if {
	base := _r2a_agg0(json.patch(_base_ct2, [{"op": "replace", "path": "/action/self_reported_ct", "value": 0}]))
	m := "self_reported_ct 0 is below gate ct 2 (gate prevails)"
	_has_msg(_r2a_set_ct(base, 2), "LAAS-OBL-SELF-001", m)
	inp := _r2a_float_ct(base, 2)
	_has_msg(inp, "LAAS-OBL-SELF-001", m)
	_r2a_no_garbage(inp)
}

# regression pin: CT4 record with 4.0 equals the integer-4 record.
test_szm_r2a_regression_ct4_float_equals_int if {
	inp := _r2a_float_ct(_base_ct4, 4)
	vf := violations with input as inp with data.laas as _cfg
	vi := violations with input as _base_ct4 with data.laas as _cfg
	vf == vi
	sf := summary with input as inp with data.laas as _cfg
	si := summary with input as _base_ct4 with data.laas as _cfg
	sf == si
}

# ---- R3c guards: invalid-bound RES-001 without tolerance-path help ----

test_szm_r3c_blocked_negative_bound_invalid if {
	inp := json.patch(_base_ct4, [
		{"op": "replace", "path": "/action_blocked", "value": true},
		{"op": "replace", "path": "/residual_error_bound", "value": -0.01},
	])
	_has_msg(inp, "LAAS-OBL-RES-001", _r3_phrase)
	not compliant with input as inp with data.laas as _cfg
}

test_szm_r3c_ct0_string_bound_invalid if {
	inp := json.patch(_base_ct2, array.concat(_retier(0, _surface_ro), [{"op": "replace", "path": "/residual_error_bound", "value": "0.01"}]))
	ct := effective_ct with input as inp with data.laas as _cfg
	ct == 0
	_has_msg(inp, "LAAS-OBL-RES-001", _r3_phrase)
	not compliant with input as inp with data.laas as _cfg
}

# --------------------------------------------------------------------------- #
# laas-szm ruling R2b (TDD: written before the laas.rego change)
# R2b extends R2a to aggregate.window_effect_ct: an integral-float window ct
# (4.0) must behave exactly like the integer in effective_ct, the tolerance
# lookup, and every %d message. Non-integral values (2.5) keep today's
# behaviour, pinned below. Float inputs carry an inert r2b_float_marker key
# for the same cache reason as r2a_float_marker (:803-805).
# --------------------------------------------------------------------------- #

# assigned_ct 2 and lattice ct 2 sit below the window, so the float 4.0
# strictly wins max() and reaches effective_ct (cf. :813-815).
_r2b_float_window(inp, n) := json.patch(inp, [
	{"op": "replace", "path": "/aggregate/window_effect_ct", "value": _r2a_f(n)},
	{"op": "add", "path": "/r2b_float_marker", "value": true},
])

_r2b_int_window(inp, n) := json.patch(inp, [{"op": "replace", "path": "/aggregate/window_effect_ct", "value": n}])

# guard: the R2b fixture's window ct really is a float.
test_szm_r2b_float_sentinel if {
	inp := _r2b_float_window(_base_ct2, 4)
	w := inp.aggregate.window_effect_ct
	sprintf("%d", [w]) != "4"
	w == 4
}

# CT4 tolerance is 0, so bound 0.01 must trip RES-001 for 4 and 4.0 alike.
test_szm_r2b_float_window_res001 if {
	m := "residual escape rate 0.01 exceeds tolerance 0 for ct 4"
	_has_msg(_r2b_int_window(_base_ct2, 4), "LAAS-OBL-RES-001", m)
	inp := _r2b_float_window(_base_ct2, 4)
	_has_msg(inp, "LAAS-OBL-RES-001", m)
	vf := violations with input as inp with data.laas as _cfg
	vi := violations with input as _r2b_int_window(_base_ct2, 4) with data.laas as _cfg
	vf == vi
}

test_szm_r2b_float_window_no_garbage if {
	_has_msg(
		_r2b_float_window(_base_ct2, 4), "LAAS-OBL-AGG-001",
		"assigned_ct 2 is below cumulative-window ct 4 (structuring guard)",
	)
	_r2a_no_garbage(_r2b_float_window(_base_ct2, 4))
}

# pin (not an endorsement): today a non-integral window ct 2.5 reaches
# effective_ct as 2.5, has no tolerance key (so no RES-001), and AGG-001
# renders "%!d(float64=2.5)". R2b leaves this behaviour unchanged.
test_szm_r2b_pin_nonintegral_window if {
	inp := json.patch(_base_ct2, [
		{"op": "replace", "path": "/aggregate/window_effect_ct", "value": 2.5},
		{"op": "add", "path": "/r2b_float_marker", "value": true},
	])
	vs := violations with input as inp with data.laas as _cfg
	vs == {{
		"obligation": "LAAS-OBL-AGG-001",
		"severity": "error",
		"msg": "assigned_ct 2 is below cumulative-window ct %!d(float64=2.5) (structuring guard)",
	}}
	s := summary with input as inp with data.laas as _cfg
	s.effective_ct == 2.5
	s.compliant == false
}
