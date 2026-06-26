@AGENTS.md

## Claude-specific notes

- **No runtime, no build.** This repo is a rego-policy artifact.
  Do not run build or test commands — there is no implementation here.
  The only verification command is `opa`.
  See `docs/agents/conventions.md`.

- **No in-repo issue tracker.** There is no beads database and no `.beads/`
  directory. Do not invoke `bd`, `bv`, or any tracker tooling.
  Work is tracked in GitHub Issues.

- **Citations.** Internal references use `file:line`.
  External references use a full bibliographic citation.
  Never assert a fact without pointing at the file that proves it.

- **Prose edits.** Use the `writing-clearly-and-concisely` skill for
  human-facing prose changes when available.

- **Staging artifacts are out of scope.** The `.claude-tmp/` directory holds
  staging-only files. These are `.gitignore`'d and must never be published.
  The `.gitignore` boundary is the source of truth for what ships.

- **Frozen content.** `conformance/**` and `docs/**` may only be changed
  with explicit maintainer approval and a semver-classified `CHANGELOG.md` entry.
