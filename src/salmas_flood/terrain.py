"""Metric-CRS terrain primitives used by the Phase 1 command-line workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pyflwdir
from affine import Affine
from pyflwdir import dem


@dataclass(frozen=True)
class PourPoint:
    x: float
    y: float
    row: int
    col: int
    upstream_area_km2: float
    search_distance_m: float


def assert_metric_north_up(transform: Affine) -> None:
    if transform.a <= 0 or transform.e >= 0 or transform.b != 0 or transform.d != 0:
        raise ValueError("A north-up metric grid is required")
    if not np.isclose(abs(transform.a), abs(transform.e), rtol=0.01):
        raise ValueError("Approximately square cells are required")


def terrain_products(
    elevation_m: np.ndarray,
    transform: Affine,
    nodata: float = -9999.0,
    max_depth_m: float = -1.0,
) -> dict[str, object]:
    assert_metric_north_up(transform)
    elevation = np.asarray(elevation_m, dtype=np.float32)
    if elevation.ndim != 2:
        raise ValueError("Elevation must be a 2D array")
    filled, d8 = dem.fill_depressions(
        elevation,
        nodata=nodata,
        max_depth=max_depth_m,
        outlets="edge",
    )
    flow = pyflwdir.from_array(d8, ftype="d8", transform=transform, latlon=False)
    area_km2 = flow.upstream_area(unit="km2")
    gy, gx = np.gradient(filled, abs(transform.e), transform.a)
    slope_degrees = np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
    return {
        "flow": flow,
        "filled_elevation_m": filled.astype(np.float32),
        "flow_direction_d8": d8,
        "upstream_area_km2": area_km2.astype(np.float32),
        "slope_degrees": slope_degrees,
        "fill_depth_m": np.where(elevation == nodata, np.nan, filled - elevation).astype(np.float32),
    }


def candidate_pour_point(
    x: float,
    y: float,
    upstream_area_km2: np.ndarray,
    transform: Affine,
    search_radius_m: float,
    minimum_drainage_area_km2: float = 1.0,
) -> PourPoint:
    assert_metric_north_up(transform)
    inverse = ~transform
    col_f, row_f = inverse * (x, y)
    row0, col0 = int(round(row_f - 0.5)), int(round(col_f - 0.5))
    rows, cols = np.indices(upstream_area_km2.shape)
    distance = np.hypot((rows - row0) * abs(transform.e), (cols - col0) * transform.a)
    eligible = (
        (distance <= search_radius_m)
        & np.isfinite(upstream_area_km2)
        & (upstream_area_km2 >= minimum_drainage_area_km2)
    )
    if not np.any(eligible):
        raise ValueError("No drainage cell meeting the contributing-area threshold within search radius")
    # Nearest qualifying network cell is less biased toward the outer search edge
    # than maximizing area. Break equal-distance ties toward the larger pathway.
    candidate_rows, candidate_cols = np.where(eligible)
    order = np.lexsort(
        (-upstream_area_km2[candidate_rows, candidate_cols], distance[candidate_rows, candidate_cols])
    )
    row, col = candidate_rows[order[0]], candidate_cols[order[0]]
    px, py = transform * (col + 0.5, row + 0.5)
    return PourPoint(
        x=float(px),
        y=float(py),
        row=int(row),
        col=int(col),
        upstream_area_km2=float(upstream_area_km2[row, col]),
        search_distance_m=float(distance[row, col]),
    )


def stable_drainage_fraction(
    area_maps: Iterable[np.ndarray], thresholds_km2: Iterable[float], tolerance_cells: int = 0
) -> dict[float, float]:
    maps = [np.asarray(item) for item in area_maps]
    if len(maps) < 2:
        raise ValueError("At least two scenarios are required for stability")
    if any(item.shape != maps[0].shape for item in maps):
        raise ValueError("Scenario grids must share a shape")
    result: dict[float, float] = {}
    for threshold in thresholds_km2:
        masks = [item >= threshold for item in maps]
        if tolerance_cells:
            from scipy.ndimage import binary_dilation

            structure = np.ones((2 * tolerance_cells + 1, 2 * tolerance_cells + 1), dtype=bool)
            masks = [binary_dilation(mask, structure=structure) for mask in masks]
        union = np.logical_or.reduce(masks)
        intersection = np.logical_and.reduce(masks)
        result[float(threshold)] = float(intersection.sum() / union.sum()) if union.any() else 1.0
    return result
