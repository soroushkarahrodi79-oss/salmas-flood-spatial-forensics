# Uncertainty model

Uncertainty is represented by source category and sensitivity, not compressed into a single confidence percentage.

| Component | Representation | Propagation | Failure mode |
|---|---|---|---|
| Event report | claim status, confidence and time-specific versions | Preserve every operational count | Treating a later count as a final census |
| Report time | separate publication and observation fields | Unknown observation times remain blank | Assuming post time equals event time |
| Settlement position | source observations plus 250–400 m working radius | Sample alternative qualifying drainage cells | Point represents a centroid, not impact location |
| Elevation | primary DSM and independent mixed-source DEM | Compare routing and candidate area | Vegetation, buildings, void edits and vertical artefacts |
| Conditioning | fill-all and preserve-depressions-over-2-m stress test | Compare networks and candidate areas | Artificial breach/fill or disconnected pits |
| Routing | D8 | Threshold and DEM comparison | Single-flow routing misses divergent flow |
| Network threshold | 0.5, 1, 2, 5 and 10 km² | Publish exact and 60 m-tolerance overlap | Threshold selected for appearance |
| Precipitation | no value until identity, run, time and checksum validate | Fail closed on missing half-hours | Village-scale interpretation of a 0.1° estimate |
| Satellite | catalogue and geometry gate | No extent unless all mandatory conditions pass | Temporal recession, cloud, shadow, wet soil and orbit mismatch |
| Transport | OSM snapshot and candidate intersections | No totals or damage class | Missing/outdated ways and positional mismatch |

## Confidence vocabulary

`none`, `low`, `medium`, `medium_high` and `high` describe support for the stated claim at its declared spatial and temporal support. They are ordinal review labels, not probabilities.

## Precision policy

Raw machine outputs may retain floating-point precision for reproducibility. Scientific prose and map labels must round to the evidence support. A 30 m raster and approximate outlet do not justify decimal-metre location claims or hundredths of square kilometres as measured truth.

## Correlation warning

DEM-source and conditioning uncertainties are not independent. Both surfaces contain radar-derived and edited terrain information, and both routing scenarios use D8. Agreement therefore does not constitute independent validation.
