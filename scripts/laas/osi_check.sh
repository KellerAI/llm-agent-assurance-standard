#!/usr/bin/env bash
# Runnable proof: OSI model -> adapter -> decision record -> opa eval, asserting
# the CT4 net_settlement_amount write is compliant under full enforcement controls.
#
# UNLIKE scripts/laas/check.sh, this script FAILS (exits non-zero) when opa is
# absent -- a proof that cannot run is not a passing proof.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
LAAS_DIR="$REPO_ROOT/conformance/laas"
CONV="$HERE/osi_to_surface.py"
BUNDLE="$LAAS_DIR/data.json"
POLICY="$LAAS_DIR/laas.rego"
MODEL="$HERE/osi/example.semantic.json"   # JSON twin -> stdlib-only, no PyYAML
RAW="$(mktemp -t osi-raw.XXXXXX.json)"
REC="$(mktemp -t osi-record.XXXXXX.json)"
trap 'rm -f "$RAW" "$REC"' EXIT

if ! command -v opa >/dev/null 2>&1; then
  echo "FAIL: opa is not on PATH -- install opa to run this proof." >&2
  exit 1
fi

echo "== 1. Adapter: OSI net_settlement_amount write -> decision record =="
python3 "$CONV" -m "$MODEL" --kind metric --name net_settlement_amount \
  --operation write --signed -b "$BUNDLE" -o "$RAW"
cat "$RAW"

echo
echo "== 2. Apply full enforcement-plane controls (human approval + trace anchors) =="
# The adapter builds the surface + CT + provenance; the deployment supplies the
# CT4 governance controls (human approval, append-only trace anchors). We add
# them here so opa eval sees a fully-conformant CT4 record.
python3 - "$RAW" "$REC" <<'PY'
import json, sys
rec = json.load(open(sys.argv[1]))
rec["human_approval"] = {"approved": True}
rec["trace"] = {"append_only": True, "actor_chain_prev_hash": "sha256:osi", "merkle_anchor": "sha256:osi"}
json.dump(rec, open(sys.argv[2], "w"), indent=2)
PY

echo "== 3. opa eval: assert compliant == true =="
RESULT="$(opa eval -f json -d "$POLICY" -d "$BUNDLE" -i "$REC" \
  'data.kellerai.laas.actions.compliant' \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d["result"][0]["expressions"][0]["value"]))')"
echo "compliant = $RESULT"
opa eval -f pretty -d "$POLICY" -d "$BUNDLE" -i "$REC" \
  'data.kellerai.laas.actions.summary'

if [ "$RESULT" != "true" ]; then
  echo "FAIL: expected compliant==true for CT4 net_settlement_amount write" >&2
  exit 1
fi
echo "PASS: CT4 net_settlement_amount write is compliant under full controls."
