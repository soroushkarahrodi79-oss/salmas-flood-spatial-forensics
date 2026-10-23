#!/usr/bin/env python3
"""Query the public CDSE STAC catalogue without downloading imagery."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request


ENDPOINT = "https://stac.dataspace.copernicus.eu/v1/search"
DEFAULT_BBOX = "44.70,38.24,45.00,38.38"
DEFAULT_DATETIME = "2026-10-01T00:00:00Z/2026-11-15T00:00:00Z"
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

    params = urllib.parse.urlencode(
        {
            "collections": args.collection,
            "bbox": args.bbox,
            "datetime": args.datetime,
            "limit": args.limit,
        }
    )
    request = urllib.request.Request(
        f"{ENDPOINT}?{params}",
        headers={"User-Agent": "salmas-flood-spatial-forensics/0.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)

    rows = []
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        rows.append(
            {
                "id": feature.get("id"),
                "datetime": properties.get("datetime"),
                "orbit_state": properties.get("sat:orbit_state"),
                "relative_orbit": properties.get("sat:relative_orbit"),
                "polarizations": properties.get("sar:polarizations"),
                "cloud_cover": properties.get("eo:cloud_cover"),
            }
        )

    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

