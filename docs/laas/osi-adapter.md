# OSI-to-Surface Adapter

The OSI-to-Surface adapter (`scripts/laas/osi_to_surface.py`) converts an
[Open Semantic Interchange](https://www.osi-standard.org) (OSI) semantic model plus
an action reference into a LAAS `EffectSurface`, then emits a full decision record
through the canonical emitter. The pipeline is:

```
OSI model (.json|.yaml)
  + action_ref (kind / name / operation)
  → osi_to_surface.py  (mapping only — no tier math)
  → EffectSurface
  → emitter.emit_decision_record  (CT assignment, obligation set)
  → decision record JSON
  → opa eval  (conformance verdict)
```

No consequence-tier math lives in the adapter. CT assignment is owned by
`emitter.derive_ct` and `conformance/laas/laas.rego`. The adapter only maps OSI
semantics to gate-observable axis values (`scripts/laas/osi_to_surface.py:1-11`).

---

## Input: the OSI model and `custom_extension`

### OSI model structure

The adapter accepts an OSI model with three top-level collections:

| Key | Description |
|-----|-------------|
| `datasets` | Named dataset objects, each optionally annotated |
| `metrics` | Named metric objects, each optionally annotated |
| `relationships` | Directed edges `{from, to}` used for blast-radius traversal |

Model files may be JSON or YAML. The JSON twin is preferred for the CLI because it
requires no external dependency; YAML requires PyYAML, which is a CLI-only optional
dependency (`scripts/laas/osi_to_surface.py:256-268`).

### KELLERAI_LAAS `custom_extension`

Each OSI object carries governance axes inside its `custom_extensions` list.
The adapter reads extensions whose `vendor_name` equals `"KELLERAI_LAAS"`
(`scripts/laas/osi_to_surface.py:62-67`).

The `data` payload is validated against
`scripts/laas/osi/kellerai_laas_extension.schema.json`:

| Field | Type | Required | Allowed values |
|-------|------|----------|---------------|
| `reversibility` | string | yes | `reversible`, `hard`, `irreversible`, `none` |
| `scope` | string | yes | `single`, `multi`, `org`, `public` |
| `consequence` | string | yes | `none`, `low`, `material`, `high` |
| `escape_rate_tolerance` | number | no | Bucket-B residual escape-rate tolerance |
| `access_sensitive` | boolean | no | When `true`, adapter coerces scope to `"public"` |

The three required axis values must be keys of the corresponding lattice entries in
`conformance/laas/data.json`. A drift test (`scripts/laas/test_osi_to_surface.py:191-203`)
asserts the schema enums equal the lattice keys at all times.

### Action reference

The CLI builds the action reference from `--kind`, `--name`, and `--operation`.
Internally it is the dict `{"kind": ..., "name": ..., "operation": ...}`.

### Worked example

`scripts/laas/osi/example.semantic.json` (and its YAML twin
`scripts/laas/osi/example.semantic.yaml`) demonstrate the expected structure:

```json
{
  "osi_version": "0.1.0",
  "name": "example_settlement_model",
  "datasets": [
    {
      "name": "orders",
      "custom_extensions": [
        {"vendor_name": "KELLERAI_LAAS",
         "data": {"reversibility": "hard", "scope": "multi", "consequence": "material"}}
      ]
    },
    {
      "name": "customers",
      "custom_extensions": [
        {"vendor_name": "KELLERAI_LAAS",
         "data": {"reversibility": "reversible", "scope": "single",
                  "consequence": "none", "access_sensitive": false}}
      ]
    }
  ],
  "metrics": [
    {
      "name": "net_settlement_amount",
      "custom_extensions": [
        {"vendor_name": "KELLERAI_LAAS",
         "data": {"reversibility": "irreversible", "scope": "org", "consequence": "high"}}
      ]
    }
  ],
  "relationships": [
    {"from": "orders", "to": "customers"}
  ]
}
```

---

## CLI usage

All four of `--model`, `--kind`, `--name`, and `--operation` are required.
The remainder are optional with the defaults shown.

```bash
python3 scripts/laas/osi_to_surface.py \
  -m  | --model     <path.json|.yaml>          # OSI model file (required)
        --kind       dataset | metric           # object type (required)
        --name       <object-name>              # object name within model (required)
        --operation  read | write | delete      # action to evaluate (required)
       [--signed]                               # mark model trusted (default)
       [--unsigned]                             # mark model untrusted
       [--actor-id       <id>]                  # default: agent.osi.demo
       [--actor-lineage  <lineage>]             # default: osi-demo-lineage
  -b  | --bundle    <data.json>                 # lattice bundle (default: conformance/laas/data.json)
  -o  | --out       <output.json>               # write record here (default: stdout)
```

Source: `scripts/laas/osi_to_surface.py:274-287`.

### Example invocation

```bash
python3 scripts/laas/osi_to_surface.py \
  -m scripts/laas/osi/example.semantic.json \
  --kind metric \
  --name net_settlement_amount \
  --operation write \
  --signed \
  -b conformance/laas/data.json \
  -o /tmp/record.json
```

This is the same invocation used in step 1 of `scripts/laas/osi_check.sh:26-27`.

---

## Output: the EffectSurface and decision record

### EffectSurface (internal)

`build_surface` (`scripts/laas/osi_to_surface.py:155-207`) returns an `EffectSurface`
with these fields:

| Field | Value |
|-------|-------|
| `external_effect` | `True` for `write` or `delete`; `False` for `read` |
| `reversibility` | Most-severe lattice key across blast radius, or `None` |
| `scope` | Most-severe lattice key across blast radius, or `None` |
| `consequence` | Most-severe lattice key across blast radius, or `None` |
| `tool` | `"osi.{kind}.{operation}:{name}"` |

A `None` on any axis means no determinable value was found; the emitter defaults
such cases to the highest CT (CT4).

### Axis derivation rules

The adapter applies three rules when building the surface for write/delete operations:

1. **Blast radius.** The adapter traverses `relationships` edges from the target
   object (cycle-safe, bounded to depth 64) and takes the most-severe value on each
   axis across all reachable objects (`scripts/laas/osi_to_surface.py:93-120,179-183`).

2. **Operation floors.** After blast-radius resolution, `write` floors `reversibility`
   to `"hard"` and `delete` floors it to `"irreversible"`, taking whichever is more
   severe (`scripts/laas/osi_to_surface.py:193-195`).

3. **`access_sensitive` coercion.** If any reachable object sets `access_sensitive: true`,
   scope is overridden to `"public"` because OSI graph reach does not equal permission
   reach (`scripts/laas/osi_to_surface.py:198-199`).

For `read` operations there is no external effect; axis values are taken directly from
the target object's annotation with no blast-radius traversal or floors applied
(`scripts/laas/osi_to_surface.py:185-189`).

### Decision record (CLI output)

The CLI wraps the surface in `osi_emit_decision_record`, which calls the canonical
`emitter.emit_decision_record`. The resulting JSON is written to stdout or `--out`.
The record carries at minimum `input.trusted`, `gate.assigned_ct`, and (when the
model is unsigned) `aggregate.window_effect_ct`, as verified by
`scripts/laas/test_osi_to_surface.py:166-188`.

#### Unsigned-model trust floor

When `--unsigned` is passed, the adapter sets `aggregate.window_effect_ct` to
`data["laas"]["untrusted_input_min_ct"]` (loaded from `conformance/laas/data.json`).
The emitter then assigns `CT = max(derived_ct, window_effect_ct)`, flooring the
assigned CT to at least that value (`scripts/laas/osi_to_surface.py:239-241`).

---

## Schema versioning

The `custom_extension` schema is **informally versioned**. No formal change-control
process has been established for it yet. This is a documented open question
(`AGENTS.md:117-118`).

The schema identifier is:

```
$id: https://kellerai.dev/schemas/osi/kellerai_laas_extension.schema.json
```

Source: `scripts/laas/osi/kellerai_laas_extension.schema.json:4`.

The schema's per-axis `enum` values are not maintained independently — they are
derived from `conformance/laas/data.json` tier lattice keys. Any change to the
lattice must also update the schema enums; the drift test at
`scripts/laas/test_osi_to_surface.py:191-203` catches divergence at test time.

Anyone extending the schema or adding axes should surface the change as a proposal
before merging, since no versioning mechanism is in place to signal breaking changes
to adopters.

---

## End-to-end proof: `osi_check.sh`

`scripts/laas/osi_check.sh` runs the full OSI-to-verdict pipeline and asserts
`compliant == true` for a CT4 scenario.

### Dependency

`opa` must be on `PATH`. The script **exits non-zero** if it is absent — by design,
a proof that cannot run is not a passing proof (`scripts/laas/osi_check.sh:20-23`):

```bash
if ! command -v opa >/dev/null 2>&1; then
  echo "FAIL: opa is not on PATH -- install opa to run this proof." >&2
  exit 1
fi
```

This differs from `scripts/laas/check.sh`, which skips the OPA step when `opa` is
absent.

### Scenario

The script exercises a `write` on the `net_settlement_amount` metric from
`scripts/laas/osi/example.semantic.json` — the highest-consequence object in the
example model (`irreversible` / `org` / `high`), which maps to CT4
(`scripts/laas/osi_check.sh:26-27`).

### Steps

```bash
bash scripts/laas/osi_check.sh
```

1. **Adapter.** Calls `osi_to_surface.py` with `--kind metric --name net_settlement_amount
   --operation write --signed` and writes the raw decision record to a temp file.

2. **Enforcement-plane controls.** A Python inline script patches the record with
   `human_approval.approved = true` and an append-only trace block
   (`scripts/laas/osi_check.sh:35-41`). These are CT4 governance controls supplied
   by the deployment; the adapter itself does not add them.

3. **`opa eval`.** Evaluates `data.kellerai.laas.actions.compliant` against the
   patched record using `conformance/laas/laas.rego` and `conformance/laas/data.json`.
   The script extracts the boolean result and also prints
   `data.kellerai.laas.actions.summary` (`scripts/laas/osi_check.sh:44-49`).

### Expected result

```
compliant = true
PASS: CT4 net_settlement_amount write is compliant under full controls.
```

If `compliant` is not `true`, the script exits non-zero with a `FAIL:` message
(`scripts/laas/osi_check.sh:51-54`).
