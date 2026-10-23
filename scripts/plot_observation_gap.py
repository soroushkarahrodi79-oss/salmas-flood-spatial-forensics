#!/usr/bin/env python3
"""Render the satellite observation-gap decision without inventing flood extent."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

os.environ.pop("PROJ_LIB", None)
os.environ.pop("PROJ_DATA", None)

import arabic_reshaper
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    config = json.loads((ROOT / "config/study.json").read_text(encoding="utf-8"))
    with (ROOT / "data/reference/affected_settlements.csv").open(encoding="utf-8", newline="") as handle:
        settlements = list(csv.DictReader(handle))
    with (ROOT / "provenance/catalog_snapshot.csv").open(encoding="utf-8", newline="") as handle:
        catalogue = list(csv.DictReader(handle))
    transform = Transformer.from_crs("EPSG:4326", "EPSG:32638", always_xy=True)
    bbox = config["spatial"]["catalogue_bbox_wgs84"]
    left, bottom = transform.transform(bbox[0], bbox[1]); right, top = transform.transform(bbox[2], bbox[3])
    commit = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, text=True).strip()
    figure, (ax, timeline) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [4, 1]}, constrained_layout=True)
    ax.add_patch(Rectangle((left, bottom), right-left, top-bottom, facecolor="#D9D9D9", edgecolor="#555555", hatch="//", linewidth=1.2))
    for index, row in enumerate(settlements):
        x, y = transform.transform(float(row["longitude"]), float(row["latitude"]))
        fa = get_display(arabic_reshaper.reshape(row["name_fa"]))
        ax.scatter(x, y, marker="x", color="#6A3D9A", zorder=3)
        ax.annotate(f"{row['name_en']} / {fa}", (x, y), xytext=(5, 6 + 8 * (index % 2)), textcoords="offset points", fontsize=7)
    status_fa = get_display(arabic_reshaper.reshape("مشاهده پس از رخداد ناکافی است"))
    ax.text((left+right)/2, (bottom+top)/2, f"INSUFFICIENT POST-EVENT OBSERVATION\n{status_fa}", ha="center", va="center", fontsize=13, color="#333333", bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#555555"})
    ax.annotate("N", xy=(0.96, 0.94), xytext=(0.96, 0.78), xycoords="axes fraction", ha="center", arrowprops={"arrowstyle": "-|>", "color": "black"})
    ax.plot([left + 1500, left + 11500], [bottom + 1200, bottom + 1200], color="black", linewidth=3)
    ax.text(left + 6500, bottom + 1500, "10 km", ha="center", fontsize=8)
    ax.set_aspect("equal"); ax.set_xlabel("Easting (m), EPSG:32638"); ax.set_ylabel("Northing (m), EPSG:32638")
    ax.set_title("Salmas satellite observation gate — audit through 23 October 2026\nNo post-event Sentinel-1 or Sentinel-2 scene in the live catalogue snapshot")
    ax.legend(handles=[
        Line2D([0], [0], marker="x", lw=0, color="#6A3D9A", label="approximate settlement reference"),
        Rectangle((0, 0), 1, 1, facecolor="#D9D9D9", edgecolor="#555555", hatch="//", label="catalogue search AOI; insufficient observation"),
    ], loc="lower left", fontsize=8)
    event_start = utc(config["event"]["event_window_utc"]["start"]); event_end = utc(config["event"]["event_window_utc"]["end"])
    timeline.axvspan(event_start, event_end, color="#E69F00", alpha=0.25, label="provisional event window")
    for row in catalogue:
        acquired = utc(row["acquired_utc"])
        y = 1 if row["collection"] == "sentinel-1-grd" else 0
        marker = "^" if y else "s"
        timeline.scatter(acquired, y, marker=marker, s=55, color="#0072B2")
        timeline.annotate(row["satellite"] if y else row["tile_id"], (acquired, y), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=7)
    timeline.set_yticks([0, 1], ["Sentinel-2", "Sentinel-1"])
    timeline.set_xlim(utc("2026-10-21T00:00:00Z"), utc("2026-10-24T00:00:00Z"))
    timeline.xaxis.set_major_formatter(mdates.DateFormatter("%d Oct\n%H:%M", tz=event_start.tzinfo))
    timeline.grid(axis="x", alpha=0.25)
    timeline.text(0.01, -0.75, f"Status: HOLD_POST_EVENT_PAIR_REQUIRED. CRS EPSG:32638. Sources: CDSE STAC snapshot. Code {commit}.\nA non-detection later would not prove no flooding; no flood extent is mapped here.", transform=timeline.transAxes, fontsize=7)
    output = ROOT / "outputs/publication/satellite_observation_gap.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, metadata={"Title": "Salmas satellite observation gap"})
    plt.close(figure)
    print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
