#!/usr/bin/env python3
"""Acquire configured public assets with resume, checksum and local manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from salmas_flood.acquisition import acquire, write_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", action="append", help="Asset ID; repeat to select multiple")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / "config/data_sources.json").read_text(encoding="utf-8"))
    selected = [row for row in config["assets"] if not args.asset or row["asset_id"] in args.asset]
    unknown = set(args.asset or []) - {row["asset_id"] for row in selected}
    if unknown:
        raise SystemExit(f"Unknown asset IDs: {sorted(unknown)}")
    records = []
    for asset in selected:
        print(f"acquire {asset['asset_id']} -> {asset['destination']}")
        records.append(acquire(asset, ROOT, force=args.force))
    manifest = ROOT / "data/raw/acquisition_manifest.json"
    write_manifest(records, manifest)
    print(f"wrote {manifest.relative_to(ROOT)} ({len(records)} assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
