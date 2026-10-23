"""Copernicus STAC normalization and fail-closed observation gate."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp lacks an offset: {value}")
    return parsed


def normalize_feature(feature: dict[str, Any], collection: str) -> dict[str, Any]:
    properties = feature.get("properties", {})
    geometry = feature.get("geometry")
    item_id = feature.get("id")
    acquired = properties.get("datetime")
    if not item_id or not acquired or not geometry:
        raise ValueError("STAC feature requires id, properties.datetime and geometry")
    normalized = {
        "collection": collection,
        "item_id": item_id,
        "acquired_utc": acquired,
        "satellite": properties.get("platform") or item_id.split("_")[0],
        "acquisition_mode": properties.get("sar:instrument_mode"),
        "product_type": properties.get("sar:product_type") or properties.get("product:type"),
        "polarizations": properties.get("sar:polarizations") or [],
        "orbit_direction": properties.get("sat:orbit_state"),
        "relative_orbit": properties.get("sat:relative_orbit"),
        "processing_level": properties.get("processing:level"),
        "tile_id": properties.get("s2:mgrs_tile") or properties.get("grid:code") or _tile_from_id(item_id),
        "catalogue_cloud_cover_percent": properties.get("eo:cloud_cover"),
        "geometry": geometry,
        "bbox": feature.get("bbox"),
    }
    return normalized


def _tile_from_id(item_id: str) -> str | None:
    for token in item_id.split("_"):
        if len(token) == 6 and token.startswith("T"):
            return token
    return None


def event_relation(acquired_utc: str, event_start_utc: str, event_end_utc: str) -> str:
    acquired = _utc(acquired_utc)
    if acquired < _utc(event_start_utc):
        return "pre_event"
    if acquired <= _utc(event_end_utc):
        return "during_event_window"
    return "post_event"


def s1_geometry_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        item.get("acquisition_mode"),
        item.get("product_type"),
        tuple(item.get("polarizations") or []),
        item.get("orbit_direction"),
        item.get("relative_orbit"),
    )


def satellite_gate(items: Iterable[dict[str, Any]]) -> tuple[str, list[str]]:
    """Assess only catalogue conditions; processing/corroboration remain mandatory."""
    rows = list(items)
    post = [row for row in rows if row.get("event_relation") == "post_event"]
    reasons: list[str] = []
    if not post:
        return "HOLD_POST_EVENT_PAIR_REQUIRED", ["No post-event catalogue item intersects the AOI."]
    compatible_pair = False
    for candidate in post:
        if candidate["collection"] == "sentinel-1-grd":
            key = s1_geometry_key(candidate)
            compatible_pair |= any(
                row.get("event_relation") == "pre_event"
                and row["collection"] == candidate["collection"]
                and s1_geometry_key(row) == key
                for row in rows
            )
        else:
            compatible_pair |= any(
                row.get("event_relation") == "pre_event"
                and row["collection"] == candidate["collection"]
                and row.get("tile_id") == candidate.get("tile_id")
                for row in rows
            )
    if not compatible_pair:
        reasons.append("No geometrically compatible pre/post pair is catalogued.")
    reasons.append("Calibration, masks, timing, threshold sensitivity and independent corroboration are not yet validated.")
    return "HOLD_PROCESSING_AND_CORROBORATION_REQUIRED", reasons
