# llm-agent-assurance-standard

LLM-Agent Assurance Standard (LAAS) — normative spec, OPA enforcement policy, and reference
tooling for action-level assurance of autonomous LLM agents.

[![CI](https://github.com/KellerAI/llm-agent-assurance-standard/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/KellerAI/llm-agent-assurance-standard/actions/workflows/ci.yml)
[![Agentic gates](https://github.com/KellerAI/llm-agent-assurance-standard/actions/workflows/conformance.yml/badge.svg)](https://github.com/KellerAI/llm-agent-assurance-standard/actions/workflows/conformance.yml)

- **License:** Apache-2.0
- **Owner:** KellerAI
- **Artifact type:** rego-policy
- **Standard version:** Draft v1.1

---

## What LAAS is

LAAS is a conformance standard for **individual actions taken by LLM-based agents**.
It assigns a **Consequence Tier (CT0–CT4)** to every action from the **observed effect surface** —
never the agent's self-report.
The governing invariant applies Zero-Trust to both the model's outputs and the enforcement
apparatus: a conforming system must not let the constrained party tier, grade, or gate itself.
Conformance asserts that the right checks ran, by the right party, with evidence.
It is a **standard of care**, not a correctness guarantee.

## Try it

You need `opa` (CI pins 1.14.1) and Python 3.13 (CI pins 3.13). From the repository root:

```sh
opa test conformance/ -v                    # 194 policy tests
python3 -m unittest discover scripts/laas   # 81 reference-tooling tests
bash scripts/laas/check.sh                  # emit a decision record, then evaluate it
```

`check.sh` emits a decision record from a sample effect surface, evaluates it against the
policy with `opa eval`, and ends by printing the `compliant` verdict: `true`.

## Status

`v0.1.0` is the only tagged release; unreleased changes are listed in [`CHANGELOG.md`](CHANGELOG.md).
Three version labels are in use, and each tracks a different thing:

- **Repository release:** `v0.1.0` (git tag; [`CITATION.cff`](CITATION.cff)).
- **Standard text:** Draft v1.1 (`standard/LAAS.md:3`).
- **Policy bundle:** `laas-fin-2.0.0` (`conformance/laas/data.json:4`), versioned with the
  obligation data the policy reads.

What is and is not measured:

- The policy suites, the reference-tooling tests, and both proof scripts pass in CI on every
  pull request (see [What CI runs](#what-ci-runs)).
- The escape-rate backtest harness (`scripts/laas/backtest.py`) has run only on its bundled
  synthetic fixture: 1,240 samples built to show a pass, a fail, and an indeterminate result
  (`docs/laas/backtest-demo.md`). This repository publishes no escape rate measured on real
  agent traces. Dataset provenance and labeling are an open question (`docs/laas/backtest.md:181`).

## What this repository contains

- [`standard/LAAS.md`](standard/LAAS.md) — normative prose standard, Draft v1.1.
  Defines CT0–CT4 tiers, 12 obligations, the governing invariant, and the conformance predicate.
  This is the canonical source; `conformance/laas/data.json` is derived from it.
- [`conformance/laas/`](conformance/laas/) — OPA/Rego policy (`package kellerai.laas.actions`)
  that machine-checks gate-produced decision records against the standard.
  Includes the obligation bundle, a 123-case test suite, and a bundled CT4-blocked example.
- [`docs/laas/standards/`](docs/laas/standards/) — four KellerAI renderings of LAAS in IEEE-, ISO-,
  NIST-, and SR-letter formats (the last after SR 11-7 / SR 26-2), none issued by those bodies.
  A PDF build pipeline with KellerAI covers and per-format CSS themes lives under
  [`docs/laas/standards/pdf/`](docs/laas/standards/pdf/).
- [`scripts/laas/`](scripts/laas/) — reference tooling: gate-side action emitter (`emitter.py`),
  Bucket-B backtest harness for escape-rate measurement (`backtest.py`), OSI-to-effect-surface
  adapter (`osi_to_surface.py`), and two proof scripts. `check.sh` emits a sample decision
  record and evaluates it with `opa eval`, skipping that step when `opa` is absent.
  `osi_check.sh` runs an OSI model through the adapter to `opa eval` and fails when `opa` is
  absent.
- [`docs/laas/`](docs/laas/) — design documentation: the v1.1 proposal (`proposal-v1.1.md`),
  steelman analysis (`steelman.md`), backtest spec (`backtest.md`) and runnable demo
  (`backtest-demo.md`), emitter reference (`emitter.md`), OSI adapter reference
  (`osi-adapter.md`), and the J-space internal-state advisory annex
  (`j-space-internal-state-annex.md`).
- [`docs/laas/profiles/`](docs/laas/profiles/) — controlled-language profiles that constrain
  the free-text fields of a decision trace, adapted from ASD-STE100 Simplified Technical
  English. A shared rule base (`ste-core.md`) plus nine industry profiles — banking,
  healthcare, SEO/advertising, real estate, building contracting (HVAC, solar), legal,
  insurance, software documentation, and education — each with a derived machine-readable
  dictionary. Informative: no new obligation or threshold.
- [`conformance/`](conformance/) — two verdict policies that CI evaluates on this repository's
  own pull requests, with their test suites.
  The in-repo OPA packages are `kellerai.laas.actions` (the LAAS agent-action policy in
  `conformance/laas/`) and two verdict policies in `conformance/`: `kellerai.oss.trust_dial`
  (the Dependabot trust-dial verdict policy) and `kellerai.oss.blast_radius` (the blast-radius
  pulse verdict policy); this repository has no `kellerai.oss.conformance` package, and the
  repo-structure check is run by the external reusable conformance workflow that `ci.yml`
  calls.

## Repository layout

| Path | What it contains |
|------|-----------------|
| [`standard/LAAS.md`](standard/LAAS.md) | Normative standard — tiers, obligations, governing invariant |
| [`conformance/laas/`](conformance/laas/) | OPA policy + data bundle + 123-case test suite + CT4 example |
| [`docs/laas/standards/`](docs/laas/standards/) | KellerAI renderings in IEEE-, ISO-, NIST-, and SR-letter formats + PDF pipeline |
| [`scripts/laas/`](scripts/laas/) | Emitter, backtest harness, OSI adapter, proof scripts (`check.sh`, `osi_check.sh`) |
| [`docs/laas/`](docs/laas/) | Design docs: v1.1 proposal, steelman, backtest spec and demo, emitter, OSI adapter, J-space annex |
| [`docs/laas/profiles/`](docs/laas/profiles/) | Controlled-language (STE) profiles: core rule base + 9 industry profiles |
| [`conformance/`](conformance/) | Verdict policies: blast-radius pulse, trust-dial (+ test suites) |
| [`docs/agents/`](docs/agents/) | Tier-2 agent guides: conventions, enforcement, glossary, citation |
| [`docs/adr/`](docs/adr/) | Architecture decision records |
| [`docs/articles/`](docs/articles/) | Index of 25 KellerAI articles on LAAS (kellerai.blog) |
| [`.github/`](.github/) | Workflows, issue and PR templates, CODEOWNERS, Dependabot config |

## Verify the policy

Run the LAAS policy against the bundled example decision record:

```bash
cd conformance/laas

# Syntax check + test suite (expect: 123/123 PASS)
opa check laas.rego laas_test.rego
opa test . -v

# Evaluate the bundled CT4-blocked example
opa eval -d laas.rego -d data.json \
  -i examples/action.ct4-blocked.json \
  'data.kellerai.laas.actions.summary' --format pretty
```

`error`-severity violations block; `warning`-severity are reported.

## What CI runs

CI runs every gate below on each pull request and on pushes to `dev` and `main`, plus a JSON
well-formedness check, Markdown lint, and a link check. The trust-dial and blast-radius
workflows also evaluate their verdict policies with `opa eval` on pull requests. The OPA and
Python test jobs are not yet required status checks. Line-level detail and sources:
[`docs/agents/conventions.md`](docs/agents/conventions.md) ("Local gates").

Run the same gates from the repository root before opening a pull request:

```sh
opa check conformance/laas/laas.rego conformance/laas/laas_test.rego
opa test conformance/laas/ -v
opa test conformance/ -v
bash scripts/check-sanitization.sh
bash scripts/laas/check.sh
bash scripts/laas/osi_check.sh
python3 -m unittest discover scripts/laas
```

Expected: `PASS: 123/123` for `conformance/laas/`, `PASS: 194/194` for all of `conformance/`,
`Ran 81 tests` and `OK` from the unit tests, and exit 0 from every other command.

## License

Licensed under the **Apache-2.0 License**.
Full text in [`LICENSE`](LICENSE); attribution in [`NOTICE`](NOTICE).

---

### For agents

Agents reading this repository should start at [AGENTS.md](AGENTS.md), not this README.
Claude Code users: see [CLAUDE.md](CLAUDE.md), which imports `AGENTS.md`.
The agent files document the conventions, vocabulary, and contribution discipline that agents are expected to follow.
