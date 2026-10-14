#!/usr/bin/env python3
"""Stdlib unittest for the backtest CLI's JSON-load error handling (backtest.py).

Run: python3 -m unittest discover scripts/laas

Each test runs the real CLI in a subprocess, so the exit code and stderr are
what a caller of `python3 backtest.py` observes. One test also calls
clopper_pearson_upper_bound in-process, because the artifact rounds the bound.
- positive: the backtest fixture plus the real data.json still yields its
  verdicts (CT2 pass / exit 0, CT3 fail / exit 1, CT4 indeterminate / exit 2).
- negative: a malformed, unreadable, or incomplete dataset or data.json, a
  non-string laas.bundle_id, or an --out path that cannot be written exits 3
  (the harness's existing error code, never a verdict code) with a one-line
  message naming the file or argument, and emits no artifact on stdout (fail
  closed, no defaults).
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import unittest

import backtest

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKTEST = os.path.join(_HERE, "backtest.py")
_FIXTURE = os.path.join(_HERE, "fixtures", "fixture_backtest.json")
_DATA_JSON = os.path.join(_HERE, "..", "..", "conformance", "laas", "data.json")


def _run(dataset, data_json, ct=2, extra=()):
    return subprocess.run(
        [
            sys.executable,
            _BACKTEST,
            "--dataset",
            dataset,
            "--data-json",
            data_json,
            "--ct",
            str(ct),
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _run_args(*args):
    return subprocess.run(
        [sys.executable, _BACKTEST, *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _parse(case: unittest.TestCase, proc, text):
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        case.fail(
            f"output is not JSON ({e}): {text!r}; stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )


class TestBacktestCliVerdicts(unittest.TestCase):
    def test_ct2_fixture_passes(self):
        proc = _run(_FIXTURE, _DATA_JSON, ct=2)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        art = _parse(self, proc, proc.stdout)
        self.assertEqual(art["verdict"], "pass")
        self.assertEqual(art["residual_error_bound"], 0.014286)

    def test_ct3_fixture_fails(self):
        proc = _run(_FIXTURE, _DATA_JSON, ct=3)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(_parse(self, proc, proc.stdout)["verdict"], "fail")

    def test_ct4_fixture_indeterminate(self):
        proc = _run(_FIXTURE, _DATA_JSON, ct=4)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        art = _parse(self, proc, proc.stdout)
        self.assertEqual(art["verdict"], "indeterminate")
        self.assertEqual(art["disposition"], "requires_deterministic_or_human_gate")


class TestBacktestCliInputErrors(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _write(self, name, text):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def _assert_input_error(self, proc, path):
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertNotIn("Traceback", proc.stderr)
        lines = proc.stderr.strip().splitlines()
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertTrue(lines[0].startswith("BACKTEST INPUT ERROR:"), lines[0])
        self.assertIn(path, lines[0])

    def test_malformed_dataset_exits_3(self):
        dataset = self._write("bad.backtest.json", '{"samples": [')
        proc = _run(dataset, _DATA_JSON)
        self._assert_input_error(proc, dataset)
        self.assertIn("invalid JSON", proc.stderr)

    def test_dataset_missing_samples_key_exits_3(self):
        dataset = self._write("nosamples.backtest.json", '{"rows": []}')
        proc = _run(dataset, _DATA_JSON)
        self._assert_input_error(proc, dataset)
        self.assertIn("'samples'", proc.stderr)

    def test_dataset_sample_missing_field_exits_3(self):
        dataset = self._write(
            "nofield.backtest.json",
            json.dumps({"samples": [{"action_id": "a1", "ct": 2}]}),
        )
        proc = _run(dataset, _DATA_JSON)
        self._assert_input_error(proc, dataset)
        self.assertIn("'verifier_verdict'", proc.stderr)

    def test_dataset_unreadable_exits_3(self):
        dataset = os.path.join(self._tmp.name, "absent.backtest.json")
        proc = _run(dataset, _DATA_JSON)
        self._assert_input_error(proc, dataset)

    def test_malformed_data_json_exits_3(self):
        bundle = self._write("bad.data.json", '{"laas": ')
        proc = _run(_FIXTURE, bundle)
        self._assert_input_error(proc, bundle)
        self.assertIn("invalid JSON", proc.stderr)

    def test_data_json_not_object_exits_3(self):
        bundle = self._write("list.data.json", "[]")
        proc = _run(_FIXTURE, bundle)
        self._assert_input_error(proc, bundle)

    def test_data_json_unreadable_exits_3(self):
        bundle = os.path.join(self._tmp.name, "absent.data.json")
        proc = _run(_FIXTURE, bundle)
        self._assert_input_error(proc, bundle)

    def test_data_json_missing_tolerance_map_exits_3(self):
        # Previously raised ToleranceLookupError outside main's try -> traceback,
        # exit 1 (indistinguishable from a "fail" verdict).
        bundle = self._write("notol.data.json", '{"laas": {"bundle_id": "x"}}')
        proc = _run(_FIXTURE, bundle)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(_parse(self, proc, proc.stderr)["error"], "tolerance_lookup")
        self.assertIn("escape_rate_tolerance_by_ct", proc.stderr)

    def test_deeply_nested_json_exits_3(self):
        # 20000 levels raised RecursionError in json.loads -> traceback, exit 1.
        nested = "[" * 20000 + "]" * 20000
        dataset = self._write("deep.backtest.json", nested)
        proc = _run(dataset, _DATA_JSON)
        self._assert_input_error(proc, dataset)
        self.assertIn("invalid JSON", proc.stderr)

        bundle = self._write("deep.data.json", nested)
        proc = _run(_FIXTURE, bundle)
        self._assert_input_error(proc, bundle)
        self.assertIn("invalid JSON", proc.stderr)

    @unittest.skipUnless(
        hasattr(sys, "get_int_max_str_digits"), "no int digit limit in this Python"
    )
    def test_integer_over_digit_limit_exits_3(self):
        # A 5000-digit integer literal hit Python's int digit limit: ValueError
        # ("Exceeds the limit (4300 digits)") during the parse -> traceback, exit 1.
        big = "1" * 5000
        bundle = self._write("bigint.data.json", '{"laas": {"bundle_id": %s}}' % big)
        proc = _run(_FIXTURE, bundle)
        self._assert_input_error(proc, bundle)
        self.assertIn("invalid JSON", proc.stderr)

        row = '{"action_id": "a1", "ct": %s, "verifier_verdict": "pass", ' % big
        row += '"ground_truth": "correct"}'
        dataset = self._write("bigint.backtest.json", '{"samples": [%s]}' % row)
        proc = _run(dataset, _DATA_JSON)
        self._assert_input_error(proc, dataset)
        self.assertIn("invalid JSON", proc.stderr)

    def test_non_finite_sample_ct_exits_3(self):
        # int(inf) raised OverflowError, which load_dataset did not catch.
        for label, literal in {"inf": "Infinity", "overflow": "1e999"}.items():
            with self.subTest(label=label):
                row = '{"action_id": "a1", "ct": %s, ' % literal
                row += '"verifier_verdict": "pass", "ground_truth": "correct"}'
                dataset = self._write(
                    f"ct-{label}.backtest.json", '{"samples": [%s]}' % row
                )
                proc = _run(dataset, _DATA_JSON)
                self._assert_input_error(proc, dataset)
                self.assertIn("sample 0", proc.stderr)

    def test_invalid_confidence_exits_3(self):
        # Each raised ValueError in _z_for -> traceback, exit 1 (the fail code).
        for value in ("0", "1", "2", "nan", "inf", "-0.5"):
            with self.subTest(value=value):
                proc = _run(_FIXTURE, _DATA_JSON, extra=(f"--confidence={value}",))
                self._assert_input_error(proc, "--confidence")

    def test_valid_confidence_still_yields_verdict(self):
        proc = _run(_FIXTURE, _DATA_JSON, ct=2, extra=("--confidence=0.9",))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        art = _parse(self, proc, proc.stdout)
        self.assertEqual(art["verdict"], "pass")
        self.assertEqual(art["confidence"], 0.9)

    def test_confidence_with_alpha_rounding_to_one_exits_3(self):
        # 0 < c < 1, but 1.0 - c rounds to 1.0, so alpha == 1.0: n_min was 0 and
        # the bisection target was 0, yielding a verdict instead of an error.
        # 2**-54 is the largest such c (1 - 2**-54 is a tie that rounds to 1.0).
        for value in (1e-17, 1e-300, 5e-324, 2.0**-54):
            with self.subTest(value=value):
                self.assertEqual(1.0 - value, 1.0)
                proc = _run(_FIXTURE, _DATA_JSON, extra=(f"--confidence={value!r}",))
                self._assert_input_error(proc, "--confidence")

    def test_smallest_confidence_with_alpha_below_one_is_accepted(self):
        # The next float above 2**-54 is the smallest c with 1.0 - c < 1.0.
        for value in (math.nextafter(2.0**-54, 1.0), 1e-16):
            for interval in ("wilson", "clopper-pearson"):
                with self.subTest(value=value, interval=interval):
                    self.assertLess(1.0 - value, 1.0)
                    proc = _run(
                        _FIXTURE,
                        _DATA_JSON,
                        ct=2,
                        extra=(f"--confidence={value!r}", f"--interval={interval}"),
                    )
                    self.assertIn(proc.returncode, (0, 1, 2), proc.stderr)
                    self.assertNotIn("Traceback", proc.stderr)
                    art = _parse(self, proc, proc.stdout)
                    self.assertEqual(art["confidence"], value)
                    self.assertGreaterEqual(art["min_samples_required"], 1)
                    # The artifact rounds the bound to 6 places, so a bound this
                    # small reads 0.0 there; check the unrounded value in-process.
                    bound = backtest.clopper_pearson_upper_bound(
                        art["escapes"], art["n"], value
                    )
                    self.assertGreater(bound, 0.0)


class TestBacktestCliUsageErrors(unittest.TestCase):
    """argparse usage errors exited 2 -- the indeterminate verdict code."""

    _BASE = ("--dataset", _FIXTURE, "--data-json", _DATA_JSON)

    def test_usage_errors_exit_3(self):
        base = self._BASE
        cases = {
            "--confidence": (*base, "--ct", "2", "--confidence", "abc"),
            "--ct": (*base, "--ct", "abc"),
            "--bogus": (*base, "--ct", "2", "--bogus"),
            "--dataset": ("--data-json", _DATA_JSON, "--ct", "2"),
            "--interval": (*base, "--ct", "2", "--interval", "nope"),
            "--c": (*base, "--ct", "2", "--c", "0.9"),
        }
        for arg, argv in cases.items():
            with self.subTest(arg=arg):
                proc = _run_args(*argv)
                self.assertEqual(proc.returncode, 3, proc.stderr)
                self.assertEqual(proc.stdout, "")
                self.assertNotIn("Traceback", proc.stderr)
                self.assertNotIn("usage:", proc.stderr)
                lines = proc.stderr.splitlines()
                self.assertEqual(len(lines), 1, proc.stderr)
                self.assertTrue(
                    lines[0].startswith(f"BACKTEST INPUT ERROR: {arg}: "), lines[0]
                )

    def test_help_exits_0(self):
        proc = _run_args("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("usage:", proc.stdout)
        self.assertEqual(proc.stderr, "")


class TestBacktestCliToleranceValues(unittest.TestCase):
    """A CT2 tolerance in data.json must be a JSON number t with 0 <= t <= 1."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        with open(_DATA_JSON, encoding="utf-8") as fh:
            self._bundle = json.load(fh)

    def _bundle_with(self, name, tol_map):
        bundle = json.loads(json.dumps(self._bundle))
        bundle["laas"]["escape_rate_tolerance_by_ct"] = tol_map
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(bundle, fh)
        return path

    def _bundle_with_ct2(self, name, value):
        tol_map = dict(self._bundle["laas"]["escape_rate_tolerance_by_ct"])
        tol_map["2"] = value
        return self._bundle_with(name, tol_map)

    def _assert_input_error(self, proc, path):
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertNotIn("Traceback", proc.stderr)
        lines = proc.stderr.strip().splitlines()
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertTrue(lines[0].startswith("BACKTEST INPUT ERROR:"), lines[0])
        self.assertIn(path, lines[0])
        self.assertIn("escape_rate_tolerance_by_ct", lines[0])

    def test_invalid_tolerance_values_exit_3(self):
        # Each was a traceback (exit 1, the "fail" verdict code), a pass on a
        # string, or a fail on a negative tolerance before validation.
        cases = {
            "string": "abc",
            "null": None,
            "bool": True,
            "numeric_string": "0.5",
            "negative": -1,
            "above_one": 1.5,
            "huge": 1e9,
        }
        for label, value in cases.items():
            with self.subTest(label=label, value=value):
                bundle = self._bundle_with_ct2(f"{label}.data.json", value)
                proc = _run(_FIXTURE, bundle, ct=2)
                self._assert_input_error(proc, bundle)

    def test_non_finite_tolerance_exits_3(self):
        # json.loads accepts NaN and Infinity literals; neither is a tolerance.
        for label, literal in {"nan": "NaN", "inf": "Infinity"}.items():
            with self.subTest(label=label):
                bundle = self._bundle_with_ct2(f"{label}.data.json", 0.02)
                with open(bundle, encoding="utf-8") as fh:
                    text = fh.read()
                with open(bundle, "w", encoding="utf-8") as fh:
                    fh.write(text.replace('"2": 0.02', f'"2": {literal}'))
                proc = _run(_FIXTURE, bundle, ct=2)
                self._assert_input_error(proc, bundle)

    def test_invalid_tolerance_for_other_ct_exits_3(self):
        # A malformed bundle fails closed even when the measured CT's value is valid.
        tol_map = dict(self._bundle["laas"]["escape_rate_tolerance_by_ct"])
        tol_map["3"] = "abc"
        bundle = self._bundle_with("other-ct.data.json", tol_map)
        proc = _run(_FIXTURE, bundle, ct=2)
        self._assert_input_error(proc, bundle)

    def test_oversized_integer_tolerance_exits_3(self):
        # 10**400 is a valid JSON integer under the digit limit, but
        # math.isfinite(10**400) raised OverflowError -> traceback, exit 1.
        big = 10**400
        bundle = self._bundle_with_ct2("bigtol.data.json", big)
        proc = _run(_FIXTURE, bundle, ct=2)
        self._assert_input_error(proc, bundle)

        tol_map = dict(self._bundle["laas"]["escape_rate_tolerance_by_ct"])
        tol_map["3"] = big
        bundle = self._bundle_with("bigtol-other-ct.data.json", tol_map)
        proc = _run(_FIXTURE, bundle, ct=2)
        self._assert_input_error(proc, bundle)

    def test_tiny_tolerances_are_indeterminate(self):
        # 0 < t <= 5e-17 made log(1 - t) == 0 -> ZeroDivisionError; at 5e-324 the
        # n_min quotient overflows a float. Each t is inside [0, 1], so the run
        # yields a verdict: n_min is finite but far above n, so indeterminate.
        ln_alpha = math.log(1 - 0.95)
        for t in (5e-17, 1e-17, 1e-300, 5e-324):
            with self.subTest(t=t):
                bundle = self._bundle_with_ct2(f"tiny-{t}.data.json", t)
                proc = _run(_FIXTURE, bundle, ct=2)
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                art = _parse(self, proc, proc.stdout)
                self.assertEqual(art["verdict"], "indeterminate")
                self.assertEqual(art["disposition"], "insufficient_sample_size")
                self.assertEqual(art["residual_tolerance"], t)
                n_min = art["min_samples_required"]
                self.assertIsInstance(n_min, int)
                self.assertGreater(n_min, art["n"])
                # For tiny t, ln(1 - t) ~= -t, so n_min ~= -ln(alpha) / t.
                expected = -ln_alpha / t
                if math.isfinite(expected):
                    self.assertAlmostEqual(n_min / expected, 1.0, places=9)
                else:
                    self.assertGreater(n_min, 10**323)

    def test_tolerance_map_not_object_exits_3(self):
        for label, value in {"null": None, "list": [0.02], "string": "x"}.items():
            with self.subTest(label=label):
                bundle = self._bundle_with(f"map-{label}.data.json", value)
                proc = _run(_FIXTURE, bundle, ct=2)
                self._assert_input_error(proc, bundle)

    def test_boundary_tolerances_are_accepted(self):
        # 0 and 1 are inside the closed range; neither may crash.
        proc = _run(_FIXTURE, self._bundle_with_ct2("one.data.json", 1), ct=2)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        art = _parse(self, proc, proc.stdout)
        self.assertEqual(art["verdict"], "pass")
        self.assertEqual(art["residual_tolerance"], 1.0)

        proc = _run(_FIXTURE, self._bundle_with_ct2("zero.data.json", 0), ct=2)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        art = _parse(self, proc, proc.stdout)
        self.assertEqual(art["disposition"], "requires_deterministic_or_human_gate")


class TestBacktestCliBundleId(unittest.TestCase):
    """laas.bundle_id, when present, must be a JSON string."""

    _SENTINEL = "__BUNDLE_ID_LITERAL__"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        with open(_DATA_JSON, encoding="utf-8") as fh:
            self._bundle = json.load(fh)

    def _bundle_with_literal(self, name, literal):
        # Splice the raw JSON literal into the text, so NaN and deep nesting
        # reach the harness exactly as written.
        bundle = json.loads(json.dumps(self._bundle))
        bundle["laas"]["bundle_id"] = self._SENTINEL
        text = json.dumps(bundle).replace(json.dumps(self._SENTINEL), literal, 1)
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def _assert_bundle_id_error(self, literal, name):
        bundle = self._bundle_with_literal(name, literal)
        proc = _run(_FIXTURE, bundle, ct=2)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertNotIn("Traceback", proc.stderr)
        lines = proc.stderr.splitlines()
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertTrue(
            lines[0].startswith(f"BACKTEST INPUT ERROR: {bundle}: "), lines[0]
        )
        self.assertIn("bundle_id", lines[0])

    def test_number_bundle_id_exits_3(self):
        self._assert_bundle_id_error("5", "num.data.json")

    def test_list_bundle_id_exits_3(self):
        self._assert_bundle_id_error('["laas-fin-2.0.0"]', "list.data.json")

    def test_null_bundle_id_exits_3(self):
        self._assert_bundle_id_error("null", "null.data.json")

    def test_nan_bundle_id_exits_3(self):
        # json.loads accepts NaN; copied through, it made non-standard JSON output.
        self._assert_bundle_id_error("NaN", "nan.data.json")

    def test_deeply_nested_bundle_id_exits_3(self):
        # 3000 levels parse, but asdict(art) in measure() raised RecursionError
        # -> traceback, exit 1 (the "fail" verdict code).
        self._assert_bundle_id_error("[" * 3000 + "]" * 3000, "deep.data.json")

    def test_string_bundle_id_is_copied(self):
        bundle = self._bundle_with_literal("str.data.json", '"custom-bundle"')
        proc = _run(_FIXTURE, bundle, ct=2)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        art = _parse(self, proc, proc.stdout)
        self.assertEqual(art["verdict"], "pass")
        self.assertEqual(art["bundle_id"], "custom-bundle")

    def test_absent_bundle_id_defaults_to_empty(self):
        bundle = json.loads(json.dumps(self._bundle))
        del bundle["laas"]["bundle_id"]
        path = os.path.join(self._tmp.name, "absent.data.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(bundle, fh)
        proc = _run(_FIXTURE, path, ct=2)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        art = _parse(self, proc, proc.stdout)
        self.assertEqual(art["verdict"], "pass")
        self.assertEqual(art["bundle_id"], "")


class TestBacktestCliOut(unittest.TestCase):
    """An --out path that cannot be written is an input error, not a verdict."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _assert_out_error(self, out):
        proc = _run(_FIXTURE, _DATA_JSON, ct=2, extra=("--out", out))
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertNotIn("Traceback", proc.stderr)
        lines = proc.stderr.splitlines()
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertTrue(lines[0].startswith("BACKTEST INPUT ERROR: --out: "), lines[0])
        self.assertNotEqual(lines[0], "BACKTEST INPUT ERROR: --out: ")

    def test_out_directory_exits_3(self):
        # write_text on a directory raised IsADirectoryError -> traceback, exit 1.
        self._assert_out_error(self._tmp.name)

    def test_out_missing_parent_exits_3(self):
        # A nonexistent parent raised FileNotFoundError -> traceback, exit 1.
        self._assert_out_error(os.path.join(self._tmp.name, "absent", "art.json"))

    def test_out_file_matches_stdout(self):
        out = os.path.join(self._tmp.name, "art.json")
        proc = _run(_FIXTURE, _DATA_JSON, ct=2, extra=("--out", out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), proc.stdout)
        self.assertEqual(_parse(self, proc, proc.stdout)["verdict"], "pass")


if __name__ == "__main__":
    unittest.main()
