# METADATA
# title: trust-dial Dependabot auto-merge verdict policy
# description: |
#   Pure deterministic verdict function. Consumes a Dependabot PR descriptor
#   plus the live trust-dial state as `input`, and the verdict matrix +
#   thresholds (trust_dial_data.json) as `data`. Emits exactly one verdict.
#
#   Two actor classes reach a base verdict:
#     - actor=bot: Dependabot PRs consult the (tier × ecosystem × update_type)
#       matrix for their base verdict.
#     - actor=codeowner: PRs authored by a login in
#       data.trust_dial.codeowner_actors bypass the matrix entirely and take a
#       base verdict of "auto-merge" directly (input.pr_author is the GitHub PR
#       author login, NOT github.actor).
#   Both classes then pass through the SAME change-surface veto pipeline, so a
#   codeowner never auto-merges an unsafe file surface.
#
#   The policy is a PURE function: no clock, no network, no filesystem read.
#   Every input is in `input`; every threshold is in `data.trust_dial`.
#   This is what makes `opa test` a proof of determinism.
package kellerai.oss.trust_dial

import rego.v1

# ---------------------------------------------------------------------------
# Data shortcuts (the trust-dial manifest, trust_dial_data.json)
# ---------------------------------------------------------------------------

_matrix := data.trust_dial.verdict_matrix

_budget := data.trust_dial.budget

_change_surface := data.trust_dial.change_surface

# ---------------------------------------------------------------------------
# Ecosystem key — explicit override row, or the "default" row.
# ---------------------------------------------------------------------------

_eco := input.ecosystem if {
	_matrix[input.tier][input.ecosystem]
}

_eco := "default" if {
	not _matrix[input.tier][input.ecosystem]
}

# ---------------------------------------------------------------------------
# Actor class — codeowner PRs take a privileged, matrix-independent path.
# input.pr_author is the GitHub PR author LOGIN (supplied by the workflow),
# deliberately NOT github.actor. Undefined pr_author → not a codeowner.
# ---------------------------------------------------------------------------

_is_codeowner if {
	input.pr_author in data.trust_dial.codeowner_actors
}

# ---------------------------------------------------------------------------
# Base verdict — the (tier × ecosystem × update_type) cell.
#
# Two complete-rule definitions that can NEVER both fire:
# - codeowner inputs short-circuit to "auto-merge" (matrix ignored).
# - the matrix cell is consulted ONLY for non-codeowner inputs; the
#   `not _is_codeowner` guard keeps the two definitions mutually exclusive,
#   so a codeowner PR that also carries update_type still takes the codeowner
#   path and the rules cannot conflict.
# ---------------------------------------------------------------------------

_base := "auto-merge" if _is_codeowner

_base := _matrix[input.tier][_eco][input.update_type] if not _is_codeowner

# ---------------------------------------------------------------------------
# Change-surface guard — safe IFF all changed_files are in allowlist AND
# none are in deny-list.
# ---------------------------------------------------------------------------

# Sentinel: input.changed_files exists and is non-empty.
_has_changed_files if {
	count(input.changed_files) > 0
}

# Check every file matches at least one allowlist glob.
_all_files_allowed if {
	_has_changed_files
	every file in input.changed_files {
		some pattern in _change_surface.auto_merge_allowed_globs
		glob.match(pattern, ["/"], file)
	}
}

# Helper: a file is denied if it matches any deny-list glob.
_file_is_denied(file) if {
	some pattern in _change_surface.deny_globs
	glob.match(pattern, ["/"], file)
}

# Check no file matches any deny-list glob.
_no_file_denied if {
	_has_changed_files
	every file in input.changed_files {
		not _file_is_denied(file)
	}
}

# Change surface is safe IFF all files allowed AND no file denied.
safe_change_surface if {
	_all_files_allowed
	_no_file_denied
}

# Helper: a file is allowed if it matches at least one allowlist glob.
_file_is_allowed(file) if {
	some pattern in _change_surface.auto_merge_allowed_globs
	glob.match(pattern, ["/"], file)
}

# First offending file (for rationale) — either denied or outside allowlist.
_first_offending_file := file if {
	_has_changed_files
	file := input.changed_files[_]
	_file_is_denied(file)
}

_first_offending_file := file if {
	_has_changed_files
	file := input.changed_files[_]
	not _file_is_allowed(file)
}

# ---------------------------------------------------------------------------
# verdict — exactly one of: "auto-merge" | "hold-for-review" | "block".
# Fail-safe default: hold-for-review. Never auto-merge by omission.
#
# Change-surface veto logic (applied ONLY to base auto-merge):
# - changed_files missing/empty → fail-safe to hold-for-review
# - changed_files provided but unsafe (denied or outside allowlist) → block
# - changed_files safe AND budget OK → auto-merge survives
# - Non-auto-merge base verdicts (hold/block) → unchanged (veto never relaxes)
# ---------------------------------------------------------------------------

default verdict := "hold-for-review"

# Non-auto-merge base verdicts pass through unchanged (veto never relaxes).
verdict := _base if {
	_base != "auto-merge"
}

# auto-merge + changed_files missing/empty → fail-safe to hold-for-review.
verdict := "hold-for-review" if {
	_base == "auto-merge"
	not _has_changed_files
}

# auto-merge + unsafe change surface → VETO to block.
verdict := "block" if {
	_base == "auto-merge"
	_has_changed_files
	not safe_change_surface
}

# auto-merge survives IFF budget OK AND change surface safe.
verdict := "auto-merge" if {
	_base == "auto-merge"
	input.cycle_merge_count < _budget.max_auto_merges_per_cycle
	safe_change_surface
}

# auto-merge + budget exhausted + safe surface → downgrade to hold-for-review.
verdict := "hold-for-review" if {
	_base == "auto-merge"
	input.cycle_merge_count >= _budget.max_auto_merges_per_cycle
	safe_change_surface
}

# ---------------------------------------------------------------------------
# rationale — a single string written verbatim into the decision trace.
# Includes change-surface decision (safe/veto/unknown).
# ---------------------------------------------------------------------------

# Change-surface status for rationale.
_surface_status := "change-surface=safe" if {
	safe_change_surface
}

_surface_status := sprintf("change-surface VETO: %s", [_first_offending_file]) if {
	_has_changed_files
	not safe_change_surface
}

_surface_status := "change-surface=unknown" if {
	not _has_changed_files
}

# Bot (Dependabot) rationale — the matrix path. Guarded with `not _is_codeowner`
# so it never co-defines with the codeowner rationale below. This text is FROZEN:
# dependabot inputs (no pr_author) must render byte-identically to prior releases.
rationale := sprintf(
	"tier=%s ecosystem=%s update_type=%s base=%s cycle=%d/%d %s -> %s",
	[
		input.tier, _eco, input.update_type, _base,
		input.cycle_merge_count, _budget.max_auto_merges_per_cycle,
		_surface_status, verdict,
	],
) if {
	not _is_codeowner
}

# Codeowner rationale — the privileged path. Carries `actor=codeowner` so traces
# distinguish it from the bot path. ecosystem/update_type may be absent or empty
# on a codeowner descriptor, so each is read via object.get with a safe default
# to keep rationale (and therefore decision) defined regardless.
rationale := sprintf(
	"actor=codeowner tier=%s ecosystem=%s update_type=%s base=%s cycle=%d/%d %s -> %s",
	[
		object.get(input, "tier", ""),
		object.get(input, "ecosystem", ""),
		object.get(input, "update_type", ""),
		_base,
		object.get(input, "cycle_merge_count", 0),
		_budget.max_auto_merges_per_cycle,
		_surface_status, verdict,
	],
) if {
	_is_codeowner
}

# ---------------------------------------------------------------------------
# decision — the full decision record, surfaced for trace emission.
# Carries the four whitepaper-mandated fields: inputs, rule_applied,
# alternatives, rationale.
# ---------------------------------------------------------------------------

decision := {
	"verdict": verdict,
	"rationale": rationale,
	"inputs": input,
	"rule_applied": "verdict_matrix",
	"alternatives": ["auto-merge", "hold-for-review", "block"],
}
