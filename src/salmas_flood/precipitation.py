"""Time-support-safe precipitation accumulation helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

import numpy as np


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")
    return parsed


def accumulation_window(
    records: Iterable[tuple[str, np.ndarray]], end_utc: str, hours: float
) -> np.ndarray:
    """Sum complete half-hour accumulations in the left-open/right-closed window."""
    if hours <= 0 or (hours * 2) % 1:
        raise ValueError("Window must be a positive multiple of 30 minutes")
    end = parse_utc(end_utc)
    start = end - timedelta(hours=hours)
    selected = [array for timestamp, array in records if start < parse_utc(timestamp) <= end]
    expected = int(hours * 2)
    if len(selected) != expected:
        raise ValueError(f"Incomplete window: expected {expected} half-hours, found {len(selected)}")
    shape = selected[0].shape
    if any(array.shape != shape for array in selected):
        raise ValueError("Grid shape changed within accumulation window")
    return np.sum(np.stack(selected, axis=0), axis=0, dtype=np.float64)


def regional_summary(array_mm: np.ndarray, valid_mask: np.ndarray) -> dict[str, float | int]:
    values = array_mm[np.asarray(valid_mask, dtype=bool)]
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ValueError("No valid IMERG cells intersect the requested support")
    return {
        "cell_count": int(values.size),
        "minimum_mm": float(np.min(values)),
        "mean_mm": float(np.mean(values)),
        "maximum_mm": float(np.max(values)),
    }
