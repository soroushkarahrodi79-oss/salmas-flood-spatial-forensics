from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from affine import Affine

from salmas_flood.acquisition import sha256_file
from salmas_flood.precipitation import accumulation_window, regional_summary
from salmas_flood.terrain import candidate_pour_point, stable_drainage_fraction, terrain_products


class ProcessingTests(unittest.TestCase):
    def test_checksum_recording_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.bin"
            path.write_bytes(b"salmas-phase-1\n")
            self.assertEqual(sha256_file(path), "50c60b6e4eaa0d7af777d4f85bd28e9dda6d230c279d1e5b406a36dab8609ba1")

    def test_synthetic_terrain_is_deterministic_and_metric(self) -> None:
        elevation = np.array([
            [9, 8, 7, 6, 5], [8, 7, 6, 5, 4], [7, 6, 1, 4, 3],
            [6, 5, 4, 3, 2], [5, 4, 3, 2, 1],
        ], dtype=np.float32)
        transform = Affine(30, 0, 500000, 0, -30, 4300000)
        first = terrain_products(elevation, transform)
        second = terrain_products(elevation, transform)
        np.testing.assert_array_equal(first["flow_direction_d8"], second["flow_direction_d8"])
        np.testing.assert_allclose(first["upstream_area_km2"], second["upstream_area_km2"])
        self.assertGreater(float(first["fill_depth_m"][2, 2]), 0)

    def test_pour_point_maximizes_contributing_area_within_radius(self) -> None:
        area = np.zeros((5, 5), dtype=float); area[2, 3] = 9; area[4, 4] = 99
        transform = Affine(10, 0, 0, 0, -10, 50)
        point = candidate_pour_point(25, 25, area, transform, search_radius_m=15)
        self.assertEqual((point.row, point.col), (2, 3))

    def test_threshold_stability_reports_intersection_over_union(self) -> None:
        a = np.array([[0, 2], [3, 0]], dtype=float); b = np.array([[0, 2], [0, 0]], dtype=float)
        self.assertEqual(stable_drainage_fraction([a, b], [1.0])[1.0], 0.5)

    def test_precipitation_window_fails_closed_on_missing_half_hour(self) -> None:
        records = [("2026-10-22T11:30:00Z", np.ones((2, 2)))]
        with self.assertRaisesRegex(ValueError, "Incomplete window"):
            accumulation_window(records, "2026-10-22T12:00:00Z", 1)

    def test_precipitation_summary_retains_regional_support(self) -> None:
        values = np.array([[1.0, 2.0], [3.0, np.nan]])
        result = regional_summary(values, np.ones((2, 2), dtype=bool))
        self.assertEqual(result, {"cell_count": 3, "minimum_mm": 1.0, "mean_mm": 2.0, "maximum_mm": 3.0})


if __name__ == "__main__":
    unittest.main()
