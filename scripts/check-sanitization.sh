#!/usr/bin/env bash
# Sanitization regression gate for llm-agent-assurance-standard.
#
# The internal-term denylist is base64-encoded so this script does not itself
# republish the strings it exists to keep out — a plaintext denylist would be
# indexed by code search. It is decoded only at runtime, into a temp file.
#
# Every publishable file is scanned for every denied term. Files excluded from
# publication (matched by .gitignore: .claude-tmp/, node_modules/) are not
# scanned. Exits non-zero on any match.
#
# IMPORTANT: Replace the DENYLIST_B64 value with the base64-encoded denylist
# for THIS repository. The placeholder below encodes only a minimal stub.
# Generate with: printf 'term1\nterm2\n' | base64
set -euo pipefail

cd "$(dirname "$0")/.."

# Replace this with the repo-specific base64-encoded denylist.
# Stub encodes a comment line only.
DENYLIST_B64='IyBSZXBsYWNlIHdpdGggcmVwby1zcGVjaWZpYyBkZW55bGlzdAo='

patterns_file="$(mktemp)"
trap 'rm -f "$patterns_file"' EXIT
printf '%s' "$DENYLIST_B64" | base64 -d > "$patterns_file"

list_files() {
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files -z
  else
    find . \
      \( -path ./.git -o -path ./.claude -o -path ./.claude-tmp \
         -o -path ./node_modules -o -path ./.venv \) -prune -o \
      -type f \
      ! -name '*.bak' ! -name '*.bak.md' ! -name '.DS_Store' \
      -print0
  fi
}

if list_files | PATTERNS="$patterns_file" LC_ALL=C perl -0 -ne '
  BEGIN {
    open my $pf, "<", $ENV{PATTERNS} or die "cannot read patterns file\n";
    while (<$pf>) { chomp; next unless length; next if /^\s*#/; push @P, qr/$_/ }
    close $pf;
    $hit = 0;
  }
  my $file = $_;
  open my $fh, "<", $file or next;
  {
    local $/ = "\n";
    while (my $line = <$fh>) {
      for my $re (@P) {
        if ($line =~ $re) { printf "LEAK  %s:%d\n", $file, $.; $hit = 1; }
      }
    }
  }
  close $fh;
  END { exit($hit ? 1 : 0); }
'; then
  echo "check-sanitization: OK — no denied terms in the publishable tree"
else
  echo "check-sanitization: FAILED — denied terms found (see LEAK lines above)"
  exit 1
fi
