# Enforcement

Tier-2 detail for [`../../AGENTS.md`](../../AGENTS.md).
How the conventions in **llm-agent-assurance-standard** are enforced — what is automated, what is reviewed, and where a convention lives when it changes.

## Automated gates

| Gate | Where it runs | What it checks |
|------|--------------|----------------|
| JSON well-formedness | CI (`.github/workflows/ci.yml:18`) | `jq empty` parses every `*.json` file in the tree. |
| `scripts/check-sanitization.sh` | CI (`.github/workflows/ci.yml:34`) and the pre-commit hook (`lefthook.yml:7–8`) | No internal term from the denylist appears in the publishable tree. The denylist is base64-encoded inside the script so the script does not itself republish those terms. |
| Markdown lint | CI (`.github/workflows/ci.yml:31`) | `markdownlint-cli2` over every Markdown file. |
| Link check | CI (`.github/workflows/ci.yml:48`) | `lychee` resolves every link. |
| `commitlint` | CI, on every pull request (`.github/workflows/commitlint.yml:18`) | Every commit message is a valid Conventional Commit. |
| Conformance workflow | CI (`.github/workflows/ci.yml:37`) | The external reusable workflow `jonathan-kellerai/kellerai-oss-template/.github/workflows/conformance.yml`; what it evaluates cannot be inspected from this repository. |
| Agentic gates | CI (`.github/workflows/conformance.yml:7`) | Repo-hygiene checks IC-1..IC-7 (`.github/workflows/conformance.yml:19`) and the D6 ADR citation check (`.github/workflows/conformance.yml:88`). |
| Branch tier | CI, on every pull request (`.github/workflows/validate-branch-tier.yml:24`) | The pull request follows the tiered merge model (`.github/workflows/validate-branch-tier.yml:10–13`). |
| External branch name | CI, on pull requests from `external/*` branches only (`.github/workflows/validate-branch-name.yml:14`) | The branch name matches the `external/` naming pattern. |
| Linked issue | CI, on pull requests from `external/*` branches only (`.github/workflows/validate-linked-issue.yml:19`) | The issue named in the branch is open and carries the `codeowner-approved` label (`.github/workflows/validate-linked-issue.yml:12–13`, `:23`). |
| Trust-dial gate | CI, on pull requests only (`.github/workflows/trust-dial-gate.yml:113`) | `opa eval` of `data.kellerai.oss.trust_dial.decision` against `conformance/`. |
| Blast-radius pulse | CI, on pull requests only (`.github/workflows/blast-radius-pulse.yml:60`) | `scripts/pulse.sh` runs `opa eval` of `data.kellerai.oss.blast_radius.result` (`scripts/pulse.sh:242`). |

The in-repo OPA packages are `kellerai.laas.actions` (the LAAS agent-action policy in `conformance/laas/`) and two verdict policies in `conformance/`: `kellerai.oss.trust_dial` (the Dependabot trust-dial verdict policy) and `kellerai.oss.blast_radius` (the blast-radius pulse verdict policy); this repository has no `kellerai.oss.conformance` package, and the repo-structure check is run by the external reusable conformance workflow that `ci.yml` calls.
Package declarations: `conformance/laas/laas.rego:19`, `conformance/trust_dial.rego:21`, `conformance/blast_radius.rego:15`.

The pre-commit hook is managed by `lefthook`.
Install it once with `lefthook install`; it then runs the sanitization gate before every commit.
CI runs the same gates, so the hook is a convenience — not the sole line of defence.

## Reviewed, not automated

- **`CODEOWNERS`** routes changes under `.github/`, `LICENSE`, `NOTICE`, `AGENTS.md`, `CLAUDE.md`,
  and `conformance/` to `@jonathan-kellerai` for review.
- The **pull-request template** requires a semver classification, the list of artifacts touched,
  and the validation-gate output. Reviewers confirm these.
- An **IP-leak audit** — a qualitative pass beyond the sanitization regex —
  is run before any machine-generated artifact is added to the publishable tree.
  The regex gate is necessary but not sufficient.

## Where a convention lives

`AGENTS.md` and the files under `docs/agents/` are canonical.
When a convention changes:

1. Change it in `docs/agents/conventions.md` (or the relevant Tier-2 file) first — that is the source of truth.
2. Update the `AGENTS.md` summary if the Tier-1 overview is now stale.
3. Propagate to `CONTRIBUTING.md` and `README.md` if either restates it.

`README.md`, `CONTRIBUTING.md`, and the issue and pull-request templates
restate conventions for convenience; they are downstream of `docs/agents/`.

## Glossary review cadence

Every change that introduces new load-bearing vocabulary MUST, in the same pull request,
add or update the [`glossary.md`](glossary.md) terms it introduces.
A reviewer who sees new vocabulary with no glossary entry should block the pull request.

## Validating the LaaS conformance policy

`conformance/laas/` holds the complete LaaS action-conformance OPA bundle.
Run these commands locally before committing any change to the policy or its data:

```bash
# Syntax and type-check
opa check conformance/laas/

# Run the sibling test suite
opa test conformance/laas/
```

The test suite lives at `conformance/laas/laas_test.rego`.
`opa test` must exit zero before any change to `conformance/laas/laas.rego`
or `conformance/laas/data.json` is committed.
This is a local contributor gate, not a CI gate.
In CI, this repository's workflows run the sanitization gate (`bash scripts/check-sanitization.sh`, in `ci.yml`) and invoke OPA only as `opa eval` (in the trust-dial gate workflow, and in the blast-radius pulse workflow via `scripts/pulse.sh`); `opa check`, `opa test`, the Python unit tests, `scripts/laas/check.sh`, and `scripts/laas/osi_check.sh` are local gates that no workflow in this repository's `.github/workflows/` runs, and what the external reusable conformance workflow called from `ci.yml` runs cannot be inspected from this repository.
Sources: `.github/workflows/ci.yml:33–34`, `.github/workflows/ci.yml:37`, `.github/workflows/trust-dial-gate.yml:113`, `.github/workflows/blast-radius-pulse.yml:60`, `scripts/pulse.sh:242`.

## The LaaS action-conformance policy

`conformance/laas/laas.rego` is the primary OPA policy for this repository
(package `kellerai.laas.actions`, declared at `laas.rego:19`).
It gates individual LLM-agent *actions* by consequence tier — not the model
itself — and applies wherever an agent can take an action with an effect
outside its sandbox.
The gate, not the agent, supplies the observed effect surface; this policy
checks that the tier assignment, verification, and enforcement are correct.

- **Package:** `kellerai.laas.actions` (`laas.rego:19`).
- **Sibling data:** `conformance/laas/data.json` carries the obligation registry,
  the CT lattice, and enforcement thresholds (`conformance/laas/data.json:1–34`).
- **Entry points:** `violations` (set of `{obligation, severity, msg}`),
  `summary` (`bundle`, `expected_ct`, `effective_ct`, `errors`, `warnings`, `compliant`;
  `bundle` at `laas.rego:216`),
  `compliant` (bool — true when no error-severity violations exist),
  and `error_ids` (set of obligation IDs with error-severity violations; rule at `laas.rego:209`)
  (`laas.rego:11–14`).
- **CT classification** — tier is the lattice max of three axes; an unknown or
  undetermined surface defaults to CT4 (`laas.rego:30`; `data.json:11`):
  - **CT0** — no external effect; read-only or fully sandboxed. Assigned only when
    `external_effect` is boolean `false` (`laas.rego:33–35`); an absent, `null`, or
    non-boolean value gives CT4 (`laas.rego:30`).
  - **CT1** — reversible, single-system internal write
    (reversibility rank 1, scope rank 1; `data.json:7–9`).
  - **CT2** — reversible or low-consequence external effect.
  - **CT3** — hard-to-reverse or material-consequence action; triggers
    independent pre-commit verification (`data.json:12`).
  - **CT4** — irreversible or high-consequence; requires independent
    verification **plus** human approval; default when surface is undetermined
    (`data.json:13`).
- **Effective tier:** max of the gate tier and the cumulative window CT,
  preventing structuring attacks (`laas.rego:48`).
  The cumulative window CT is supplied by the caller (the policy does not compute it);
  the max rule only consumes it, so preventing structuring also depends on that supplied value
  (`input.aggregate.window_effect_ct`, `laas.rego:310`).
  The gate tier is `gate.assigned_ct`, or the lattice CT when `assigned_ct` is absent or not an integer 0..4
  (`laas.rego:265–276`).
- **Fail-safe default:** `default expected_ct := 4` (`laas.rego:30`).
  An absent or invalid `assigned_ct` falls back to the lattice CT and raises TIER-001 (`laas.rego:262–283`).

### LaaS obligation families

Each obligation maps to a violation rule in `laas.rego`; severities are
recorded in `conformance/laas/data.json:19–32`.

- **`LAAS-OBL-TIER-001`** — CT is gate-derived from the observed effect surface;
  a valid gate-assigned tier below the lattice-derived tier is an error
  (`laas.rego:99–104`; `data.json:20`).
  It also fires when the gate did not record an integer `assigned_ct` in 0..4,
  and the lattice tier is then enforced (`laas.rego:278–283`; `data.json:20`).
- **`LAAS-OBL-SELF-001`** — a self-reported tier may not lower the gate-derived
  tier; the gate always prevails
  (compared against the lattice CT when `assigned_ct` is invalid;
  warning, `laas.rego:107–112`; `data.json:21`).
- **`LAAS-OBL-ENF-001`** — enforcement-plane integrity: the policy bundle must
  be signed and the gate must run out-of-process (`laas.rego:115–123`; `data.json:22`).
  OPA checks only the recorded `gate.bundle_signed` and `gate.out_of_process` flags;
  the actual signature and process boundary require separate verification.
- **`LAAS-OBL-TRC-001`** — the decision trace must be append-only and chained.
  The cited OPA rule checks only the `append_only` flag; it does not reference
  the chain hash or Merkle anchor, so chaining needs separate verification or a
  deployment control (`laas.rego:126–128`; `data.json:23`).
- **`LAAS-OBL-AGG-001`** — a valid assigned tier must not be below the cumulative
  window CT; guards against structuring (`laas.rego:131–136`; `data.json:24`).
  An invalid `assigned_ct` is handled by TIER-001 (`laas.rego:278–283`).
- **`LAAS-OBL-INP-001`** — untrusted input must raise the tier to the configured
  floor (CT≥3 by default) or the action must be blocked
  (`laas.rego:139–146`; `data.json:18,25`).
- **`LAAS-OBL-VEN-001`** — third-party or vendor dependencies require attribution
  and scope limits (`laas.rego:149–152`; `data.json:26`).
- **`LAAS-OBL-IRR-001`** — CT≥3 actions require a passing independent pre-commit
  verifier unless the action is blocked. OPA's IRR-001 rule checks only that a
  non-blocked CT≥3 verifier verdict is `pass` (`laas.rego:155–159`; `data.json:27`);
  independence and qualification are checked by IND-001 and VQ-001 below.
- **`LAAS-OBL-IND-001`** — the pre-commit verifier must be independent: deterministic,
  human, or a model of a different lineage with error-correlation ≤ 0.2
  (`laas.rego:76–84`, `:162–167`). At CT4 a passed model verifier on a non-blocked
  action violates it;
  a deterministic or human verifier is required (`laas.rego:225–230`; `data.json:13,14,28`).
- **`LAAS-OBL-VQ-001`** — the verifier must be qualified (DO-330 analogue)
  (`laas.rego:170–175`; `data.json:29`).
- **`LAAS-OBL-RES-001`** — the Bucket-B residual escape rate must be within
  tolerance for the effective tier (`laas.rego:185–193`). At CT≥2 on a non-blocked
  action, a numeric bound also needs non-empty `evidence_refs` (`laas.rego:248–253`),
  and a Bucket-B action (no passed deterministic verifier) must supply a bound
  (`laas.rego:255–260`; `data.json:15,30`).
  A supplied `residual_error_bound` that is not a number >= 0 also fires RES-001 at any CT, blocked or not
  (`laas.rego:285–300`).
  A `null` bound counts as absent, and an invalid bound is never compared to the tolerance.
- **`LAAS-OBL-HUM-001`** — CT4 actions require human approval unless the action
  is blocked (`laas.rego:178–182`; `data.json:13,31`).

### Audit trail — `violations` and `summary`

Every evaluation produces a `summary` record (`laas.rego:215–222`) containing
`bundle`, `expected_ct`, `effective_ct`, `errors`, `warnings`, and `compliant`.
The `violations` set carries the full obligation ID, severity, and a diagnostic
message for each firing rule.
These surfaces are the canonical inputs to any downstream decision log or
append-only trace required by `LAAS-OBL-TRC-001`.

### Proof scripts — LaaS action-conformance (`scripts/laas/`)

The LaaS action-conformance policy ships a decision-record emitter, backtest
harness, OSI adapter, and runnable proofs under `scripts/laas/`.
Each is invoked directly with `python3` or `bash`; none are wired into a git hook
(`lefthook.yml:7–8` runs only the sanitization gate) or into any workflow in `.github/workflows/`,
so contributors run them on demand.

| Script | Invocation | Purpose |
|--------|------------|---------|
| `scripts/laas/emitter.py` | `python3 scripts/laas/emitter.py -i <effect-surface.json> -b conformance/laas/data.json -o <out.json>` | Emit a gate-derived decision record from an effect surface. |
| `scripts/laas/backtest.py` | `python3 scripts/laas/backtest.py --dataset <fixture.json> --data-json conformance/laas/data.json --ct <CT>` | Measure the Bucket-B escape rate against a labeled backtest fixture and validate it against the per-CT tolerance in `conformance/laas/data.json`. |
| `scripts/laas/check.sh` | `bash scripts/laas/check.sh` | Emit a sample decision record from `scripts/laas/fixtures/transfer.effect-surface.json` and (if `opa` is present) evaluate it against `package kellerai.laas.actions`; skips the OPA step when `opa` is absent. |
| `scripts/laas/osi_to_surface.py` | `python3 scripts/laas/osi_to_surface.py -m <model.json> --kind dataset\|metric --name <name> --operation read\|write\|delete` (add `--unsigned` for an untrusted model) | OSI (Open Semantic Interchange) → LaaS adapter: build an effect surface from an annotated OSI model and emit a decision record via the canonical emitter — no tier math lives in the adapter. |
| `scripts/laas/osi_check.sh` | `bash scripts/laas/osi_check.sh` | OSI model → adapter → decision record → `opa eval` proof, asserting the CT4 `net_settlement_amount` write is compliant under full enforcement controls. **Exits non-zero if `opa` is absent** — a proof that cannot run is not a passing proof. |

`scripts/laas/test_osi_to_surface.py` is the stdlib unittest for the OSI adapter.
Run the full suite with `python3 -m unittest discover scripts/laas`.
