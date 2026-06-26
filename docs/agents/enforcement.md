# Enforcement

Tier-2 detail for [`../../AGENTS.md`](../../AGENTS.md).
How the conventions in **llm-agent-assurance-standard** are enforced — what is automated, what is reviewed, and where a convention lives when it changes.

## Automated gates

| Gate | Where it runs | What it checks |
|------|--------------|----------------|
| `scripts/check-sanitization.sh` | CI and the pre-commit hook | No internal term from the denylist appears in the publishable tree. The denylist is base64-encoded inside the script so the script does not itself republish those terms. |
| Markdown lint | CI | `markdownlint-cli2` over every Markdown file. |
| Link check | CI | `lychee` resolves every link. |
| `commitlint` | CI, on every pull request | Every commit message is a valid Conventional Commit. |
| Conformance policy | CI | `kellerai.oss.conformance` OPA policy via the reusable workflow. |

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

## The LaaS action-conformance policy

`conformance/laas/laas.rego` is the primary OPA policy for this repository
(package `kellerai.laas.actions`, declared at `laas.rego:18`).
It gates individual LLM-agent *actions* by consequence tier — not the model
itself — and applies wherever an agent can take an action with an effect
outside its sandbox.
The gate, not the agent, supplies the observed effect surface; this policy
checks that the tier assignment, verification, and enforcement are correct.

- **Package:** `kellerai.laas.actions` (`laas.rego:18`).
- **Sibling data:** `conformance/laas/data.json` carries the obligation registry,
  the CT lattice, and enforcement thresholds (`conformance/laas/data.json:1–34`).
- **Entry points:** `violations` (set of `{obligation, severity, msg}`),
  `summary` (`expected_ct`, `effective_ct`, `errors`, `warnings`, `compliant`),
  and `compliant` (bool — true when no error-severity violations exist)
  (`laas.rego:11–13`).
- **CT classification** — tier is the lattice max of three axes; an unknown or
  undetermined surface defaults to CT4 (`laas.rego:29`; `data.json:11`):
  - **CT0** — no external effect; read-only or fully sandboxed (`laas.rego:32–34`).
  - **CT1** — reversible, single-system internal write
    (reversibility rank 1, scope rank 1; `data.json:7–9`).
  - **CT2** — reversible or low-consequence external effect.
  - **CT3** — hard-to-reverse or material-consequence action; triggers
    independent pre-commit verification (`data.json:12`).
  - **CT4** — irreversible or high-consequence; requires independent
    verification **plus** human approval; default when surface is undetermined
    (`data.json:13`).
- **Effective tier:** max of the gate-assigned CT and the cumulative window CT,
  preventing structuring attacks (`laas.rego:47–49`).
- **Fail-safe default:** `default expected_ct := 4` (`laas.rego:29`).

### LaaS obligation families

Each obligation maps to a violation rule in `laas.rego`; severities are
recorded in `conformance/laas/data.json:19–32`.

- **`LAAS-OBL-TIER-001`** — CT is gate-derived from the observed effect surface;
  a gate-assigned tier below the lattice-derived tier is an error
  (`laas.rego:97–103`; `data.json:20`).
- **`LAAS-OBL-SELF-001`** — a self-reported tier may not lower the gate-derived
  tier; the gate always prevails (warning, `laas.rego:105–111`; `data.json:21`).
- **`LAAS-OBL-ENF-001`** — enforcement-plane integrity: the policy bundle must
  be signed and the gate must run out-of-process (`laas.rego:113–122`; `data.json:22`).
- **`LAAS-OBL-TRC-001`** — the decision trace must be append-only and chained
  (`laas.rego:124–127`; `data.json:23`).
- **`LAAS-OBL-AGG-001`** — the assigned tier must not be below the cumulative
  window CT; guards against structuring (`laas.rego:129–135`; `data.json:24`).
- **`LAAS-OBL-INP-001`** — untrusted input must raise the tier to the configured
  floor (CT≥3 by default) or the action must be blocked
  (`laas.rego:137–145`; `data.json:18,25`).
- **`LAAS-OBL-VEN-001`** — third-party or vendor dependencies require attribution
  and scope limits (`laas.rego:147–151`; `data.json:26`).
- **`LAAS-OBL-IRR-001`** — CT≥3 actions require a passing independent pre-commit
  verifier unless the action is blocked (`laas.rego:153–158`; `data.json:27`).
- **`LAAS-OBL-IND-001`** — the pre-commit verifier must be independent: a distinct
  checker type, different model lineage, and error-correlation ≤ 0.2
  (`laas.rego:160–166`; `data.json:14,28`).
- **`LAAS-OBL-VQ-001`** — the verifier must be qualified (DO-330 analogue)
  (`laas.rego:168–174`; `data.json:29`).
- **`LAAS-OBL-RES-001`** — the Bucket-B residual escape rate must be within
  tolerance for the effective tier (`laas.rego:183–192`; `data.json:15,30`).
- **`LAAS-OBL-HUM-001`** — CT4 actions require human approval unless the action
  is blocked (`laas.rego:176–181`; `data.json:13,31`).

### Audit trail — `violations` and `summary`

Every evaluation produces a `summary` record (`laas.rego:214–221`) containing
`bundle`, `expected_ct`, `effective_ct`, `errors`, `warnings`, and `compliant`.
The `violations` set carries the full obligation ID, severity, and a diagnostic
message for each firing rule.
These surfaces are the canonical inputs to any downstream decision log or
append-only trace required by `LAAS-OBL-TRC-001`.

### Proof scripts — LaaS action-conformance (`scripts/laas/`)

The LaaS action-conformance policy ships a decision-record emitter, backtest
harness, OSI adapter, and runnable proofs under `scripts/laas/`.
Each is invoked directly with `python3` or `bash`; none are wired into a git hook,
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
