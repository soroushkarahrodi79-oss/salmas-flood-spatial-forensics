#!/usr/bin/env python3
"""Fail-closed structural validation for the research baseline."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_HEADERS = {
    "provenance/source_manifest.csv": [
        "source_id", "title", "publisher", "url", "source_type",
        "published_or_reference_date", "retrieved_utc", "role", "status",
        "license_or_terms", "limitations",
    ],
    "provenance/claim_register.csv": [
        "claim_id", "claim", "claim_time_utc", "status", "confidence",
        "evidence_source_ids", "spatial_support", "temporal_support",
        "claim_boundary", "next_action",
    ],
    "provenance/event_timeline.csv": [
        "event_id", "time_local", "time_utc", "place", "event_type",
        "observation", "source_id", "confidence", "verification_status",
    ],
    "data/reference/affected_settlements.csv": [
        "settlement_id", "name_en", "name_fa", "longitude", "latitude",
        "coordinate_status", "population_2016", "population_status", "source_id",
    ],
}


def read_csv(relative_path: str) -> list[dict[str, str]]:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_HEADERS[relative_path]:
            raise ValueError(f"Unexpected schema in {relative_path}: {reader.fieldnames}")
        return list(reader)


def validate_unique(rows: list[dict[str, str]], field: str, label: str) -> None:
    values = [row[field] for row in rows]
    if any(not value for value in values):
        raise ValueError(f"Empty {field} in {label}")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field} in {label}")


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    with (ROOT / "config/study.json").open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    bbox = config["spatial"]["catalogue_bbox_wgs84"]
    if len(bbox) != 4 or not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        raise ValueError("Invalid catalogue_bbox_wgs84")
    if config["gates"]["satellite_flood_extent"] != "HOLD_POST_EVENT_PAIR_REQUIRED":
        raise ValueError("Satellite extent gate must remain HOLD at baseline")

    sources = read_csv("provenance/source_manifest.csv")
    claims = read_csv("provenance/claim_register.csv")
    timeline = read_csv("provenance/event_timeline.csv")
    settlements = read_csv("data/reference/affected_settlements.csv")

    validate_unique(sources, "source_id", "source manifest")
    validate_unique(claims, "claim_id", "claim register")
    validate_unique(timeline, "event_id", "event timeline")
    validate_unique(settlements, "settlement_id", "settlements")

    source_ids = {row["source_id"] for row in sources}
    for row in timeline:
        if row["source_id"] not in source_ids:
            raise ValueError(f"Unknown timeline source: {row['source_id']}")
        local = parse_datetime(row["time_local"])
        utc = parse_datetime(row["time_utc"])
        if local.astimezone(utc.tzinfo) != utc:
            raise ValueError(f"Local/UTC mismatch in {row['event_id']}")

    for row in settlements:
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            raise ValueError(f"Settlement outside catalogue bbox: {row['settlement_id']}")
        if row["source_id"] not in source_ids:
            raise ValueError(f"Unknown settlement source: {row['source_id']}")

    print(
        "PASS: configuration, schemas, IDs, source references, timezone pairs "
        "and settlement bounds validated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

