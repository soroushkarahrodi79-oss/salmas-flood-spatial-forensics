from __future__ import annotations

import unittest

from salmas_flood.catalogue import event_relation, normalize_feature, s1_geometry_key, satellite_gate


class CatalogueTests(unittest.TestCase):
    def feature(self, item_id: str, acquired: str, orbit: int = 174) -> dict:
        return {
            "id": item_id,
            "bbox": [44.0, 38.0, 45.0, 39.0],
            "geometry": {"type": "Polygon", "coordinates": [[[44, 38], [45, 38], [45, 39], [44, 39], [44, 38]]]},
            "properties": {
                "datetime": acquired, "platform": "sentinel-1d", "sar:instrument_mode": "IW",
                "sar:product_type": "GRD", "sar:polarizations": ["VV", "VH"],
                "sat:orbit_state": "ascending", "sat:relative_orbit": orbit,
            },
        }

    def test_parser_preserves_required_sar_geometry(self) -> None:
        row = normalize_feature(self.feature("S1D_TEST", "2026-10-21T14:52:30Z"), "sentinel-1-grd")
        self.assertEqual(s1_geometry_key(row), ("IW", "GRD", ("VV", "VH"), "ascending", 174))
        self.assertIsNotNone(row["geometry"])

    def test_event_relation_uses_timezone_aware_boundaries(self) -> None:
        self.assertEqual(event_relation("2026-10-22T10:59:59Z", "2026-10-22T11:00:00Z", "2026-10-22T16:30:00Z"), "pre_event")
        self.assertEqual(event_relation("2026-10-22T17:00:00Z", "2026-10-22T11:00:00Z", "2026-10-22T16:30:00Z"), "post_event")

    def test_gate_holds_without_post_event_item(self) -> None:
        status, reasons = satellite_gate([{"event_relation": "pre_event"}])
        self.assertEqual(status, "HOLD_POST_EVENT_PAIR_REQUIRED")
        self.assertTrue(reasons)

    def test_incompatible_orbit_cannot_open_gate(self) -> None:
        pre = normalize_feature(self.feature("S1D_PRE", "2026-10-21T14:00:00Z", 174), "sentinel-1-grd")
        post = normalize_feature(self.feature("S1D_POST", "2026-10-24T14:00:00Z", 72), "sentinel-1-grd")
        pre["event_relation"], post["event_relation"] = "pre_event", "post_event"
        status, _ = satellite_gate([pre, post])
        self.assertEqual(status, "HOLD_PROCESSING_AND_CORROBORATION_REQUIRED")
