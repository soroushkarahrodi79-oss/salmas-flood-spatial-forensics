"""Dependency-free fail-closed validation of the reviewable research record."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_HEADERS = {
    "provenance/source_manifest.csv": [
        "source_id", "title", "publisher", "url", "source_type", "published_or_reference_date",
        "publication_time_status", "retrieved_utc", "observation_start_utc", "observation_end_utc",
        "spatial_coverage", "role", "status", "accessibility", "archive_status", "license_or_terms", "limitations",
    ],
    "provenance/claim_register.csv": [
        "claim_id", "claim_category", "claim_original_fa", "claim_translation_en", "analyst_interpretation",
        "claim_time_utc", "publication_time_utc", "observation_start_utc", "observation_end_utc", "status",
        "confidence", "evidence_source_ids", "spatial_support", "temporal_support", "claim_boundary", "next_action",
    ],
    "provenance/event_timeline.csv": [
        "event_id", "publication_time_local", "publication_time_utc", "observation_start_utc", "observation_end_utc",
        "time_status", "place", "event_type", "original_fa", "translation_en", "analyst_interpretation",
        "source_id", "confidence", "verification_status", "evidence_class",
    ],
    "provenance/catalog_snapshot.csv": [
        "snapshot_id", "collection", "item_id", "acquired_utc", "satellite", "acquisition_mode", "product_type",
        "processing_level", "orbit_direction", "relative_orbit", "polarizations", "tile_id",
        "catalogue_cloud_cover_percent", "aoi_clear_pixel_percent", "footprint_intersects_catalogue_aoi",
        "event_relation", "geometry_compatibility", "query_bbox", "query_datetime", "queried_utc", "source_id", "interpretation",
    ],
    "data/reference/affected_settlements.csv": [
        "settlement_id", "name_en", "name_fa", "name_variants", "longitude", "latitude", "coordinate_status",
        "coordinate_uncertainty_m", "coordinate_revision_id", "population_2016", "population_status", "source_ids",
    ],
    "provenance/settlement_coordinate_observations.csv": [
        "coordinate_observation_id", "settlement_id", "source_id", "source_feature_id", "observed_name", "longitude",
        "latitude", "geometry_type", "retrieved_utc", "estimated_source_precision_m", "offset_from_adopted_m",
        "adoption_status", "reason",
    ],
}


def read_csv(relative_path: str) -> list[dict[str, str]]:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_HEADERS[relative_path]:
            raise ValueError(f"Unexpected schema in {relative_path}: {reader.fieldnames}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"Unquoted delimiter created surplus columns in {relative_path}")
    return rows


def validate_unique(rows: list[dict[str, str]], field: str, label: str) -> None:
    values = [row[field] for row in rows]
    if any(not value for value in values):
        raise ValueError(f"Empty {field} in {label}")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field} in {label}")


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Timestamp lacks timezone: {value}")
    return parsed


def _ids(value: str) -> set[str]:
    return {item for item in value.split("|") if item}


def validate_project(root: Path = ROOT) -> None:
    global ROOT
    ROOT = root
    config = json.loads((ROOT / "config/study.json").read_text(encoding="utf-8"))
    vocab = json.loads((ROOT / "config/vocabularies.json").read_text(encoding="utf-8"))
    terrain = json.loads((ROOT / "config/terrain.json").read_text(encoding="utf-8"))
    precipitation = json.loads((ROOT / "config/precipitation.json").read_text(encoding="utf-8"))

    bbox = config["spatial"]["catalogue_bbox_wgs84"]
    if len(bbox) != 4 or not (-180 <= bbox[0] < bbox[2] <= 180 and -90 <= bbox[1] < bbox[3] <= 90):
        raise ValueError("Invalid catalogue_bbox_wgs84")
    if config["spatial"]["analysis_crs"] != "EPSG:32638" or terrain["analysis_crs"] != "EPSG:32638":
        raise ValueError("Metric analysis must use EPSG:32638")
    if config["spatial"]["web_crs"] != "EPSG:4326":
        raise ValueError("Interchange must use EPSG:4326")
    for state in config["gates"].values():
        if not any(state.startswith(prefix) for prefix in vocab["gate_state_prefix"]):
            raise ValueError(f"Unknown gate state: {state}")
    if not config["gates"]["satellite_flood_extent"].startswith(("HOLD", "NO_GO")):
        raise ValueError("Satellite extent gate cannot be GO without a validated evidence envelope")
    if precipitation["preferred_current_run"] == "Final":
        raise ValueError("Final IMERG cannot be the current run one day after the event")

    sources = read_csv("provenance/source_manifest.csv")
    claims = read_csv("provenance/claim_register.csv")
    timeline = read_csv("provenance/event_timeline.csv")
    catalogue = read_csv("provenance/catalog_snapshot.csv")
    settlements = read_csv("data/reference/affected_settlements.csv")
    coordinates = read_csv("provenance/settlement_coordinate_observations.csv")
    for rows, field, label in [
        (sources, "source_id", "sources"), (claims, "claim_id", "claims"), (timeline, "event_id", "timeline"),
        (catalogue, "snapshot_id", "catalogue"), (settlements, "settlement_id", "settlements"),
        (coordinates, "coordinate_observation_id", "coordinate observations"),
    ]:
        validate_unique(rows, field, label)

    source_ids = {row["source_id"] for row in sources}
    settlement_ids = {row["settlement_id"] for row in settlements}
    coordinate_ids = {row["coordinate_observation_id"] for row in coordinates}
    for row in sources:
        parse_timestamp(row["retrieved_utc"])
        for field in ("observation_start_utc", "observation_end_utc"):
            if row[field]:
                parse_timestamp(row[field])
        if row["observation_start_utc"] and row["observation_end_utc"]:
            if parse_timestamp(row["observation_start_utc"]) > parse_timestamp(row["observation_end_utc"]):
                raise ValueError(f"Reversed source observation interval: {row['source_id']}")

    for row in claims:
        if row["status"] not in vocab["claim_status"] or row["confidence"] not in vocab["confidence"]:
            raise ValueError(f"Unknown claim vocabulary: {row['claim_id']}")
        unknown = _ids(row["evidence_source_ids"]) - source_ids
        if unknown:
            raise ValueError(f"Unknown claim sources {unknown}: {row['claim_id']}")
        parse_timestamp(row["claim_time_utc"])
        for field in ("publication_time_utc", "observation_start_utc", "observation_end_utc"):
            if row[field]:
                parse_timestamp(row[field])

    for row in timeline:
        if row["source_id"] not in source_ids:
            raise ValueError(f"Unknown timeline source: {row['source_id']}")
        if row["confidence"] not in vocab["confidence"] or row["evidence_class"] not in vocab["evidence_class"]:
            raise ValueError(f"Unknown timeline vocabulary: {row['event_id']}")
        local = parse_timestamp(row["publication_time_local"])
        utc = parse_timestamp(row["publication_time_utc"])
        if local.astimezone(timezone.utc) != utc.astimezone(timezone.utc):
            raise ValueError(f"Local/UTC mismatch: {row['event_id']}")

    for row in settlements:
        lon, lat = float(row["longitude"]), float(row["latitude"])
        if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            raise ValueError(f"Settlement outside catalogue bbox: {row['settlement_id']}")
        if float(row["coordinate_uncertainty_m"]) <= 0:
            raise ValueError(f"Non-positive coordinate uncertainty: {row['settlement_id']}")
        if row["coordinate_revision_id"] not in coordinate_ids:
            raise ValueError(f"Unknown adopted coordinate observation: {row['settlement_id']}")
        if _ids(row["source_ids"]) - source_ids:
            raise ValueError(f"Unknown settlement source: {row['settlement_id']}")

    for row in coordinates:
        if row["settlement_id"] not in settlement_ids or row["source_id"] not in source_ids:
            raise ValueError(f"Broken coordinate reference: {row['coordinate_observation_id']}")
        parse_timestamp(row["retrieved_utc"])

    item_ids: set[str] = set()
    for row in catalogue:
        if row["item_id"] in item_ids:
            raise ValueError(f"Duplicate catalogue item: {row['item_id']}")
        item_ids.add(row["item_id"])
        if row["source_id"] not in source_ids:
            raise ValueError(f"Unknown catalogue source: {row['snapshot_id']}")
        parse_timestamp(row["acquired_utc"])
        parse_timestamp(row["queried_utc"])
        if row["event_relation"] == "post_event":
            raise ValueError("Snapshot contains post-event data but the flood gate was not reassessed")


def main() -> int:
    validate_project()
    print("PASS: schemas, controlled vocabularies, IDs, references, timezones, CRS rules, AOI bounds and fail-closed gates validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
