# OSI-to-Surface Adapter

The OSI-to-Surface adapter (`scripts/laas/osi_to_surface.py`) converts an
Open Semantic Interchange (OSI) semantic model plus
an action reference into a LAAS `EffectSurface`, then emits a full decision record
through the canonical emitter. The pipeline is:

```text
OSI model (.json|.yaml)
  + action_ref (kind / name / operation)
  → osi_to_surface.py  (mapping only — no tier math)
  → EffectSurface
  → emitter.emit_decision_record  (CT assignment, record assembly)
  → decision record JSON
  → opa eval  (obligation evaluation, conformance verdict)
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

Model files may be JSON or YAML (`.yaml` or `.yml`). The JSON twin is preferred for
the CLI because it requires no external dependency; YAML requires PyYAML, which is a
CLI-only optional dependency (`scripts/laas/osi_to_surface.py:256-268`).

### KELLERAI_LAAS `custom_extension`

Each OSI object carries governance axes inside its `custom_extensions` list.
The adapter reads the `data` payload of the first extension whose `vendor_name` equals
`"KELLERAI_LAAS"` (`scripts/laas/osi_to_surface.py:62-67`).

`scripts/laas/osi/kellerai_laas_extension.schema.json` describes the `data` payload.
The adapter does not load that schema or check payloads against it at runtime; the
only code link between the two is the enum drift test described below:

| Field | Type | Required | Allowed values |
|-------|------|----------|---------------|
| `reversibility` | string | yes | `reversible`, `hard`, `irreversible`, `none` |
| `scope` | string | yes | `single`, `multi`, `org`, `public` |
| `consequence` | string | yes | `none`, `low`, `material`, `high` |
| `escape_rate_tolerance` | number | no | Bucket-B residual escape-rate tolerance |
| `access_sensitive` | boolean | no | When `true`, adapter coerces scope to `"public"` |

The schema sets `"additionalProperties": false`
(`scripts/laas/osi/kellerai_laas_extension.schema.json:8`), so a payload with any key
outside these five is invalid under the schema.
Because nothing enforces the schema at runtime, the adapter reads only
`reversibility`, `scope`, `consequence`, and `access_sensitive`, and ignores any
other key (`scripts/laas/osi_to_surface.py:180-189`).
It does not read `escape_rate_tolerance`; neither `osi_to_surface.py` nor
`emitter.py` contains the string `escape_rate`.
For `write` and `delete`, it treats a missing or unrecognised axis value as
undetermined (`scripts/laas/osi_to_surface.py:126-138`).

The three required axis values must be keys of the corresponding lattice entries in
`conformance/laas/data.json`. A drift test (`scripts/laas/test_osi_to_surface.py:191-203`)
asserts the schema enums equal the lattice keys whenever the unit tests run.

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

This is a synopsis, not a runnable command: `|` separates alternatives and `#`
starts a note.

```text
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

Step 1 of `scripts/laas/osi_check.sh:26-27` passes the same flags, with absolute
paths and a temporary output file.

---

## Output: the EffectSurface and decision record

### EffectSurface (internal)

`build_surface` (`scripts/laas/osi_to_surface.py:155-207`) returns an `EffectSurface`
with these fields:

| Field | Value |
|-------|-------|
| `external_effect` | `True` for `write` or `delete`; `False` for `read` |
| `reversibility` | `write`/`delete`: most-severe lattice key across blast radius, after the operation floor, or `None`; `read`: the target's own value |
| `scope` | `write`/`delete`: most-severe lattice key across blast radius, or `None`; `read`: the target's own value; `"public"` when `access_sensitive` applies |
| `consequence` | `write`/`delete`: most-severe lattice key across blast radius, or `None`; `read`: the target's own value |
| `tool` | `"osi.{kind}.{operation}:{name}"` |

A `None` on any axis means no determinable value was found.
For `write` and `delete`, `emitter.derive_ct` then returns
`default_ct_when_undetermined` from the bundle, which is 4 (CT4) in
`conformance/laas/data.json:11` (`scripts/laas/emitter.py:304-328`).
For `read`, `external_effect` is `False`, so `derive_ct` returns CT0 whatever the
axis values are (`scripts/laas/emitter.py:289-290`;
`scripts/laas/osi_to_surface.py:185`); only the unsigned-model floor below can raise it.

### Axis derivation rules

The adapter applies rules 1 and 2 only to `write` and `delete`; rule 3 applies to
every operation:

1. **Blast radius.** The adapter traverses `relationships` edges from the target
   object (cycle-safe, bounded to depth 64) and takes the most-severe value on each
   axis across all reachable objects (`scripts/laas/osi_to_surface.py:93-120,179-183`).

2. **Operation floors.** After blast-radius resolution, `write` floors `reversibility`
   to `"hard"` and `delete` floors it to `"irreversible"`, taking whichever is more
   severe (`scripts/laas/osi_to_surface.py:193-195`).

3. **`access_sensitive` coercion.** If any reachable object (for `read`, the target
   itself) sets `access_sensitive: true`, scope is overridden to `"public"` because
   OSI graph reach does not equal permission reach
   (`scripts/laas/osi_to_surface.py:183`, `:189`, `:198-199`).

For `read` operations there is no external effect; axis values are taken directly from
the target object's annotation with no blast-radius traversal or floors applied
(`scripts/laas/osi_to_surface.py:185-189`).

### Decision record (CLI output)

The CLI wraps the surface in `osi_emit_decision_record`, which calls the canonical
`emitter.emit_decision_record`. The resulting JSON is written to stdout or `--out`.
The record carries `input.trusted`, `gate.assigned_ct`, and
`aggregate.window_effect_ct` (`scripts/laas/test_osi_to_surface.py:166-188`).
The emitter always writes `aggregate.window_effect_ct` (`scripts/laas/emitter.py:408`):
it is 0 for a signed model and `untrusted_input_min_ct` for an unsigned one.
The CLI also supplies a deterministic, qualified, passing verifier (`VRF-OSI-DET`), so
the proof script can show a compliant CT4 write
(`scripts/laas/osi_to_surface.py:296-306`).

#### Unsigned-model trust floor

When `--unsigned` is passed, the adapter sets `aggregate.window_effect_ct` to
`data["laas"]["untrusted_input_min_ct"]`, read from the `--bundle` file
(default `conformance/laas/data.json`) (`scripts/laas/osi_to_surface.py:239-241`,
`:314`).
The emitter then assigns `CT = max(derived_ct, window_effect_ct)`, flooring the
assigned CT to at least that value (`scripts/laas/emitter.py:378`).

---

## Schema versioning

The `custom_extension` schema is **informally versioned**. No formal change-control
process has been established for it yet. This is a documented open question
(`AGENTS.md:130-131`, "Open questions" item 1).

The schema identifier is:

```text
$id: https://kellerai.dev/schemas/osi/kellerai_laas_extension.schema.json
```

Source: `scripts/laas/osi/kellerai_laas_extension.schema.json:3`.

The schema's per-axis `enum` lists are hand-written copies of the
`conformance/laas/data.json` tier lattice keys; nothing generates them. Any change to the
lattice must also update the schema enums; the drift test at
`scripts/laas/test_osi_to_surface.py:191-203` catches divergence at test time.
Run it with `python3 -m unittest discover scripts/laas`
(`scripts/laas/test_osi_to_surface.py:4`).

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

This differs from `scripts/laas/check.sh`, which skips the OPA step and exits 0
when `opa` is absent (`scripts/laas/check.sh:23-25`).

### Scenario

The script exercises a `write` on the `net_settlement_amount` metric from
`scripts/laas/osi/example.semantic.json` — the highest-consequence object in the
example model (`irreversible` / `org` / `high`), which maps to CT4
(`scripts/laas/osi_check.sh:26-27`; `scripts/laas/test_osi_to_surface.py:166-175`).

### Steps

```bash
bash scripts/laas/osi_check.sh
```

1. **Adapter.** Calls `osi_to_surface.py` with `--kind metric --name net_settlement_amount
   --operation write --signed`, writes the raw decision record to a temp file, and
   prints it (`scripts/laas/osi_check.sh:26-28`).

2. **Enforcement-plane controls.** A Python inline script patches the record with
   `human_approval.approved = true` and an append-only trace block
   (`scripts/laas/osi_check.sh:35-41`). These are CT4 governance controls supplied
   by the deployment; the adapter itself does not add them.

3. **`opa eval`.** Evaluates `data.kellerai.laas.actions.compliant` against the
   patched record using `conformance/laas/laas.rego` and `conformance/laas/data.json`.
   The script extracts the boolean result and also prints
   `data.kellerai.laas.actions.summary` (`scripts/laas/osi_check.sh:44-49`).

### Expected result

Steps 1 and 2 print their headings and the raw record first; the output ends with
step 3:

```text
== 3. opa eval: assert compliant == true ==
compliant = true
{
  "bundle": "laas-fin-2.0.0",
  "compliant": true,
  "effective_ct": 4,
  "errors": 0,
  "expected_ct": 4,
  "warnings": 0
}
PASS: CT4 net_settlement_amount write is compliant under full controls.
```

If `compliant` is not `true`, the script exits non-zero with a `FAIL:` message
(`scripts/laas/osi_check.sh:51-54`).
