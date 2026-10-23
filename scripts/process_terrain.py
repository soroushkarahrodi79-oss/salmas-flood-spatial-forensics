#!/usr/bin/env python3
"""Run metric terrain routing, threshold sensitivity and candidate catchments."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

# Do not inherit an unrelated system PROJ installation (common with PostGIS).
# Rasterio and pyproj wheels discover their own compatible projection database.
os.environ.pop("PROJ_LIB", None)
os.environ.pop("PROJ_DATA", None)

import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.features import shapes
from rasterio.warp import Resampling, reproject, transform_bounds
from shapely.geometry import mapping, shape
from shapely.ops import transform as geometry_transform, unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from salmas_flood.acquisition import sha256_file  # noqa: E402
from salmas_flood.terrain import candidate_pour_point, stable_drainage_fraction, terrain_products  # noqa: E402

NODATA = -9999.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publication-dir", default="outputs/publication")
    parser.add_argument("--interim-dir", default="data/interim/terrain")
    parser.add_argument("--skip-figure", action="store_true")
    return parser.parse_args()


def common_grid(config: dict) -> tuple[Affine, int, int]:
    left, bottom, right, top = transform_bounds("EPSG:4326", config["analysis_crs"], *config["working_extent_wgs84"], densify_pts=21)
    resolution = float(config["target_resolution_m"])
    left = np.floor(left / resolution) * resolution
    bottom = np.floor(bottom / resolution) * resolution
    right = np.ceil(right / resolution) * resolution
    top = np.ceil(top / resolution) * resolution
    width, height = int(round((right - left) / resolution)), int(round((top - bottom) / resolution))
    return Affine(resolution, 0, left, 0, -resolution, top), width, height


def read_source(source: dict) -> tuple[np.ndarray, Affine, str, float]:
    path = ROOT / source["path"]
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as handle:
            array = np.frombuffer(handle.read(), dtype=">i2")
        side = int(np.sqrt(array.size))
        if side * side != array.size:
            raise ValueError(f"Unexpected HGT cell count: {array.size}")
        array = array.reshape((side, side)).astype(np.float32)
        transform = Affine(1 / (side - 1), 0, 44, 0, -1 / (side - 1), 39)
        return array, transform, "EPSG:4326", -32768.0
    with rasterio.open(path) as dataset:
        return dataset.read(1).astype(np.float32), dataset.transform, dataset.crs.to_string(), float(dataset.nodata or NODATA)


def warp_source(source: dict, dst_transform: Affine, width: int, height: int) -> np.ndarray:
    data, src_transform, src_crs, src_nodata = read_source(source)
    destination = np.full((height, width), NODATA, dtype=np.float32)
    reproject(
        source=data,
        destination=destination,
        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=src_nodata,
        dst_transform=dst_transform,
        dst_crs="EPSG:32638",
        dst_nodata=NODATA,
        resampling=Resampling.bilinear,
        num_threads=2,
    )
    return destination


def warp_mask(path: Path, dst_transform: Affine, width: int, height: int) -> np.ndarray:
    destination = np.full((height, width), 255, dtype=np.uint8)
    with rasterio.open(path) as dataset:
        reproject(
            source=dataset.read(1), destination=destination,
            src_transform=dataset.transform, src_crs=dataset.crs,
            src_nodata=dataset.nodata, dst_transform=dst_transform, dst_crs="EPSG:32638",
            dst_nodata=255, resampling=Resampling.nearest,
        )
    return destination


def write_raster(path: Path, array: np.ndarray, transform: Affine, nodata: float | int, dtype: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1], count=1,
        dtype=dtype, crs="EPSG:32638", transform=transform, nodata=nodata,
        compress="deflate", predictor=2 if dtype.startswith("float") else 1, tiled=True,
    ) as dataset:
        dataset.write(array.astype(dtype), 1)
        dataset.update_tags(
            ANALYSIS_CLASS="terrain_susceptibility_only",
            PROHIBITED_INTERPRETATION="not observed flood extent; not water depth",
        )


def rows_from_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def catchment_geometry(mask: np.ndarray, transform: Affine):
    polygons = [shape(geometry) for geometry, value in shapes(mask.astype(np.uint8), mask=mask, transform=transform) if value == 1]
    return unary_union(polygons) if polygons else None


def touches_edge(mask: np.ndarray) -> bool:
    return bool(mask[0].any() or mask[-1].any() or mask[:, 0].any() or mask[:, -1].any())


def geojson_feature(geometry, properties: dict, transformer: Transformer) -> dict:
    projected = geometry_transform(transformer.transform, geometry)
    return {"type": "Feature", "properties": properties, "geometry": mapping(projected)}


def make_figure(publication_dir: Path, primary: dict, settlements: list[dict[str, str]], transform: Affine, commit: str) -> None:
    import matplotlib.pyplot as plt
    from bidi.algorithm import get_display
    import arabic_reshaper
    from matplotlib.lines import Line2D
    metric = Transformer.from_crs("EPSG:4326", "EPSG:32638", always_xy=True)

    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    slope = primary["products"]["slope_degrees"]
    valid = np.isfinite(slope) & (slope >= 0)
    image = np.where(valid, slope, np.nan)
    extent = [transform.c, transform.c + transform.a * slope.shape[1], transform.f + transform.e * slope.shape[0], transform.f]
    view = ax.imshow(image, extent=extent, origin="upper", cmap="Greys", vmin=0, vmax=35, alpha=0.72)
    area = primary["products"]["upstream_area_km2"]
    for threshold, color, width in [(1.0, "#56B4E9", 0.35), (5.0, "#0072B2", 0.8)]:
        for feature in primary["flow"].streams(mask=area >= threshold):
            coordinates = np.asarray(feature["geometry"]["coordinates"])
            if coordinates.size:
                ax.plot(coordinates[:, 0], coordinates[:, 1], color=color, linewidth=width, alpha=0.8)
    offsets = {"SET-001": (-52, -26), "SET-002": (-10, 28), "SET-003": (-54, 18), "SET-004": (14, 34), "SET-005": (18, -30)}
    for item in primary["pour_points"]:
        row = next(value for value in settlements if value["settlement_id"] == item["settlement_id"])
        label_fa = get_display(arabic_reshaper.reshape(row["name_fa"]))
        sx, sy = metric.transform(float(row["longitude"]), float(row["latitude"]))
        ax.plot([sx, item["x"]], [sy, item["y"]], color="#6A3D9A", linewidth=0.5, linestyle="--", alpha=0.8)
        ax.scatter(sx, sy, marker="x", s=28, color="#6A3D9A", linewidth=1.1, zorder=5)
        ax.scatter(item["x"], item["y"], marker="o", s=24, facecolor="#E69F00", edgecolor="black", linewidth=0.4, zorder=5)
        ax.annotate(
            f"{row['name_en']}\n{label_fa}", xy=(item["x"], item["y"]), xytext=offsets[row["settlement_id"]],
            textcoords="offset points", fontsize=7, zorder=6,
            arrowprops={"arrowstyle": "-", "linewidth": 0.5, "color": "#333333"},
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none", "pad": 1.5},
        )
    ax.set_title("Salmas Phase 1 — terrain-supported runoff pathways\n22 October 2026 event | candidate drainage only / مسیرهای مدل‌شده، نه گستره سیلاب", fontsize=12)
    ax.set_xlabel("Easting (m), EPSG:32638")
    ax.set_ylabel("Northing (m), EPSG:32638")
    ax.annotate("N", xy=(0.965, 0.94), xytext=(0.965, 0.84), xycoords="axes fraction", ha="center", arrowprops={"arrowstyle": "-|>", "color": "black"}, fontsize=10)
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim(); length = 10000
    sx, sy = x0 + (x1 - x0) * 0.06, y0 + (y1 - y0) * 0.06
    ax.plot([sx, sx + length], [sy, sy], color="black", linewidth=3)
    ax.text(sx + length / 2, sy + (y1 - y0) * 0.012, "10 km", ha="center", fontsize=8)
    ax.text(
        0.01, 0.01,
        f"Terrain susceptibility only — not observed flood extent or depth.\n"
        f"Sources: Copernicus DEM GLO-30 2021; Mapzen Terrain Tiles sensitivity. CRS EPSG:32638. Code {commit}.",
        transform=ax.transAxes, fontsize=7, va="bottom", bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )
    colorbar = fig.colorbar(view, ax=ax, fraction=0.03, pad=0.02)
    colorbar.set_label("Slope (degrees; DSM-derived)")
    ax.legend(handles=[
        Line2D([0], [0], color="#56B4E9", lw=1, label="≥1 km² contributing area"),
        Line2D([0], [0], color="#0072B2", lw=2, label="≥5 km² contributing area"),
        Line2D([0], [0], marker="x", color="#6A3D9A", lw=0, label="reported-settlement reference point"),
        Line2D([0], [0], marker="o", markerfacecolor="#E69F00", markeredgecolor="black", lw=0, label="candidate outlet (unverified)"),
    ], loc="upper left", fontsize=7, framealpha=0.85)
    path = publication_dir / "terrain_pathway_feasibility.png"
    fig.savefig(path, dpi=180, metadata={"Title": "Terrain-supported runoff pathways; insufficient event observation"})
    plt.close(fig)


def main() -> int:
    args = parse_args()
    publication_dir, interim_dir = ROOT / args.publication_dir, ROOT / args.interim_dir
    publication_dir.mkdir(parents=True, exist_ok=True); interim_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / "config/terrain.json").read_text(encoding="utf-8"))
    transform, width, height = common_grid(config)
    settlements = rows_from_csv(ROOT / "data/reference/affected_settlements.csv")
    to_metric = Transformer.from_crs("EPSG:4326", "EPSG:32638", always_xy=True)
    to_wgs84 = Transformer.from_crs("EPSG:32638", "EPSG:4326", always_xy=True)
    scenario_results: dict[str, dict] = {}
    summary_rows: list[dict] = []
    catchment_features: list[dict] = []
    point_features: list[dict] = []
    for source in config["dem_sources"]:
        elevation = warp_source(source, transform, width, height)
        source_key = source["id"].lower()
        write_raster(interim_dir / f"{source_key}_elevation.tif", elevation, transform, NODATA, "float32")
        for scenario in config["conditioning_scenarios"]:
            key = f"{source['id']}__{scenario['id']}"
            print(f"route {key} on {height}x{width} metric cells")
            products = terrain_products(elevation, transform, nodata=NODATA, max_depth_m=float(scenario["max_depth_m"]))
            flow = products.pop("flow")
            scenario_result = {"flow": flow, "products": products, "pour_points": []}
            scenario_results[key] = scenario_result
            for product_name in ("slope_degrees", "filled_elevation_m", "upstream_area_km2", "fill_depth_m"):
                write_raster(interim_dir / f"{source_key}_{scenario['id']}_{product_name}.tif", products[product_name], transform, NODATA, "float32")
            write_raster(interim_dir / f"{source_key}_{scenario['id']}_flow_direction_d8.tif", products["flow_direction_d8"], transform, 247, "uint8")
            for integer_id, settlement in enumerate(settlements, start=1):
                x, y = to_metric.transform(float(settlement["longitude"]), float(settlement["latitude"]))
                point = candidate_pour_point(
                    x, y, products["upstream_area_km2"], transform,
                    float(config["pour_point_search_radius_m"]),
                    float(config["pour_point_minimum_drainage_area_km2"]),
                )
                idx = point.row * width + point.col
                basin = flow.basins(idxs=np.array([idx]), ids=np.array([integer_id], dtype=np.uint32)) == integer_id
                boundary = touches_edge(basin)
                uncertainty = float(settlement["coordinate_uncertainty_m"])
                rr, cc = np.indices(basin.shape)
                nearby = np.hypot((rr - point.row) * abs(transform.e), (cc - point.col) * transform.a) <= uncertainty
                stream_nearby = nearby & (products["upstream_area_km2"] >= 0.5)
                areas = products["upstream_area_km2"][stream_nearby]
                record = {
                    "settlement_id": settlement["settlement_id"], "dem_source": source["id"], "conditioning": scenario["id"],
                    "x": point.x, "y": point.y, "snap_distance_m": point.search_distance_m,
                    "candidate_catchment_area_km2": point.upstream_area_km2,
                    "uncertainty_area_min_km2": float(np.min(areas)) if areas.size else point.upstream_area_km2,
                    "uncertainty_area_max_km2": float(np.max(areas)) if areas.size else point.upstream_area_km2,
                    "catchment_touches_working_edge": boundary,
                    "status": "candidate_unverified_pour_point",
                }
                scenario_result["pour_points"].append(record); summary_rows.append(record)
                if source["id"].startswith("COPDEM") and scenario["id"] == "fill_all_depressions":
                    geom = catchment_geometry(basin, transform)
                    if geom is not None:
                        catchment_features.append(geojson_feature(geom, {k: v for k, v in record.items() if k not in {"x", "y"}}, to_wgs84))
                    point_geom = shape({"type": "Point", "coordinates": [point.x, point.y]})
                    point_features.append(geojson_feature(point_geom, record, to_wgs84))
    thresholds = [float(value) for value in config["drainage_threshold_km2"]]
    stability_rows = []
    for scenario in config["conditioning_scenarios"]:
        keys = [f"{source['id']}__{scenario['id']}" for source in config["dem_sources"]]
        maps = [scenario_results[key]["products"]["upstream_area_km2"] for key in keys]
        for tolerance in (0, 2):
            stability = stable_drainage_fraction(maps, thresholds, tolerance_cells=tolerance)
            for threshold, fraction in stability.items():
                stability_rows.append({"comparison": f"DEM_sources__{scenario['id']}", "tolerance_cells": tolerance, "threshold_km2": threshold, "intersection_over_union": fraction})
    for source in config["dem_sources"]:
        keys = [f"{source['id']}__{scenario['id']}" for scenario in config["conditioning_scenarios"]]
        maps = [scenario_results[key]["products"]["upstream_area_km2"] for key in keys]
        for tolerance in (0, 2):
            stability = stable_drainage_fraction(maps, thresholds, tolerance_cells=tolerance)
            for threshold, fraction in stability.items():
                stability_rows.append({"comparison": f"conditioning__{source['id']}", "tolerance_cells": tolerance, "threshold_km2": threshold, "intersection_over_union": fraction})
    with (publication_dir / "candidate_pour_points.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0])); writer.writeheader(); writer.writerows(summary_rows)
    with (publication_dir / "drainage_threshold_sensitivity.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(stability_rows[0])); writer.writeheader(); writer.writerows(stability_rows)
    (publication_dir / "candidate_catchments.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": catchment_features}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (publication_dir / "candidate_pour_points.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": point_features}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    edm = warp_mask(ROOT / config["dem_sources"][0]["quality_mask_path"], transform, width, height)
    wbm = warp_mask(ROOT / config["dem_sources"][0]["water_mask_path"], transform, width, height)
    quality = {
        "edm_code_counts": {str(int(value)): int(count) for value, count in zip(*np.unique(edm, return_counts=True))},
        "water_mask_code_counts": {str(int(value)): int(count) for value, count in zip(*np.unique(wbm, return_counts=True))},
        "copdem_void_cells": int(np.sum(scenario_results["COPDEM_GLO30_N38E044__fill_all_depressions"]["products"]["filled_elevation_m"] == NODATA)),
        "note": "Codes are reported without relabelling; consult the Copernicus DEM Product Handbook.",
    }
    (publication_dir / "terrain_quality_summary.json").write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    commit = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, text=True).strip()
    primary = scenario_results["COPDEM_GLO30_N38E044__fill_all_depressions"]
    if not args.skip_figure:
        make_figure(publication_dir, primary, settlements, transform, commit)
    config_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in sorted((ROOT / "config").glob("*.json"))}
    inputs = json.loads((ROOT / "data/raw/acquisition_manifest.json").read_text(encoding="utf-8"))
    manifest = {
        "run_id": "phase1-terrain-reference", "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "code_commit": commit, "working_tree_note": "Publication products are committed separately after this code revision.",
        "analysis_crs": "EPSG:32638", "grid": {"width": width, "height": height, "transform": list(transform)[:6]},
        "configuration_sha256": config_hashes, "inputs": inputs,
        "software": {name: version(name) for name in ["numpy", "rasterio", "pyflwdir", "pyproj", "shapely", "matplotlib"]},
        "outputs": {},
        "scientific_class": "terrain_susceptibility_only",
        "prohibited_interpretations": ["observed flood extent", "flood depth", "discharge", "confirmed damage"],
    }
    for path in sorted(publication_dir.iterdir()):
        if path.name != "phase1_run_manifest.json":
            manifest["outputs"][path.name] = {"size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
    (publication_dir / "phase1_run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest['outputs'])} publication outputs; manifest code={commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
