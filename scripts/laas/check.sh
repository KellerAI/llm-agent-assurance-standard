#!/usr/bin/env bash
# Runnable proof: emit a decision record from a sample effect surface, then
# (if opa is present) evaluate it against the canonical in-repo LAAS policy+data
# to prove the emitted record is actually evaluable by package kellerai.laas.actions.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
LAAS_DIR="$REPO_ROOT/conformance/laas"
EMITTER="$HERE/emitter.py"
BUNDLE="$LAAS_DIR/data.json"
POLICY="$LAAS_DIR/laas.rego"
FIXTURE="$HERE/fixtures/transfer.effect-surface.json"
OUT="$(mktemp -t laas-decision-record.XXXXXX.json)"
trap 'rm -f "$OUT"' EXIT

echo "== 1. Emit decision record from effect surface =="
python3 "$EMITTER" -i "$FIXTURE" -b "$BUNDLE" -o "$OUT"
cat "$OUT"

echo
echo "== 2. opa eval against package kellerai.laas.actions =="
if ! command -v opa >/dev/null 2>&1; then
  echo "opa ABSENT -- skipping policy evaluation (install opa to run the proof)."
  exit 0
fi

opa version | head -1

echo "-- summary --"
opa eval -f pretty -d "$POLICY" -d "$BUNDLE" -i "$OUT" \
  'data.kellerai.laas.actions.summary'

echo "-- error obligation ids --"
opa eval -f pretty -d "$POLICY" -d "$BUNDLE" -i "$OUT" \
  'data.kellerai.laas.actions.error_ids'

echo "-- compliant --"
opa eval -f pretty -d "$POLICY" -d "$BUNDLE" -i "$OUT" \
  'data.kellerai.laas.actions.compliant'
