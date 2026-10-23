# Salmas Flood 2026 — Open Spatial Forensics

[![QA](https://github.com/soroushkarahrodi79-oss/salmas-flood-spatial-forensics/actions/workflows/qa.yml/badge.svg)](https://github.com/soroushkarahrodi79-oss/salmas-flood-spatial-forensics/actions/workflows/qa.yml)

**Status: PHASE 1 HOLD / TERRAIN SUSCEPTIBILITY AVAILABLE / VALIDATED RAINFALL AND SATELLITE FLOOD EXTENT UNAVAILABLE**

This repository is an independent, reproducible reconstruction of the flash-flood event reported in rural Salmas County, West Azerbaijan Province, Iran, on **22 October 2026 (30 Mehr 1405)**.

The project asks:

> How far can open Earth observation, terrain analysis and time-stamped public evidence robustly reconstruct the Salmas flash flood and identify potentially exposed receptors without claiming precision that the available observations do not support?

## Current evidence state

- Heavy rainfall, hail and flash flooding were reported during the afternoon of 22 October 2026.
- Initial operational reporting named Kaniyan, Shurik, Silab, Mafi Kandi and Shekeryazi; later reporting used a four-village scope.
- Casualty and dwelling counts evolved during response operations and are preserved as time-stamped claims rather than collapsed into one supposedly final number.
- A Sentinel-2 acquisition at 07:49 UTC on the event date provides a same-day pre-event baseline.
- A Sentinel-1 acquisition at 14:52 UTC on 21 October provides a close radar baseline.
- A live Copernicus catalogue audit through 23 October 2026 found no post-event Sentinel-1 or Sentinel-2 acquisition intersecting the search AOI. No flood polygon is therefore authorized.
- Reproducible terrain outputs identify modelled runoff pathways and candidate upstream catchments; they are susceptibility evidence, not an observed event extent.
- The configured IMERG Late Run is credential-gated at the provider and no verified local gauge or pluviograph observation was found. No precipitation accumulation is published.

See [Project scope](docs/PROJECT_SCOPE.md), [Sensor gate](docs/SENSOR_GATE.md), [Methods](docs/METHODS.md), and [Limitations](docs/LIMITATIONS.md).

## Analytical model

The study follows a source–pathway–receptor–consequence structure:

1. **Source** — rainfall, hail and antecedent wetness.
2. **Pathway** — upstream catchments, terrain convergence, drainage and infrastructure crossings.
3. **Receptor** — settlements, buildings, roads, railway, agricultural land and services.
4. **Consequence** — observed impacts and explicitly labelled potential exposure.

The intended spatial result is a multi-evidence envelope with separate classes for observed impact, satellite-consistent change, terrain-supported pathway, susceptibility-only areas and insufficient observation. It is not a single overconfident flood polygon.

## Claim boundary

The project may reconstruct an event timeline, model terrain-supported runoff pathways, describe regional precipitation context, identify satellite-observed changes and estimate potential exposure subject to documented completeness tests.

It does **not** currently estimate flood depth, velocity, discharge, return period, building damage, economic loss, climate attribution or operational early-warning performance.

## Initial study area

- Exploratory bounding box: `44.70, 38.24, 45.00, 38.38` (WGS 84)
- Analysis CRS: `EPSG:32638` (WGS 84 / UTM zone 38N)
- Event timezone: `Asia/Tehran` (`UTC+03:30` on the event date)

The analytical area must expand to the upstream catchments derived from validated pour points. The exploratory bounding box is a catalogue-search window, not a hydrological boundary.

## Repository map

| Path | Function |
|---|---|
| `config/study.json` | Machine-readable scope, gates and spatial configuration |
| `config/terrain.json` | DEM, conditioning, routing and threshold parameters |
| `config/precipitation.json` | IMERG identity, event timing and accumulation windows |
| `provenance/source_manifest.csv` | Sources, retrieval state and analytical role |
| `provenance/claim_register.csv` | Versioned material claims and confidence |
| `provenance/event_timeline.csv` | Time-stamped event observations |
| `provenance/catalog_snapshot.csv` | Initial Copernicus catalogue observations |
| `data/reference/affected_settlements.csv` | Approximate settlement seed coordinates |
| `scripts/query_cdse_catalog.py` | Re-runnable CDSE STAC catalogue query |
| `scripts/acquire_data.py` | Idempotent, checksummed acquisition of spatially constrained inputs |
| `scripts/process_terrain.py` | Reproducible terrain sensitivity and candidate-catchment workflow |
| `scripts/plot_observation_gap.py` | Publication map of the unresolved satellite-observation gap |
| `scripts/validate_project.py` | Dependency-free repository QA |
| `docs/` | Scope, methods, gates and limitations |

Raw satellite imagery, DEMs and other large third-party datasets are not committed. Their exact identifiers, licenses, retrieval dates and checksums belong in the source manifest and acquisition records.

## Quick validation

```bash
python scripts/validate_project.py
python -m unittest discover -s tests -v
```

For the full analytical environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.txt
.venv/bin/python -m pip install -e .
.venv/bin/python scripts/process_terrain.py
.venv/bin/python scripts/plot_observation_gap.py
```

On Windows, replace `.venv/bin/python` with `.venv\\Scripts\\python`.

Query the live Copernicus catalogue without downloading imagery:

```bash
python scripts/query_cdse_catalog.py --collection sentinel-1-grd
python scripts/query_cdse_catalog.py --collection sentinel-2-l2a
```

## Publication language

The canonical scientific record is English. Public-facing maps and the eventual evidence viewer should be bilingual **Persian–English**, with original Persian statements preserved separately from translations.

## Ethics

Do not publish identifiable victims, exact household locations, private contact details or unlicensed media. Social-media material is a lead for verification, not automatic ground truth.

