#!/usr/bin/env bash
# Proves both sides of the Dependabot ignore in commitlint.config.js, using the
# same unpinned npx invocation as .github/workflows/commitlint.yml.
# Run from the repo root: bash scripts/test-commitlint-config.sh
set -u
cd "$(dirname "$0")/.."

lint() {
  npx --yes --package @commitlint/cli --package @commitlint/config-conventional \
    commitlint >/dev/null 2>&1
}

fail=0
expect() { # expect <pass|fail> <name> ; message on stdin
  local want="$1" name="$2" got
  if lint; then got=pass; else got=fail; fi
  if [ "$got" = "$want" ]; then echo "ok   $name ($got)"; else echo "FAIL $name (want $want, got $got)"; fail=1; fi
}

SHA1=beaa1ffe080944b46d2f48c563e241809e35ee17
SHA2=8c0f533df8d19f1ebbb560b31021436c05ff537d
BUMP="chore: bump jonathan-kellerai/kellerai-oss-template/.github/workflows/conformance.yml from $SHA1 to $SHA2 (#6)"
TRAILER="Signed-off-by: dependabot[bot] <support@github.com>"
HUMAN101="docs: $(printf 'x%.0s' $(seq 1 95))"

[ "${#BUMP}" -eq 180 ] || { echo "fixture: bump header is ${#BUMP} chars, want 180"; exit 2; }
[ "${#HUMAN101}" -eq 101 ] || { echo "fixture: human header is ${#HUMAN101} chars, want 101"; exit 2; }

printf '%s\n\nBumps the conformance workflow.\n\n%s\n' "$BUMP" "$TRAILER" \
  | expect pass "180-char Dependabot squash header with sign-off trailer"
printf '%s\n' "$HUMAN101" \
  | expect fail "101-char human header"
printf '%s\n\nHand-written, no Dependabot trailer.\n' "$BUMP" \
  | expect fail "180-char bump-shaped header without trailer"
printf 'docs: %s\n\n%s\n' "$(printf 'y%.0s' $(seq 1 120))" "$TRAILER" \
  | expect fail "126-char non-bump header with Dependabot trailer"
printf '%s\n\n> %s\n' "$BUMP" "$TRAILER" \
  | expect fail "bump header with trailer quoted, not on its own line"

exit "$fail"
