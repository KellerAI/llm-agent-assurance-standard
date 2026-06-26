# llm-agent-assurance-standard

LLM-Agent Assurance Standard (LAAS) — normative spec, OPA enforcement policy, and reference
tooling for action-level assurance of autonomous LLM agents.

[![Conformance](https://github.com/KellerAI/llm-agent-assurance-standard/actions/workflows/conformance.yml/badge.svg)](https://github.com/KellerAI/llm-agent-assurance-standard/actions/workflows/conformance.yml)

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

## What this repository contains

- [`standard/LAAS.md`](standard/LAAS.md) — normative prose standard, Draft v1.1.
  Defines CT0–CT4 tiers, 12 obligations, the governing invariant, and the conformance predicate.
  This is the canonical source; `conformance/laas/data.json` is derived from it.
- [`conformance/laas/`](conformance/laas/) — OPA/Rego policy (`package kellerai.laas.actions`)
  that machine-checks gate-produced decision records against the standard.
  Includes the obligation bundle, a 19-case test suite, and a bundled CT4-blocked example.
- [`docs/laas/standards/`](docs/laas/standards/) — four standards-body-styled renderings of LAAS:
  IEEE, NIST, ISO, and Summary-Report formats.
  A PDF build pipeline with house-styled covers and CSS themes lives under
  [`docs/laas/standards/pdf/`](docs/laas/standards/pdf/).
- [`scripts/laas/`](scripts/laas/) — reference tooling: gate-side action emitter (`emitter.py`),
  Bucket-B backtest harness for escape-rate measurement (`backtest.py`), OSI-to-effect-surface
  adapter (`osi_to_surface.py`), and a proof-check script (`check.sh`).
- [`docs/laas/`](docs/laas/) — design documentation: v1.1 proposal, backtest spec,
  steelman analysis, and emitter reference.
- [`conformance/`](conformance/) — structural conformance policies: blast-radius pulse and
  trust-dial verdict, enforced on every push via `.github/workflows/`.

## Repository layout

| Path | What it contains |
|------|-----------------|
| [`standard/LAAS.md`](standard/LAAS.md) | Normative standard — tiers, obligations, governing invariant |
| [`conformance/laas/`](conformance/laas/) | OPA policy + data bundle + 19-case test suite + CT4 example |
| [`docs/laas/standards/`](docs/laas/standards/) | IEEE, NIST, ISO, SR renderings + PDF pipeline |
| [`scripts/laas/`](scripts/laas/) | Emitter, backtest harness, OSI adapter, proof scripts |
| [`docs/laas/`](docs/laas/) | Design docs: v1.1 proposal, backtest spec, steelman |
| [`conformance/`](conformance/) | Structural policies: blast-radius, trust-dial |
| [`docs/agents/`](docs/agents/) | Tier-2 agent guides: conventions, enforcement, glossary |
| [`docs/adr/`](docs/adr/) | Architecture decision records |
| [`docs/articles/`](docs/articles/) | 25-article LAAS bibliography |
| [`.github/`](.github/) | Workflows, issue templates, CODEOWNERS |

## Verify the policy

Run the LAAS policy against the bundled example decision record:

```bash
cd conformance/laas

# Syntax check + test suite (expect: 19/19 PASS)
opa check laas.rego laas_test.rego
opa test . -v

# Evaluate the bundled CT4-blocked example
opa eval -d laas.rego -d data.json \
  -i examples/action.ct4-blocked.json \
  'data.kellerai.laas.actions.summary' --format pretty
```

`error`-severity violations block; `warning`-severity are reported.

## Status

`v0.1.0` — initial public release. Standard at Draft v1.1.

## License

Licensed under the **Apache-2.0 License**.
Full text in [`LICENSE`](LICENSE); attribution in [`NOTICE`](NOTICE).

---

### For agents

Agents reading this repository should start at [AGENTS.md](AGENTS.md), not this README.
Claude Code users: see [CLAUDE.md](CLAUDE.md), which imports `AGENTS.md`.
The agent files document the conventions, vocabulary, and contribution discipline that agents are expected to follow.
