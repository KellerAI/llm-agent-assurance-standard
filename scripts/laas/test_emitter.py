#!/usr/bin/env python3
"""Stdlib unittest for the emitter CLI's JSON-load error handling (emitter.py).

Run: python3 -m unittest discover scripts/laas

Each test runs the real CLI in a subprocess, so the exit code and stderr are
what a caller of `python3 emitter.py` observes.
- positive: the transfer fixture plus the real data.json still emits a record.
- negative: an unreadable, malformed, non-UTF-8, too-deep, or wrong-shape
  effect-surface spec (file or stdin) exits 2 with a one-line message naming
  the spec source, and emits no record.
- negative: a malformed, non-UTF-8, incomplete, or wrong-shape data.json, or
  one whose lattice entry or default CT is the wrong shape where derive_ct
  reads it, exits 2 with a one-line message naming the bundle file (fail
  closed, no fallback to defaults, no traceback).
- positive: values the pre-check emitter emitted or validated keep that
  behaviour, byte for byte: a bad lattice entry or default CT that the spec
  never reaches still emits. Only inputs that used to crash become input
  errors, and the original's exit-2 messages are unchanged.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_EMITTER = os.path.join(_HERE, "emitter.py")
_FIXTURE = os.path.join(_HERE, "fixtures", "transfer.effect-surface.json")
_DATA_JSON = os.path.join(_HERE, "..", "..", "conformance", "laas", "data.json")


def _run(*args):
    return subprocess.run(
        [sys.executable, _EMITTER, *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _run_stdin(data, *args):
    """Run the CLI with raw bytes on stdin; return a text CompletedProcess."""
    raw = subprocess.run(
        [sys.executable, _EMITTER, *args],
        input=data,
        capture_output=True,
        check=False,
        timeout=60,
    )
    return subprocess.CompletedProcess(
        raw.args,
        raw.returncode,
        stdout=raw.stdout.decode("utf-8", errors="replace"),
        stderr=raw.stderr.decode("utf-8", errors="replace"),
    )


def _fixture_spec():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _bundle_with(**laas_updates):
    """Return the real data.json text with `laas` keys replaced."""
    with open(_DATA_JSON, encoding="utf-8") as fh:
        blob = json.load(fh)
    blob["laas"].update(laas_updates)
    return json.dumps(blob)


_DROP = object()

# External effect with scope undetermined: derive_ct returns the bundle's
# default CT and never compares the lattice values (max(axis_cts) unused).
_UNDET_SPEC = {
    "effect_surface": {
        "external_effect": True,
        "reversibility": "reversible",
        "consequence": "low",
    }
}


def _real_lattice():
    """Return a fresh copy of the real data.json tier_lattice."""
    with open(_DATA_JSON, encoding="utf-8") as fh:
        return json.load(fh)["laas"]["tier_lattice"]


def _lattice_with(axis, key, value=_DROP):
    """Return the real tier_lattice with one entry set (or dropped)."""
    lattice = _real_lattice()
    if value is _DROP:
        del lattice[axis][key]
    else:
        lattice[axis][key] = value
    return lattice


class TestEmitterCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _write(self, name, text):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def _write_bytes(self, name, data):
        path = os.path.join(self._tmp.name, name)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def _assert_input_error(self, proc, path):
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertNotIn("Traceback", proc.stderr)
        lines = proc.stderr.strip().splitlines()
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertTrue(lines[0].startswith("EMITTER INPUT ERROR:"), lines[0])
        self.assertIn(path, lines[0])

    def test_valid_fixture_emits_record(self):
        proc = _run("-i", _FIXTURE, "-b", _DATA_JSON)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        try:
            record = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            self.fail(f"emitter stdout is not JSON ({e}): {proc.stdout!r}")
        self.assertEqual(record["action"]["id"], "act_7c31")
        self.assertEqual(record["gate"]["assigned_ct"], 4)

    def test_malformed_spec_exits_2(self):
        spec = self._write("bad.effect-surface.json", '{"effect_surface": {')
        proc = _run("-i", spec, "-b", _DATA_JSON)
        self._assert_input_error(proc, spec)
        self.assertIn("invalid JSON", proc.stderr)

    def test_malformed_bundle_exits_2(self):
        bundle = self._write("bad.data.json", '{"laas": ')
        proc = _run("-i", _FIXTURE, "-b", bundle)
        self._assert_input_error(proc, bundle)
        self.assertIn("invalid JSON", proc.stderr)

    def test_bundle_missing_laas_key_exits_2(self):
        bundle = self._write("nolaas.data.json", '{"tier_lattice": {}}')
        proc = _run("-i", _FIXTURE, "-b", bundle)
        self._assert_input_error(proc, bundle)
        self.assertIn("'laas'", proc.stderr)

    def test_bundle_unreadable_exits_2(self):
        bundle = os.path.join(self._tmp.name, "absent.data.json")
        proc = _run("-i", _FIXTURE, "-b", bundle)
        self._assert_input_error(proc, bundle)

    def test_bundle_not_utf8_exits_2(self):
        bundle = self._write_bytes("binary.data.json", b"\xff\xfe")
        proc = _run("-i", _FIXTURE, "-b", bundle)
        self._assert_input_error(proc, bundle)
        self.assertIn("cannot read bundle", proc.stderr)

    def _spec_file(self, spec_obj):
        return self._write("case.effect-surface.json", json.dumps(spec_obj))

    def test_bundle_wrong_shape_exits_2(self):
        # Valid JSON of the wrong shape must fail closed, not crash. The
        # fixture has an external effect, so derive_ct reads the lattice.
        cases = {
            "top-level list": ("[]", "expected a JSON object"),
            "laas not object": ('{"laas": []}', "laas must be a JSON object"),
            # The original emitter's message, unchanged.
            "lattice missing": ('{"laas": {}}', "missing key 'tier_lattice'"),
            "lattice not object": (
                '{"laas": {"tier_lattice": 5}}',
                "laas.tier_lattice must be a JSON object",
            ),
            "lattice missing axis": (
                '{"laas": {"tier_lattice": {}}}',
                "missing key 'laas.tier_lattice.reversibility'",
            ),
            "axis not object": (
                '{"laas": {"tier_lattice": {"reversibility": [],'
                ' "scope": {}, "consequence": {}}}}',
                "laas.tier_lattice.reversibility must be a JSON object",
            ),
        }
        for name, (text, reason) in cases.items():
            with self.subTest(name):
                bundle = self._write("shape.data.json", text)
                proc = _run("-i", _FIXTURE, "-b", bundle)
                self._assert_input_error(proc, bundle)
                self.assertIn(reason, proc.stderr)

    def test_bundle_shape_unread_still_emits(self):
        # With no external effect derive_ct returns CT0 before it reads the
        # lattice or the default CT, so the original emitter emitted these.
        # The record must be byte-identical to the one from the real bundle.
        spec_obj = _fixture_spec()
        spec_obj["effect_surface"]["external_effect"] = False
        spec = self._spec_file(spec_obj)
        expected = _run("-i", spec, "-b", _DATA_JSON)
        self.assertEqual(expected.returncode, 0, expected.stderr)
        cases = {
            "lattice list": {"tier_lattice": []},
            "lattice number": {"tier_lattice": 5},
            "lattice missing axis": {
                "tier_lattice": {"reversibility": {}, "consequence": {}}
            },
            "axis list": {"tier_lattice": {**_real_lattice(), "scope": []}},
            "axis string": {"tier_lattice": {**_real_lattice(), "scope": "public"}},
            "default ct string": {"default_ct_when_undetermined": "x"},
            "lattice value string": {
                "tier_lattice": _lattice_with("scope", "public", "x")
            },
            "axis without worst key": {
                "tier_lattice": _lattice_with("scope", "public")
            },
        }
        for name, updates in cases.items():
            with self.subTest(name):
                bundle = self._write("unread.data.json", _bundle_with(**updates))
                proc = _run("-i", spec, "-b", bundle)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stderr, "")
                self.assertEqual(proc.stdout, expected.stdout)

    def test_bundle_bad_values_exit_2(self):
        # A bad value exits 2 only where derive_ct reaches it, which is where
        # the original emitter crashed: a non-number default CT on an
        # undetermined axis, a non-number lattice value the spec selects on a
        # fully determined surface, or a missing §6.2 worst key it falls
        # back to.
        undet = self._spec_file(_UNDET_SPEC)
        dct = "laas.default_ct_when_undetermined must be a number"
        cases = {
            "default ct string": (
                undet,
                {"default_ct_when_undetermined": "x"},
                dct,
            ),
            "default ct null": (
                undet,
                {"default_ct_when_undetermined": None},
                dct,
            ),
            "default ct list": (undet, {"default_ct_when_undetermined": []}, dct),
            "selected lattice value string": (
                _FIXTURE,
                {"tier_lattice": _lattice_with("scope", "public", "x")},
                "laas.tier_lattice.scope.public must be a number",
            ),
            "selected lattice value null": (
                _FIXTURE,
                {"tier_lattice": _lattice_with("consequence", "high", None)},
                "laas.tier_lattice.consequence.high must be a number",
            ),
            "worst key needed by unrecognized key": (
                _FIXTURE,
                {"tier_lattice": _lattice_with("scope", "public")},
                "laas.tier_lattice.scope must include 'public'",
            ),
            "worst key needed by undetermined axis": (
                undet,
                {"tier_lattice": _lattice_with("scope", "public")},
                "laas.tier_lattice.scope must include 'public'",
            ),
        }
        for name, (spec, updates, reason) in cases.items():
            with self.subTest(name):
                bundle = self._write("values.data.json", _bundle_with(**updates))
                proc = _run("-i", spec, "-b", bundle)
                self._assert_input_error(proc, bundle)
                self.assertIn(reason, proc.stderr)

    def test_bundle_unused_bad_values_still_emit(self):
        # A bad value derive_ct never compares is not an input error: the
        # original emitter emitted these, and the record must be identical
        # to the one from the real bundle.
        undet = self._spec_file(_UNDET_SPEC)
        cases = {
            "default ct string, surface determined": (
                _FIXTURE,
                {"default_ct_when_undetermined": "x"},
            ),
            "default ct null, surface determined": (
                _FIXTURE,
                {"default_ct_when_undetermined": None},
            ),
            "default ct list, surface determined": (
                _FIXTURE,
                {"default_ct_when_undetermined": []},
            ),
            "unselected lattice value string": (
                _FIXTURE,
                {"tier_lattice": _lattice_with("scope", "single", "x")},
            ),
            "selected lattice value string, axis undetermined": (
                undet,
                {"tier_lattice": _lattice_with("scope", "public", "x")},
            ),
            "selected lattice value null, axis undetermined": (
                undet,
                {"tier_lattice": _lattice_with("scope", "public", None)},
            ),
            "worst key not needed, surface determined": (
                _FIXTURE,
                {"tier_lattice": _lattice_with("reversibility", "none")},
            ),
            "worst key not needed, other axis undetermined": (
                undet,
                {"tier_lattice": _lattice_with("consequence", "high")},
            ),
        }
        for name, (spec, updates) in cases.items():
            with self.subTest(name):
                expected = _run("-i", spec, "-b", _DATA_JSON)
                self.assertEqual(expected.returncode, 0, expected.stderr)
                bundle = self._write("unused.data.json", _bundle_with(**updates))
                proc = _run("-i", spec, "-b", bundle)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stderr, "")
                self.assertEqual(proc.stdout, expected.stdout)

    def test_bundle_error_reported_before_spec_shape(self):
        # The original loaded the bundle before it read the spec's keys, so
        # a bundle it rejected wins over a wrong-shape spec.
        spec_obj = _fixture_spec()
        spec_obj["verifier"] = 1
        spec = self._spec_file(spec_obj)
        for name, (text, reason) in {
            "no laas": ('{"tier_lattice": {}}', "missing key 'laas'"),
            "no tier_lattice": ('{"laas": {}}', "missing key 'tier_lattice'"),
        }.items():
            with self.subTest(name):
                bundle = self._write("first.data.json", text)
                proc = _run("-i", spec, "-b", bundle)
                self._assert_input_error(proc, bundle)
                self.assertIn(reason, proc.stderr)

    def test_bundle_values_keep_original_behaviour(self):
        # Values the original emitter emitted or validated are not input
        # errors: range and bool are left to validate_emitted / the policy.
        def run_bundle(**updates):
            bundle = self._write("ok.data.json", _bundle_with(**updates))
            return _run("-i", _FIXTURE, "-b", bundle)

        for name, updates in {
            "default ct bool": {"default_ct_when_undetermined": True},
            "default ct 9": {"default_ct_when_undetermined": 9},
            "default ct -1": {"default_ct_when_undetermined": -1},
            "lattice value bool": {
                "tier_lattice": _lattice_with("scope", "single", True)
            },
        }.items():
            with self.subTest(name):
                proc = run_bundle(**updates)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)["gate"]["assigned_ct"], 4)
        with self.subTest("bundle_id list"):
            proc = run_bundle(bundle_id=[1])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["gate"]["bundle_version"], [1])
        with self.subTest("lattice value 5 reaches validation"):
            proc = run_bundle(tier_lattice=_lattice_with("scope", "public", 5))
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertEqual(proc.stdout, "")
            self.assertTrue(
                proc.stderr.startswith("EMITTER VALIDATION FAILED:"), proc.stderr
            )

    def test_bundle_too_deep_exits_2(self):
        bundle = self._write("deep.data.json", "[" * 200000 + "]" * 200000)
        proc = _run("-i", _FIXTURE, "-b", bundle)
        self._assert_input_error(proc, bundle)
        self.assertIn("invalid JSON", proc.stderr)

    def test_spec_unreadable_exits_2(self):
        spec = os.path.join(self._tmp.name, "absent.effect-surface.json")
        proc = _run("-i", spec, "-b", _DATA_JSON)
        self._assert_input_error(proc, spec)
        self.assertIn(
            f"cannot read spec {spec}: No such file or directory", proc.stderr
        )

    def test_spec_not_utf8_exits_2(self):
        spec = self._write_bytes("binary.effect-surface.json", b"\xff\xfe")
        proc = _run("-i", spec, "-b", _DATA_JSON)
        self._assert_input_error(proc, spec)
        self.assertIn("cannot read spec", proc.stderr)

    def test_stdin_not_utf8_exits_2(self):
        proc = _run_stdin(b"\xff\xfe", "-b", _DATA_JSON)
        self._assert_input_error(proc, "<stdin>")
        self.assertIn("cannot read spec", proc.stderr)

    def test_spec_too_deep_exits_2(self):
        spec = self._write("deep.effect-surface.json", "[" * 200000 + "]" * 200000)
        proc = _run("-i", spec, "-b", _DATA_JSON)
        self._assert_input_error(proc, spec)
        self.assertIn("invalid JSON", proc.stderr)

    def test_spec_too_deep_to_serialise_exits_2(self):
        # effect_surface.tool sits one level deeper in the record than in the
        # spec, so a tool nested just under the parse limit parses but the
        # record does not serialise. The original crashed with RecursionError
        # "while encoding". The limit is the interpreter's C recursion limit
        # (tool depth 9996 on CPython 3.13.9), so scan down from above it:
        # every depth must be an input error until the encoding one is found.
        def spec_text(depth, **surface):
            spec = _fixture_spec()
            spec["effect_surface"].update(surface, tool="@@")
            return json.dumps(spec).replace('"@@"', "[" * depth + "]" * depth)

        spec = None
        for depth in range(10000, 9900, -1):
            spec = self._write("deep-tool.effect-surface.json", spec_text(depth))
            proc = _run("-i", spec, "-b", _DATA_JSON)
            self._assert_input_error(proc, spec)
            if "encoding" in proc.stderr:
                break
        else:
            self.fail("no tool depth reached the record-serialisation limit")
        self.assertIn("too deeply nested to serialise", proc.stderr)
        with self.subTest("stdin"):
            proc = _run_stdin(spec_text(depth).encode(), "-b", _DATA_JSON)
            self._assert_input_error(proc, "<stdin>")
        with self.subTest("no bundle"):
            proc = _run("-i", spec)
            self._assert_input_error(proc, spec)
        with self.subTest("external_effect false still serialises tool"):
            text = spec_text(depth, external_effect=False)
            noext = self._write("deep-noext.effect-surface.json", text)
            proc = _run("-i", noext, "-b", _DATA_JSON)
            self._assert_input_error(proc, noext)
            self.assertIn("encoding", proc.stderr)
        with self.subTest("top-level id lands at action.id"):
            body = _fixture_spec()
            body.pop("action", None)
            body["id"] = "@@"
            nest = "[" * (depth + 1) + "]" * (depth + 1)
            deep_id = self._write(
                "deep-id.effect-surface.json",
                json.dumps(body).replace('"@@"', nest),
            )
            proc = _run("-i", deep_id, "-b", _DATA_JSON)
            self._assert_input_error(proc, deep_id)
            self.assertIn("encoding", proc.stderr)

    def test_int_over_digit_limit_exits_2(self):
        # A JSON integer over sys.get_int_max_str_digits() (4300 by default)
        # made json.loads raise a bare ValueError the original did not catch.
        digits = "9" * (sys.get_int_max_str_digits() + 700)
        spec_text = json.dumps(dict(_fixture_spec(), residual_error_bound="@@"))
        spec_text = spec_text.replace('"@@"', digits)
        with self.subTest("spec file"):
            spec = self._write("bigint.effect-surface.json", spec_text)
            proc = _run("-i", spec, "-b", _DATA_JSON)
            self._assert_input_error(proc, spec)
            self.assertIn("invalid JSON", proc.stderr)
            self.assertIn("integer string conversion", proc.stderr)
        with self.subTest("stdin"):
            proc = _run_stdin(spec_text.encode(), "-b", _DATA_JSON)
            self._assert_input_error(proc, "<stdin>")
            self.assertIn("invalid JSON", proc.stderr)
        with self.subTest("bundle"):
            text = _bundle_with(unused_big="@@").replace('"@@"', digits)
            bundle = self._write("bigint.data.json", text)
            proc = _run("-i", _FIXTURE, "-b", bundle)
            self._assert_input_error(proc, bundle)
            self.assertIn("invalid JSON", proc.stderr)
            self.assertIn("integer string conversion", proc.stderr)
        with self.subTest("an int at the limit still emits"):
            at_limit = "9" * sys.get_int_max_str_digits()
            spec = self._write(
                "limit.effect-surface.json", spec_text.replace(digits, at_limit)
            )
            proc = _run("-i", spec, "-b", _DATA_JSON)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(f'"residual_error_bound": {at_limit},', proc.stdout)

    def test_spec_wrong_shape_exits_2(self):
        # Every one of these used to end in a traceback (exit 1), except the
        # falsy non-object verifier, which used to fall back to the
        # placeholder verifier.
        def spec_with(**updates):
            spec = _fixture_spec()
            spec.update(updates)
            return spec

        def surface_with(**updates):
            spec = _fixture_spec()
            spec["effect_surface"].update(updates)
            return spec

        verifier = _fixture_spec()["verifier"]
        no_id = {k: v for k, v in verifier.items() if k != "id"}
        obj = "must be a JSON object"
        cases = {
            "top-level list": ([], "expected a JSON object"),
            "no effect_surface": ({"id": "x"}, "missing key 'effect_surface'"),
            "effect_surface list": (
                {"effect_surface": []},
                "effect_surface " + obj,
            ),
            "effect_surface null": (
                {"effect_surface": None},
                "effect_surface " + obj,
            ),
            "no external_effect": (
                {"effect_surface": {}},
                "missing key 'effect_surface.external_effect'",
            ),
            "axis list": (
                surface_with(reversibility=[]),
                "effect_surface.reversibility must be a JSON scalar",
            ),
            "axis object": (
                surface_with(scope={}),
                "effect_surface.scope must be a JSON scalar",
            ),
            "actor list": (spec_with(actor=[]), "actor " + obj),
            "actor null": (spec_with(actor=None), "actor " + obj),
            "aggregate list": (spec_with(aggregate=[]), "aggregate " + obj),
            "vendor list": (spec_with(vendor=[]), "vendor " + obj),
            "input list": (spec_with(input=[]), "input " + obj),
            "trace list": (spec_with(trace=[]), "trace " + obj),
            "human_approval list": (
                spec_with(human_approval=[]),
                "human_approval " + obj,
            ),
            "action null": (spec_with(action=None), "action " + obj),
            "verifier list": (
                spec_with(verifier=[1]),
                "verifier must be a JSON object",
            ),
            "verifier string": (
                spec_with(verifier="x"),
                "verifier must be a JSON object",
            ),
            "verifier true": (
                spec_with(verifier=True),
                "verifier must be a JSON object",
            ),
            "verifier without id": (
                spec_with(verifier=no_id),
                "missing key 'verifier.id'",
            ),
            "verifier verdict list": (
                spec_with(verifier={**verifier, "verdict": []}),
                "verifier.verdict must be a JSON scalar",
            ),
            "verifier type object": (
                spec_with(verifier={**verifier, "type": {}}),
                "verifier.type must be a JSON scalar",
            ),
            "window ct string": (
                spec_with(aggregate={"window_effect_ct": "x"}),
                "aggregate.window_effect_ct must be a number",
            ),
            "window ct null": (
                spec_with(aggregate={"window_effect_ct": None}),
                "aggregate.window_effect_ct must be a number",
            ),
            "window ct list": (
                spec_with(aggregate={"window_effect_ct": []}),
                "aggregate.window_effect_ct must be a number",
            ),
        }
        for name, (spec_obj, reason) in cases.items():
            with self.subTest(name):
                spec = self._write("shape.effect-surface.json", json.dumps(spec_obj))
                proc = _run("-i", spec, "-b", _DATA_JSON)
                self._assert_input_error(proc, spec)
                self.assertIn(reason, proc.stderr)

    def test_spec_accepted_edge_values_still_emit(self):
        # Values that emitted a record before the shape checks still do.
        def emit(**updates):
            spec_obj = _fixture_spec()
            spec_obj.update(updates)
            spec = self._write("ok.effect-surface.json", json.dumps(spec_obj))
            proc = _run("-i", spec, "-b", _DATA_JSON)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(proc.stdout)

        self.assertEqual(
            emit(aggregate={"window_effect_ct": 4.0})["gate"]["assigned_ct"], 4
        )
        for name, falsy in {
            "null": None,
            "{}": {},
            "[]": [],
            "0": 0,
            '""': "",
            "false": False,
        }.items():
            with self.subTest(verifier=name):
                self.assertEqual(emit(verifier=falsy)["verifier"]["id"], "none")
        for window in (True, False):
            with self.subTest(window_effect_ct=window):
                record = emit(aggregate={"window_effect_ct": window})
                self.assertEqual(record["gate"]["assigned_ct"], 4)
        surface = dict(_fixture_spec()["effect_surface"], reversibility=5)
        self.assertEqual(emit(effect_surface=surface)["gate"]["assigned_ct"], 4)
        # derive_ct never reads the axes of a surface with no external
        # effect, so a non-scalar axis there emitted a record before.
        for name, updates in {
            "external_effect false, axis list": {
                "external_effect": False,
                "reversibility": [],
            },
            "external_effect 0, axis object": {"external_effect": 0, "scope": {}},
        }.items():
            with self.subTest(name):
                surface = dict(_fixture_spec()["effect_surface"], **updates)
                record = emit(effect_surface=surface)
                self.assertEqual(
                    record["action"]["effect_surface"],
                    {
                        "external_effect": updates["external_effect"],
                        "tool": "payments.transfer",
                    },
                )

    def test_spec_newlines_read_as_text(self):
        # The original read a spec file in text mode, so CR and CRLF became
        # LF before json.loads, and read stdin through sys.stdin, which does
        # not translate newlines on POSIX. The invalid-JSON message from each
        # source must match the original's.
        cases = {
            "crlf": b'{\r\n "effect_surface": {\r\n  oops\r\n}\r\n',
            "cr": b'{\r "effect_surface": {\r  oops\r}\r',
        }
        for name, data in cases.items():
            with self.subTest(name):
                spec = self._write_bytes("nl.effect-surface.json", data)
                with open(spec, encoding="utf-8") as fh:
                    text = fh.read()
                with self.assertRaises(json.JSONDecodeError) as text_err:
                    json.loads(text)
                with self.assertRaises(json.JSONDecodeError) as bytes_err:
                    json.loads(data.decode("utf-8"))
                file_reason = str(text_err.exception)
                stdin_reason = str(bytes_err.exception)
                # Guard: the probe must tell text mode from a bytes decode.
                self.assertNotEqual(file_reason, stdin_reason)
                for where, reason, proc in (
                    (spec, file_reason, _run("-i", spec, "-b", _DATA_JSON)),
                    (
                        "<stdin>",
                        stdin_reason,
                        _run_stdin(data, "-b", _DATA_JSON),
                    ),
                ):
                    self.assertEqual(proc.returncode, 2, proc.stderr)
                    self.assertEqual(
                        proc.stderr,
                        f"EMITTER INPUT ERROR: spec {where}: invalid JSON: {reason}\n",
                    )


if __name__ == "__main__":
    unittest.main()
