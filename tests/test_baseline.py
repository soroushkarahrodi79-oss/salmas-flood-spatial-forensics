from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BaselineTests(unittest.TestCase):
    def test_validation_script_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_project.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_scientific_gates_are_fail_closed(self) -> None:
        config = json.loads((ROOT / "config/study.json").read_text(encoding="utf-8"))
        gates = config["gates"]
        self.assertEqual(gates["satellite_flood_extent"], "HOLD_POST_EVENT_PAIR_REQUIRED")
        self.assertTrue(gates["hydraulic_depth_velocity"].startswith("NO_GO"))
        self.assertTrue(gates["return_period"].startswith("NO_GO"))

    def test_analysis_crs_is_utm_zone_38n(self) -> None:
        config = json.loads((ROOT / "config/study.json").read_text(encoding="utf-8"))
        self.assertEqual(config["spatial"]["analysis_crs"], "EPSG:32638")


if __name__ == "__main__":
    unittest.main()

