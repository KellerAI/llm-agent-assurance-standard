#!/usr/bin/env bash
# Render the LAAS standards markdown into house-styled PDFs.
#
# Each source document is converted markdown -> HTML (pandoc) -> PDF
# (WeasyPrint) using a per-body CSS theme that emulates the visual style
# of the corresponding standards body. The themes carry NO official IEEE,
# NIST, or ISO logos, seals, or trademarks; every output is a clearly
# marked UNOFFICIAL draft rendering.
#
# Requirements: pandoc, weasyprint (both on PATH).
# Outputs land in ./out (git-ignored). Source markdown is one level up.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$(cd "$here/.." && pwd)"
themes="$here/themes"
out="$here/out"
mkdir -p "$out"

for bin in pandoc weasyprint; do
  command -v "$bin" >/dev/null 2>&1 || { echo "error: '$bin' not found on PATH" >&2; exit 1; }
done

# Minimal pandoc HTML template: no default styling, so the theme CSS is
# the single source of visual truth.
tpl="$(mktemp -t laas-tpl.XXXXXX.html)"
trap 'rm -f "$tpl"' EXIT
cat > "$tpl" <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>$title$</title>
</head>
<body>
$include-before$
$body$
$include-after$
</body>
</html>
HTML

# theme:basename pairs
for pair in "ieee:laas-ieee" "nist:laas-nist" "iso:laas-iso" "sr:laas-sr"; do
  theme="${pair%%:*}"
  base="${pair##*:}"
  md="$src/$base.md"
  html="$out/$base.html"
  pdf="$out/$base.pdf"

  [ -f "$md" ] || { echo "error: source not found: $md" >&2; exit 1; }
  [ -f "$themes/$theme.css" ] || { echo "error: theme not found: $themes/$theme.css" >&2; exit 1; }
  [ -f "$here/covers/$theme-cover.html" ] || { echo "error: cover not found: $here/covers/$theme-cover.html" >&2; exit 1; }

  echo "==> $base  (theme: $theme)"
  pandoc "$md" \
    --from gfm \
    --to html5 \
    --standalone \
    --template "$tpl" \
    --include-before-body "$here/covers/$theme-cover.html" \
    --metadata title="$base" \
    --output "$html"
  weasyprint --stylesheet "$themes/$theme.css" "$html" "$pdf"
  rm -f "$html"
  echo "    wrote $pdf"
done

echo "Done. PDFs in: $out"
