// Commit message linting — Conventional Commits.
// Enforced as a hard gate by .github/workflows/commitlint.yml.
// The <= 50-character subject convention is documented for contributors in
// docs/agents/conventions.md; it is not enforced as a build-breaking rule so
// that Dependabot's generated commit messages cannot deadlock CI.
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'subject-case': [0], // disabled — agents author headers with proper-cased terms/acronyms
  },
};
