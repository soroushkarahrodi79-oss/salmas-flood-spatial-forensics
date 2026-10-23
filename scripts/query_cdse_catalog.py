#!/usr/bin/env python3
"""Query and normalize the public CDSE STAC catalogue without asset download."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from salmas_flood.catalogue import event_relation, normalize_feature  # noqa: E402

ENDPOINT = "https://stac.dataspace.copernicus.eu/v1/search"
DEFAULT_BBOX = "44.70,38.24,45.00,38.38"
DEFAULT_DATETIME = "2026-10-01T00:00:00Z/2026-11-15T00:00:00Z"
EVENT_START_UTC = "2026-10-22T11:00:00Z"
EVENT_END_UTC = "2026-10-22T16:30:00Z"
ALLOWED_COLLECTIONS = {"sentinel-1-grd", "sentinel-2-l2a"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", choices=sorted(ALLOWED_COLLECTIONS), required=True)
    parser.add_argument("--bbox", default=DEFAULT_BBOX)
    parser.add_argument("--datetime", default=DEFAULT_DATETIME)
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.limit <= 1000:
        raise SystemExit("--limit must be between 1 and 1000")
    bbox = [float(value) for value in args.bbox.split(",")]
    if len(bbox) != 4 or not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        raise SystemExit("--bbox requires west,south,east,north")
    params = urllib.parse.urlencode({"collections": args.collection, "bbox": args.bbox, "datetime": args.datetime, "limit": args.limit})
    request = urllib.request.Request(f"{ENDPOINT}?{params}", headers={"User-Agent": "salmas-flood-spatial-forensics/0.2"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    rows = []
    for feature in payload.get("features", []):
        row = normalize_feature(feature, args.collection)
        row["event_relation"] = event_relation(row["acquired_utc"], EVENT_START_UTC, EVENT_END_UTC)
        row["footprint_intersects_query_bbox"] = True
        rows.append(row)
    rows.sort(key=lambda row: (row["acquired_utc"], row["item_id"]), reverse=True)
    result = {
        "endpoint": ENDPOINT,
        "exact_query": {"collection": args.collection, "bbox": bbox, "datetime": args.datetime, "limit": args.limit},
        "event_window_utc": [EVENT_START_UTC, EVENT_END_UTC],
        "returned": len(rows),
        "items": rows,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
