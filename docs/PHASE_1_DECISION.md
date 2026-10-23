# Phase 1 decision — terrain–rainfall–observation feasibility

**Decision date:** 23 October 2026  
**Milestone verdict:** **HOLD**  
**Terrain component:** **GO — terrain susceptibility only**  
**Precipitation component:** **HOLD — validated observation not acquired**  
**Satellite flood extent:** **HOLD — post-event pair required**

## Decision basis

The project can now reproduce a terrain-based screening model, candidate upstream catchments and transport/drainage intersection candidates. It cannot yet reconstruct event rainfall or observed flood extent. Phase 1 is therefore not a GO for event mapping.

### Terrain findings

The reference run uses Copernicus DEM GLO-30 (a DSM) reprojected to a 30 m EPSG:32638 grid. It tests complete depression filling and a stress test that preserves depressions deeper than 2 m. Mapzen Terrain Tiles provide a second, mixed-source bare-earth sensitivity surface.

For the primary Copernicus/all-filled scenario, the nearest ≥1 km² drainage candidates are 0–424 m from the adopted settlement reference points. Candidate upstream areas are 2.47–7.35 km². None of the five candidate catchments touches the working-grid edge, so raster truncation was not detected. These are not verified impact catchments.

The Copernicus candidate areas are unchanged between the two conditioning scenarios at the selected outlets. The all-filled Mapzen comparison is similar at four candidates but gives 9.00 km² rather than 5.62 km² at Shurik. The stress-test Mapzen routing changes strongly when depressions over 2 m are preserved. At a two-cell spatial tolerance, Copernicus–Mapzen network intersection-over-union falls from 0.54 at 0.5 km² to 0.42 at 10 km². Exact-cell agreement is lower. Individual centerlines and higher-threshold networks are therefore model-sensitive.

### Precipitation finding

NASA identifies IMERG V07 Late Run as the best presently available run; the Final Run normally follows roughly 3.5 months after the observation month. Direct PPS access returned HTTP 401 without registered credentials. No authoritative local gauge or pluviograph amount with verified station identity, units, interval and quality control was found. No precipitation number is published.

### Satellite finding

The live CDSE STAC audit through 23 October 2026 23:59 UTC found no post-event Sentinel-1 or Sentinel-2 item intersecting the catalogue AOI. The event-day Sentinel-2 observations precede the provisional event window, and the closest Sentinel-1 scene is also pre-event. The flood-extent gate remains closed.

## Publication-output checklist

| Output | Decision supported | Inputs and transformations | Valid support | Main uncertainty | Prohibited conclusion |
|---|---|---|---|---|---|
| `terrain_pathway_feasibility.png` | Where terrain routes runoff near reported settlements | GLO-30 → EPSG:32638 → depression treatment → D8 → area thresholds | 30 m model grid; regional pathway screening | DSM artefacts, conditioning, DEM and outlet location | Observed inundation, depth or damage |
| `candidate_catchments.geojson` | What areas are upstream of unverified candidate outlets | Primary D8 routing and nearest ≥1 km² drainage-cell rule | Candidate outlets only | 250–400 m settlement uncertainty; no field-verified crossings | Administrative boundary, event extent or validated basin |
| `drainage_threshold_sensitivity.csv` | Which network features persist across choices | Two DEMs, two conditioning scenarios, five area thresholds, exact and 60 m-tolerance overlap | Working grid | Comparison surface has mixed lineage; overlap metric depends on tolerance | Accuracy estimate or proof of channel presence |
| `candidate_infrastructure_crossings.*` | Where field inspection could test the pathway model | OSM transport snapshot intersected with ≥1 km² modeled network | OSM query window and snapshot date | OSM completeness/position and 30 m drainage geometry | Bridge, culvert, flooding or damage confirmation |
| `satellite_observation_gap.png` | Whether EO supports flood mapping now | CDSE catalogue query and provisional event window | Query AOI and audit time | Catalogue latency; short-lived flood signal | No flooding occurred |
| `phase1_run_manifest.json` | Can the run be repeated and audited? | Config hashes, input hashes, software versions and output hashes | Exact recorded run | Does not capture external service state beyond snapshots | Scientific validity by itself |

## Gates

| Question | Decision | Opening criterion |
|---|---|---|
| Event occurrence | GO (source-reported) | Already met; does not establish extent |
| Terrain analysis | GO_TERRAIN_SUSCEPTIBILITY_ONLY | Independent crossing validation needed for stronger use |
| Regional precipitation context | HOLD_VALIDATED_OBSERVATION_REQUIRED | Checksummed IMERG or verified gauge/pluviograph data |
| Satellite flood extent | HOLD_POST_EVENT_PAIR_REQUIRED | All eight conditions in `SENSOR_GATE.md` |
| Detailed exposure/damage | HOLD_GROUND_TRUTH_REQUIRED | Valid event envelope plus audited receptor completeness |
| Hydraulic depth/velocity | NO_GO_INPUTS_INSUFFICIENT | Hydrograph/rainfall-runoff, geometry, structures and calibration |
| Return period | NO_GO_GAUGE_SERIES_REQUIRED | Suitable gauge series and documented frequency method |
| Climate attribution | OUT_OF_SCOPE | Formal attribution study outside this repository |

## Ruthless self-review

- **Most analyst-sensitive result:** candidate catchment area, because outlet choice and DEM routing change the contributing area.
- **Easiest map to misread:** the blue drainage network; it is modeled susceptibility, not event water. The map states this in its title, legend and footer.
- **Number most at risk of false precision:** catchment area. Machine outputs retain values for reproducibility, but narrative values are rounded and not reported as measurements.
- **Least complete spatial layer:** OSM transport data; intersection candidates are inspection targets only.
- **Likely first hydrologist objection:** unverified outlet locations and 30 m DSM routing across agricultural drainage and structures.
- **Result that can disappear:** high-threshold Mapzen pathways under the preserve-depressions stress test.
- **What is mapped:** topographic susceptibility and candidate pathways, not the event or its consequences.
- **Crucial missing evidence:** validated rainfall observations, a post-event compatible satellite scene and geolocated ground observations.
- **Falsification:** field drainage direction, a verified crossing inconsistent with the model, a better DTM, or a compatible EO pair that contradicts candidate pathways would require revision.
