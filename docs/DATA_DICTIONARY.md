# Data dictionary

Pipe-delimited fields contain multiple identifiers. Blank means unknown or not applicable, never zero.

## Evidence tables

### `provenance/source_manifest.csv`

One row per source. Publication/reference date, retrieval time and observation interval are separate. `accessibility` records whether the source could be revisited; `archive_status` states whether a stable capture exists. `limitations` states what the source cannot establish.

### `provenance/claim_register.csv`

One row per material claim. `claim_original_fa`, `claim_translation_en` and `analyst_interpretation` are deliberately separate. `status` and `confidence` must match `config/vocabularies.json`. `evidence_source_ids` must resolve to the source manifest.

### `provenance/event_timeline.csv`

One row per reported event-time statement. Publication time is not silently treated as observation time. `evidence_class` is a communication class, not a numeric probability.

### `provenance/observation_gaps.csv`

One row per unresolved decision-critical gap. `opening_criteria` are mandatory evidence conditions. `prohibited_inference` states what absence of data must not be used to claim.

## Spatial reference tables

### `data/reference/affected_settlements.csv`

Adopted approximate representative points. `coordinate_uncertainty_m` is a working radius informed by cross-source disagreement, not surveyed accuracy. `coordinate_revision_id` resolves to the adopted observation in `settlement_coordinate_observations.csv`. Historical population is context only.

### `provenance/settlement_coordinate_observations.csv`

Append-only coordinate observations from independent sources. `adoption_status` distinguishes the retained baseline from comparison-only positions. A new source requires a new row; never overwrite history.

## Catalogue and acquisitions

### `provenance/catalog_snapshot.csv`

Normalized satellite items used in the gate decision. Empty AOI clear-pixel percentage means it was not calculated because imagery was not acquired. Sentinel-1 geometry is defined by mode, product type, polarization, orbit direction and relative orbit.

### `provenance/acquisition_inventory.csv`

Tracked immutable metadata for locally acquired files. SHA-256 is the local integrity identifier. Large files remain under ignored `data/raw/`.

## Publication outputs

### `candidate_pour_points.csv`

`candidate_catchment_area_km2` is modeled upstream area at the nearest qualifying drainage cell. `uncertainty_area_min_km2` and `uncertainty_area_max_km2` sample qualifying network cells within the settlement uncertainty radius. Machine precision supports deterministic comparison; it is not measurement accuracy.

### `drainage_threshold_sensitivity.csv`

`intersection_over_union` compares binary drainage masks. `tolerance_cells=0` is exact-grid overlap; `2` allows a 60 m neighborhood after dilation. Neither is an accuracy score.

### `candidate_infrastructure_crossings.csv`

Intersections of an OSM transport way with the modeled ≥1 km² drainage network. They are screening candidates. `osm_way_id` supports traceability; no row confirms a bridge, culvert, flood or damage.

### GeoJSON files

All publication GeoJSON uses EPSG:4326 for interchange. Metric calculations occur before export in EPSG:32638.
