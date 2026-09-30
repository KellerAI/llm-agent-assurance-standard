# conformance/ — Verdict policies

This directory holds two OPA/Rego verdict policies for **this repository's own automation**:
Dependabot auto-merge (`trust_dial.rego:2`) and the blast-radius pulse (`blast_radius.rego:2`).
They are distinct from [`conformance/laas/`](laas/README.md), which gates autonomous LLM-agent
*actions* at runtime.

The in-repo OPA packages are `kellerai.laas.actions` (the LAAS agent-action policy in `conformance/laas/`) and two verdict policies in `conformance/`: `kellerai.oss.trust_dial` (the Dependabot trust-dial verdict policy) and `kellerai.oss.blast_radius` (the blast-radius pulse verdict policy); this repository has no `kellerai.oss.conformance` package, and the repo-structure check is run by the external reusable conformance workflow that `ci.yml` calls.

Package declarations: `laas/laas.rego:19`, `trust_dial.rego:21`, `blast_radius.rego:15`. The
external workflow call is `.github/workflows/ci.yml:37`
(see `.github/workflows/conformance.yml:4-5`).

| File | Package | Asserts |
|------|---------|---------|
| [`trust_dial.rego`](trust_dial.rego) | `kellerai.oss.trust_dial` | Dependabot PR auto-merge verdict (tier × ecosystem × update type × weekly budget). Codeowner-authored PRs take a matrix-independent base verdict, and every auto-merge passes the change-surface veto |
| [`trust_dial_data.json`](trust_dial_data.json) | — (data) | Verdict matrix, tier list, promotion thresholds, per-cycle budget, circuit-breaker config, change-surface globs, codeowner logins |
| [`blast_radius.rego`](blast_radius.rego) | `kellerai.oss.blast_radius` | Cross-file blast-radius pulse: which secondary files are owed when a trigger path changes |
| [`affects.json`](affects.json) | — (data) | Affects manifest (BR-002 – BR-015): trigger globs, required actions, severity, verifiability |
| [`trust_dial_test.rego`](trust_dial_test.rego) | `kellerai.oss.trust_dial_test` | Determinism proof suite for `trust_dial.rego` (every tier × update-type cell, budget exhaustion, change-surface veto, codeowner path) |
| [`blast_radius_test.rego`](blast_radius_test.rego) | `kellerai.oss.blast_radius_test` | Determinism proof suite for `blast_radius.rego` (fire and clear cases for BR-002 – BR-009 and BR-011, verifiable/unverifiable split) |

Both policies are **pure functions**: no clock, no network, no filesystem reads. Every threshold
is in `data`; every variable is in `input`. A passing `opa test` run is a proof of determinism.

---

## `trust_dial` — Dependabot auto-merge verdict

**Policy file**: `conformance/trust_dial.rego` — **data file**: `conformance/trust_dial_data.json`

### Data manifest structure

`trust_dial_data.json` is loaded as `data.trust_dial`. Top-level keys:

- `tiers` — ordered list: `["Observed", "Assisted", "Supervised", "Trusted"]`
- `default_tier` — `"Observed"`
- `verdict_matrix` — nested object: `tier → ecosystem → update_type → verdict`
- `promotion` — per-transition `clean_streak_required` counts
- `budget` — `max_auto_merges_per_cycle: 5`, `cycle: "weekly"`
- `circuit_breaker` — `regression_threshold` and `window_cycles`
- `bake` — `consecutive_clean_cycles_required`
- `change_surface` — `auto_merge_allowed_globs` and `deny_globs` (`trust_dial_data.json:51`)
- `codeowner_actors` — PR-author logins that take the codeowner path (`trust_dial_data.json:66`)

### Input shape

```json
{
  "tier":              "Assisted",
  "ecosystem":         "github-actions",
  "update_type":       "version-update:semver-patch",
  "cycle_merge_count": 0,
  "changed_files":     [".github/workflows/ci.yml"],
  "pr_author":         "dependabot[bot]"
}
```

The policy reads exactly these six fields. `pr_author` is the PR author login; a login listed in
`codeowner_actors` takes the codeowner path (`trust_dial.rego:53`). `changed_files` is required
for auto-merge (see the change-surface veto below). The trust-dial gate workflow also supplies
`dependency`, `from_version`, `to_version`, `pr_number` and `pr_actor`
(`.github/workflows/trust-dial-gate.yml:92-104`); the policy ignores them, and they reach the
trace only through `decision.inputs` (`trust_dial.rego:241`).

`tier` must be one of the four values in `tiers`. `ecosystem` falls back to the `"default"` row
when no override row exists (`trust_dial.rego:39-45`). `update_type` must be one of
`version-update:semver-patch`, `version-update:semver-minor`, `version-update:semver-major`.

### Public rules

| Rule | Type | Values |
|------|------|--------|
| `verdict` | string | `"auto-merge"` \| `"hold-for-review"` \| `"block"` |
| `rationale` | string | Human-readable trace: tier, ecosystem, update type, base, cycle count, change-surface status, verdict; prefixed `actor=codeowner` on the codeowner path (`trust_dial.rego:202-230`) |
| `decision` | object | `{verdict, rationale, inputs, rule_applied, alternatives}` — the verdict plus the four whitepaper-mandated fields (`trust_dial.rego:238-244`) |

The base verdict is `"auto-merge"` for a codeowner-authored PR and the matrix cell otherwise
(`trust_dial.rego:68-70`). Default `verdict` is `"hold-for-review"` (fail-safe; never
auto-merges by omission — `trust_dial.rego:146`). An `auto-merge` base verdict then passes the
change-surface veto: it falls back to `"hold-for-review"` when `changed_files` is missing or
empty (`trust_dial.rego:154-157`), and becomes `"block"` when any changed file matches a
`deny_globs` entry or falls outside `auto_merge_allowed_globs` (`trust_dial.rego:160-164`). A safe
`auto-merge` is downgraded to `"hold-for-review"` when
`cycle_merge_count >= budget.max_auto_merges_per_cycle` (`trust_dial.rego:174-178`).

### Example

```bash
# Run the full determinism proof (40 tests)
opa test conformance/trust_dial.rego conformance/trust_dial_test.rego \
  conformance/trust_dial_data.json -v

# Evaluate a single verdict
opa eval \
  -d conformance/trust_dial.rego \
  -d conformance/trust_dial_data.json \
  -I \
  'data.kellerai.oss.trust_dial.decision' \
  --format pretty \
  <<'EOF'
{"tier":"Assisted","ecosystem":"github-actions",
 "update_type":"version-update:semver-patch","cycle_merge_count":0,
 "changed_files":[".github/workflows/ci.yml"]}
EOF
# → verdict: "auto-merge"
```

---

## `blast_radius` — Cross-file blast-radius pulse

**Policy file**: `conformance/blast_radius.rego` — **data file**: `conformance/affects.json`

### Affects manifest structure

`affects.json` is loaded as `data.blast_radius`. The `affects` array (`affects.json:13`) holds
14 entries (BR-002 – BR-015). Each entry:

```jsonc
{
  "id":               "BR-006-new-rego-policy",
  "when_changed":     "conformance/*.rego",              // repo-relative glob; optional #subtarget suffix
  "affects":          ["conformance/*_test.rego", "docs/agents/enforcement.md"],
  "reason":           "...",
  "required_actions": ["...", "..."],
  "severity":         "error",    // "error" | "warning"
  "verifiable":       false       // true = machine-checkable; false = advisory
}
```

A `when_changed` value like `"conformance/data.json#schema.artifact_types"` fires only when the
`schema.artifact_types` key appears in `input.json_changes["conformance/data.json"]`
(`blast_radius.rego:69-87`).

### Input shape

```json
{
  "changed_files":              ["conformance/trust_dial.rego"],
  "json_changes":               {"conformance/data.json": ["schema.artifact_types"]},
  "commit_footer_actions_done": ["BR-006-new-rego-policy-1", "BR-006-new-rego-policy-2"],
  "git_sha":                    "abc123",
  "mode":                       "live"
}
```

`json_changes` and `commit_footer_actions_done` are optional (default to `{}` and `[]`
respectively — `blast_radius.rego:31-33`).

### Public rules

| Rule | Type | Values / meaning |
|------|------|-----------------|
| `fired` | set of objects | One element per triggered entry; each carries `id`, `trigger`, `affects`, `reason`, `required_actions`, `severity`, `verifiable`, `owed_count`, `affected_present_in_diff`, `affected_missing_from_diff` |
| `errors` | integer | Count of fired entries where `severity == "error"` AND `verifiable == true` AND `owed_count > 0` |
| `warnings` | integer | Count of fired entries with owed actions that do NOT qualify as `errors` |
| `verdict` | string | `"clear"` \| `"owed"` \| `"blocked"` |
| `allow` | boolean | `true` when `verdict != "blocked"` |
| `result` | object | `{verdict, fired, errors, warnings, git_sha, mode, inputs, rule_applied, alternatives, rationale}` |

**Verdict semantics** (`blast_radius.rego:206-215`):
- `"blocked"` — at least one `verifiable=true` error-severity entry with owed actions.
- `"owed"` — owed actions exist but none are both error-severity and verifiable (advisory only).
- `"clear"` — no entry fired with any owed action.

A `verifiable=false` entry at `severity="error"` **downgrades to a warning** and never blocks
(`blast_radius.rego:185-194`). See `docs/agents/enforcement.md` for the per-entry classification.

### Example

```bash
# Run the full determinism proof (31 tests)
opa test conformance/blast_radius.rego conformance/blast_radius_test.rego \
  conformance/affects.json -v

# Evaluate a change that blocks (CLAUDE.md edit, no actions declared DONE)
opa eval \
  -d conformance/blast_radius.rego \
  -d conformance/affects.json \
  -I \
  'data.kellerai.oss.blast_radius.result' \
  --format pretty \
  <<'EOF'
{"changed_files":["CLAUDE.md"],"json_changes":{},"commit_footer_actions_done":[]}
EOF
# → verdict: "blocked"  (BR-005-claude-md, severity=error, verifiable=true)
```

---

## LAAS action-gating policy

[`conformance/laas/`](laas/README.md) holds a separate policy — `kellerai.laas.actions` — that
gates autonomous LLM-agent *actions* at runtime by consequence tier (CT0–CT4). It is
independent of the two verdict policies above. See
[`conformance/laas/README.md`](laas/README.md) for its package, rules, and `opa eval` examples.
