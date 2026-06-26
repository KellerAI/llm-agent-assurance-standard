# Security Policy

**llm-agent-assurance-standard** is a **rego-policy** artifact, not a running system.
A security-relevant defect here is a design choice in the artifact that — faithfully implemented — would create a vulnerability in a consuming system.
For example: a field the artifact stores in the clear that should be hashed, or wording that admits a fail-open path.

## Reporting a vulnerability

Report suspected security-relevant defects **privately**, through GitHub's
**Security Advisories** — use the *Report a vulnerability* button on this
repository's **Security** tab.
Do not open a public issue for these.

Include:

- The location in the artifact — file and section or element.
- The defect, and the failure it would produce in a faithful implementation.

You can expect an initial response within a reasonable time.
If a defect is confirmed, it is corrected in the artifact and recorded in `CHANGELOG.md`.

## Scope

This policy covers the **llm-agent-assurance-standard** artifact in this repository only.
It does not cover downstream systems that consume or implement against this artifact — the security of an implementation is the responsibility of its own maintainers.

## Supported versions

Only the current published version (`v0.1.0`) is in scope.
