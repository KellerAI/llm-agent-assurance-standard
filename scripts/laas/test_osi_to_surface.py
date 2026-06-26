#!/usr/bin/env python3
"""Stdlib unittest for the OSI->LaaS converter/adapter (osi_to_surface.py).

Run: python3 -m unittest discover scripts/laas

Acceptance linkage:
- AC1 (sufficient): each fixture asserts the converter-built surface, run
  through emitter.derive_ct, yields the expected CT (the converter does no tier
  math; the CT is owned by derive_ct / data.json).
- AC4: signed vs unsigned -- unsigned floors assigned_ct to >=
  untrusted_input_min_ct via the aggregate window.
"""
import json
import os
import unittest

from emitter import ActorContext, GateContext, derive_ct
import osi_to_surface as osi

_DATA_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "conformance", "laas", "data.json"
)
_SCHEMA = os.path.join(
    os.path.dirname(__file__), "osi", "kellerai_laas_extension.schema.json"
)


def _gate():
    return GateContext.from_bundle(_DATA_JSON)


def _ct(surface):
    ct, _ = derive_ct(surface, _gate())
    return ct


def _ext(rev, scope, cons, **extra):
    data = {"reversibility": rev, "scope": scope, "consequence": cons}
    data.update(extra)
    return [{"vendor_name": "KELLERAI_LAAS", "data": data}]


def _model():
    return {
        "datasets": [
            {"name": "orders", "custom_extensions": _ext("hard", "multi", "material")},
            {
                "name": "customers",
                "custom_extensions": _ext(
                    "reversible", "single", "none", access_sensitive=False
                ),
            },
        ],
        "metrics": [
            {
                "name": "net_settlement_amount",
                "custom_extensions": _ext("irreversible", "org", "high"),
            },
        ],
        "relationships": [{"from": "orders", "to": "customers"}],
    }


class TestBuildSurface(unittest.TestCase):
    def test_ct4_write(self):
        s = osi.build_surface(
            _model(),
            {"kind": "metric", "name": "net_settlement_amount", "operation": "write"},
        )
        self.assertTrue(s.external_effect)
        self.assertEqual(s.reversibility, "irreversible")
        self.assertEqual(s.scope, "org")
        self.assertEqual(s.consequence, "high")
        self.assertEqual(_ct(s), 4)

    def test_ct0_read(self):
        s = osi.build_surface(
            _model(), {"kind": "dataset", "name": "customers", "operation": "read"}
        )
        self.assertFalse(s.external_effect)
        self.assertEqual(_ct(s), 0)

    def test_delete_floors_irreversible(self):
        # customers is annotated reversible; delete floors reversibility to
        # irreversible -> CT4.
        s = osi.build_surface(
            _model(), {"kind": "dataset", "name": "customers", "operation": "delete"}
        )
        self.assertEqual(s.reversibility, "irreversible")
        self.assertEqual(_ct(s), 4)

    def test_write_floors_hard(self):
        # A reversible object written -> reversibility floored to hard.
        model = {
            "datasets": [
                {"name": "ds", "custom_extensions": _ext("reversible", "single", "low")}
            ],
            "relationships": [],
        }
        s = osi.build_surface(
            model, {"kind": "dataset", "name": "ds", "operation": "write"}
        )
        self.assertEqual(s.reversibility, "hard")

    def test_blast_radius_downstream_higher_consequence(self):
        # Target a is low-consequence; downstream b (reachable a->b) is high ->
        # CT4 on the consequence axis (proves blast radius spans all 3 axes).
        model = {
            "datasets": [
                {"name": "a", "custom_extensions": _ext("reversible", "single", "low")},
                {"name": "b", "custom_extensions": _ext("reversible", "single", "high")},
            ],
            "relationships": [{"from": "a", "to": "b"}],
        }
        s = osi.build_surface(
            model, {"kind": "dataset", "name": "a", "operation": "write"}
        )
        self.assertEqual(s.consequence, "high")
        self.assertEqual(_ct(s), 4)

    def test_missing_axis_defaults_ct4(self):
        # scope omitted -> None -> derive_ct default-to-highest -> CT4.
        model = {
            "datasets": [
                {
                    "name": "ds",
                    "custom_extensions": [
                        {
                            "vendor_name": "KELLERAI_LAAS",
                            "data": {"reversibility": "hard", "consequence": "low"},
                        }
                    ],
                }
            ],
            "relationships": [],
        }
        s = osi.build_surface(
            model, {"kind": "dataset", "name": "ds", "operation": "write"}
        )
        self.assertIsNone(s.scope)
        self.assertEqual(_ct(s), 4)

    def test_access_sensitive_coerces_scope_public(self):
        model = {
            "datasets": [
                {
                    "name": "ds",
                    "custom_extensions": _ext(
                        "hard", "single", "low", access_sensitive=True
                    ),
                }
            ],
            "relationships": [],
        }
        s = osi.build_surface(
            model, {"kind": "dataset", "name": "ds", "operation": "write"}
        )
        self.assertEqual(s.scope, "public")
        self.assertEqual(_ct(s), 4)  # public scope -> CT4


class TestAdapterTrust(unittest.TestCase):
    def _actor(self):
        return ActorContext(actor_id="agent.test", actor_model_lineage="L")

    def test_signed_ct4_write(self):
        rec = osi.osi_emit_decision_record(
            _model(),
            {"kind": "metric", "name": "net_settlement_amount", "operation": "write"},
            model_signed=True,
            actor=self._actor(),
            gate=_gate(),
        )
        self.assertTrue(rec["input"]["trusted"])
        self.assertEqual(rec["gate"]["assigned_ct"], 4)

    def test_unsigned_floors_assigned_ct(self):
        # CT0 read, but unsigned -> window_effect_ct=3 floors assigned_ct to >= 3.
        rec = osi.osi_emit_decision_record(
            _model(),
            {"kind": "dataset", "name": "customers", "operation": "read"},
            model_signed=False,
            actor=self._actor(),
            gate=_gate(),
        )
        self.assertFalse(rec["input"]["trusted"])
        self.assertGreaterEqual(rec["gate"]["assigned_ct"], 3)
        self.assertEqual(rec["aggregate"]["window_effect_ct"], 3)


class TestSchemaDrift(unittest.TestCase):
    def test_schema_enums_match_lattice_keys(self):
        # AC2: the schema's per-axis enums must equal the data.json lattice keys.
        with open(_SCHEMA, encoding="utf-8") as fh:
            props = json.load(fh)["properties"]
        with open(_DATA_JSON, encoding="utf-8") as fh:
            lattice = json.load(fh)["laas"]["tier_lattice"]
        for axis in ("reversibility", "scope", "consequence"):
            self.assertEqual(
                set(props[axis]["enum"]),
                set(lattice[axis].keys()),
                f"schema enum drift on axis {axis!r}",
            )


if __name__ == "__main__":
    unittest.main()
