# METADATA
# title: trust-dial verdict policy — determinism test suite
# description: |
#   Enumerates the verdict matrix (4 tiers × 3 update-types × budget states)
#   plus fail-safe cases. A passing run is a proof that trust_dial.rego is a
#   pure deterministic function of (input, data).
#
#   The thresholds and matrix are loaded from conformance/trust_dial_data.json
#   exactly as in production; the tests vary `input` only. This is the same
#   convention conformance_test.rego uses — and is what allows OPA to compile
#   without spurious cross-package recursion warnings.
package kellerai.oss.trust_dial_test

import data.kellerai.oss.trust_dial
import rego.v1

# ---------------------------------------------------------------------------
# Input fixture — every test passes a variation of this descriptor.
# ---------------------------------------------------------------------------

_input(tier, eco, update_type, cycle_n) := {
	"tier": tier,
	"ecosystem": eco,
	"update_type": update_type,
	"dependency": "actions/checkout",
	"from_version": "4.1.0",
	"to_version": "4.2.0",
	"cycle_merge_count": cycle_n,
	"pr_number": 42,
	"pr_actor": "dependabot[bot]",
}

# ---------------------------------------------------------------------------
# Observed — every cell is hold-for-review.
# ---------------------------------------------------------------------------

test_observed_patch_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Observed", "github-actions", "version-update:semver-patch", 0)
}

test_observed_minor_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Observed", "github-actions", "version-update:semver-minor", 0)
}

test_observed_major_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Observed", "github-actions", "version-update:semver-major", 0)
}

# ---------------------------------------------------------------------------
# Assisted — patch auto-merges (within budget); minor holds; major blocks.
# ---------------------------------------------------------------------------

# NOTE: Post change-surface veto, omitting `changed_files` fail-safes to hold-for-review.
# This test preserves the original intent (auto-merge for patch at Assisted) by providing
# a safe changed_files array that passes the change-surface guard.
test_assisted_patch_auto if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

test_assisted_patch_budget_exhausted_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Assisted", "github-actions", "version-update:semver-patch", 5)
}

test_assisted_minor_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Assisted", "github-actions", "version-update:semver-minor", 0)
}

test_assisted_major_blocks if {
	trust_dial.verdict == "block" with input as _input("Assisted", "github-actions", "version-update:semver-major", 0)
}

# ---------------------------------------------------------------------------
# Supervised — patch + minor auto-merge; major holds.
# ---------------------------------------------------------------------------

test_supervised_patch_auto if {
	inp := object.union(_input("Supervised", "github-actions", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

test_supervised_minor_auto if {
	inp := object.union(_input("Supervised", "github-actions", "version-update:semver-minor", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

test_supervised_minor_budget_exhausted_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Supervised", "github-actions", "version-update:semver-minor", 5)
}

test_supervised_major_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Supervised", "github-actions", "version-update:semver-major", 0)
}

# ---------------------------------------------------------------------------
# Trusted — patch + minor auto-merge; major holds (deliberate ceiling).
# ---------------------------------------------------------------------------

test_trusted_patch_auto if {
	inp := object.union(_input("Trusted", "github-actions", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

test_trusted_minor_auto if {
	inp := object.union(_input("Trusted", "github-actions", "version-update:semver-minor", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

test_trusted_major_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Trusted", "github-actions", "version-update:semver-major", 0)
}

test_trusted_patch_budget_exhausted_holds if {
	trust_dial.verdict == "hold-for-review" with input as _input("Trusted", "github-actions", "version-update:semver-patch", 5)
}

# ---------------------------------------------------------------------------
# Fail-safe: unknown tier → default `hold-for-review` (never auto-merge).
# ---------------------------------------------------------------------------

test_unknown_tier_falls_back_to_hold if {
	trust_dial.verdict == "hold-for-review" with input as _input("Untrusted", "github-actions", "version-update:semver-patch", 0)
}

# ---------------------------------------------------------------------------
# Ecosystem fallback: an ecosystem with no override falls back to "default".
# ---------------------------------------------------------------------------

test_unknown_ecosystem_uses_default_row if {
	inp := object.union(_input("Assisted", "npm", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

# ---------------------------------------------------------------------------
# decision record carries the four whitepaper-mandated fields.
# ---------------------------------------------------------------------------

test_decision_carries_rule_applied if {
	d := trust_dial.decision with input as _input("Observed", "github-actions", "version-update:semver-patch", 0)
	d.rule_applied == "verdict_matrix"
}

test_decision_carries_alternatives if {
	d := trust_dial.decision with input as _input("Observed", "github-actions", "version-update:semver-patch", 0)
	d.alternatives == ["auto-merge", "hold-for-review", "block"]
}

# NOTE: Post change-surface veto, rationale includes change-surface status.
# This test now expects "change-surface=unknown" because changed_files is omitted.
test_decision_carries_rationale if {
	d := trust_dial.decision with input as _input("Trusted", "github-actions", "version-update:semver-major", 0)
	d.rationale == "tier=Trusted ecosystem=default update_type=version-update:semver-major base=hold-for-review cycle=0/5 change-surface=unknown -> hold-for-review"
}

# ---------------------------------------------------------------------------
# Determinism: identical (input, data) → identical verdict, twice.
# ---------------------------------------------------------------------------

test_deterministic_same_input_same_verdict if {
	inp := object.union(_input("Supervised", "github-actions", "version-update:semver-minor", 2), {"changed_files": [".github/workflows/ci.yml"]})
	v1 := trust_dial.verdict with input as inp
	v2 := trust_dial.verdict with input as inp
	v1 == v2
	v1 == "auto-merge"
}

# ---------------------------------------------------------------------------
# Change-surface veto — restricts auto-merge to safe file patterns.
# ---------------------------------------------------------------------------

# Base auto-merge + all changed files in auto_merge_allowed_globs → auto-merge survives.
test_change_surface_safe_allows_auto_merge if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml", ".github/workflows/test.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

# Base auto-merge + a changed file in deny_globs (conformance/**) → VETO to block.
test_change_surface_deny_glob_blocks if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml", "conformance/trust_dial.rego"]})
	trust_dial.verdict == "block" with input as inp
}

# Base auto-merge + a changed file outside auto_merge_allowed_globs → block.
test_change_surface_outside_allowlist_blocks if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-patch", 0), {"changed_files": ["package.json"]})
	trust_dial.verdict == "block" with input as inp
}

# Base auto-merge + changed_files omitted → fail-safe to hold-for-review.
test_change_surface_missing_downgrades_to_hold if {
	# Existing _input helper does NOT include changed_files → fail-safe applies
	trust_dial.verdict == "hold-for-review" with input as _input("Assisted", "github-actions", "version-update:semver-patch", 0)
}

# Base block (e.g. major at Assisted) + any changed_files → stays block (veto never relaxes).
test_change_surface_cannot_relax_block if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-major", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "block" with input as inp
}

# Base hold + safe changed_files → stays hold (veto never promotes).
test_change_surface_cannot_promote_hold if {
	inp := object.union(_input("Observed", "github-actions", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "hold-for-review" with input as inp
}

# Empty changed_files array → treated as missing → fail-safe to hold.
test_change_surface_empty_array_downgrades_to_hold if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-patch", 0), {"changed_files": []})
	trust_dial.verdict == "hold-for-review" with input as inp
}

# Rationale field includes change-surface decision for safe case.
test_rationale_includes_change_surface_safe if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-patch", 0), {"changed_files": [".github/workflows/ci.yml"]})
	d := trust_dial.decision with input as inp
	contains(d.rationale, "change-surface=safe")
}

# Rationale field includes veto detail when file in deny-list.
test_rationale_includes_change_surface_veto if {
	inp := object.union(_input("Assisted", "github-actions", "version-update:semver-patch", 0), {"changed_files": ["conformance/trust_dial.rego"]})
	d := trust_dial.decision with input as inp
	contains(d.rationale, "change-surface VETO")
	contains(d.rationale, "conformance/trust_dial.rego")
}

# ---------------------------------------------------------------------------
# Codeowner auto-merge path — a PR authored by a login in
# data.trust_dial.codeowner_actors bypasses the tier/ecosystem/update_type
# matrix and takes base=auto-merge, then flows through the SAME change-surface
# veto pipeline. Deliberately omits tier/ecosystem/update_type to prove the
# codeowner path is defined without matrix inputs.
# ---------------------------------------------------------------------------

# Codeowner descriptor — no tier/ecosystem/update_type; those are matrix-only.
_codeowner_input(cycle_n) := {
	"pr_author": "jonathan-kellerai",
	"dependency": "actions/checkout",
	"cycle_merge_count": cycle_n,
	"pr_number": 99,
}

# Codeowner + safe surface + budget OK → auto-merge (matrix never consulted).
test_codeowner_safe_surface_budget_ok_auto_merge if {
	inp := object.union(_codeowner_input(0), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "auto-merge" with input as inp
}

# Codeowner + a deny-list file (conformance/**) → VETO to block.
test_codeowner_denied_file_blocks if {
	inp := object.union(_codeowner_input(0), {"changed_files": [".github/workflows/ci.yml", "conformance/x.rego"]})
	trust_dial.verdict == "block" with input as inp
}

# Codeowner + a file outside the allowlist → block.
test_codeowner_outside_allowlist_blocks if {
	inp := object.union(_codeowner_input(0), {"changed_files": ["package.json"]})
	trust_dial.verdict == "block" with input as inp
}

# Codeowner + missing changed_files → fail-safe to hold-for-review.
test_codeowner_missing_changed_files_holds if {
	trust_dial.verdict == "hold-for-review" with input as _codeowner_input(0)
}

# Codeowner + empty changed_files → treated as missing → hold-for-review.
test_codeowner_empty_changed_files_holds if {
	inp := object.union(_codeowner_input(0), {"changed_files": []})
	trust_dial.verdict == "hold-for-review" with input as inp
}

# Codeowner + safe surface + budget exhausted → downgrade to hold-for-review.
test_codeowner_budget_exhausted_holds if {
	inp := object.union(_codeowner_input(5), {"changed_files": [".github/workflows/ci.yml"]})
	trust_dial.verdict == "hold-for-review" with input as inp
}

# Non-codeowner pr_author falls through to the matrix/default path (NOT the
# codeowner short-circuit): Observed patch resolves to hold, and the rationale
# uses the bot format (no actor=codeowner token).
test_non_codeowner_author_falls_through_to_matrix if {
	inp := object.union(_input("Observed", "github-actions", "version-update:semver-patch", 0), {
		"pr_author": "someone-else",
		"changed_files": [".github/workflows/ci.yml"],
	})
	trust_dial.verdict == "hold-for-review" with input as inp
	d := trust_dial.decision with input as inp
	not contains(d.rationale, "actor=codeowner")
}

# Codeowner input that ALSO carries an update_type still takes the codeowner
# path: Observed major would be hold in the matrix, but the codeowner base is
# auto-merge, so a safe surface + budget OK yields auto-merge (matrix ignored).
test_codeowner_with_update_type_ignores_matrix if {
	inp := object.union(_codeowner_input(0), {
		"tier": "Observed",
		"ecosystem": "github-actions",
		"update_type": "version-update:semver-major",
		"changed_files": [".github/workflows/ci.yml"],
	})
	trust_dial.verdict == "auto-merge" with input as inp

	# This input carries BOTH codeowner and full matrix fields — the exact case
	# where a missing `not _is_codeowner` guard on the bot rationale would make
	# both rationale rules co-define with different values (runtime conflict).
	# Evaluating decision.rationale exercises that guard and locks the path.
	d := trust_dial.decision with input as inp
	contains(d.rationale, "actor=codeowner")
}

# Rationale is defined for a codeowner input and carries the actor=codeowner
# token (proves both "defined" and "path-distinguishing").
test_codeowner_rationale_defined if {
	inp := object.union(_codeowner_input(0), {"changed_files": [".github/workflows/ci.yml"]})
	d := trust_dial.decision with input as inp
	contains(d.rationale, "actor=codeowner")
}
