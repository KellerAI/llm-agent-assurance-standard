// Commit message linting — Conventional Commits.
// Enforced as a hard gate by .github/workflows/commitlint.yml.
// The <= 50-character subject convention is documented for contributors in
// docs/agents/conventions.md; it is not enforced as a build-breaking rule so
// that Dependabot's generated commit messages cannot deadlock CI.

// Dependabot bump headers embed full action paths and 40-character SHAs, so
// they routinely exceed header-max-length (100). commitlint's built-in ignores
// (defaultIgnores, left on) cover merges, reverts and semver-only chores, not
// this form. A message is ignored only when BOTH signals are present:
//   1. the header is exactly Dependabot's bump form (prefix `chore`, no scope,
//      per .github/dependabot.yml), optionally ending in " (#N)", which is the
//      form GitHub writes when a Dependabot PR is squash-merged; and
//   2. the body carries Dependabot's own sign-off trailer on its own line.
// A hand-written header that copies the bump shape without the trailer is
// still linted. Note: an ignored squash commit skips linting for every commit
// folded into it. Tests: scripts/test-commitlint-config.sh
const DEPENDABOT_HEADER = /^chore: bump \S+ from \S+ to \S+( \(#\d+\))?$/;
const DEPENDABOT_TRAILER = /^Signed-off-by: dependabot\[bot\] <support@github\.com>$/m;

const isDependabotBump = (message) => {
  const text = String(message).replace(/\r\n/g, '\n');
  const header = text.split('\n', 1)[0];
  return DEPENDABOT_HEADER.test(header) && DEPENDABOT_TRAILER.test(text);
};

module.exports = {
  extends: ['@commitlint/config-conventional'],
  ignores: [isDependabotBump],
  rules: {
    'subject-case': [0], // disabled — agents author headers with proper-cased terms/acronyms
  },
};
