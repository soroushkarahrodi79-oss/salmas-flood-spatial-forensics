# Sensor feasibility gate

**Current gate status: HOLD_POST_EVENT_PAIR_REQUIRED**

The live Copernicus Data Space STAC audit covered the catalogue-search AOI through `2026-10-23T23:59:59Z`. It returned no post-event Sentinel-1 GRD or Sentinel-2 L2A item. Monitoring may continue, but flood delineation is not authorized. The reviewable result is the observation-gap map in `outputs/publication/satellite_observation_gap.png`.

## Known pre-event observations

### Sentinel-2

Sentinel-2C acquired tiles `T38SNH` and `T38SMH` at `2026-10-22T07:49:51Z`, before the first currently registered local impact report at `2026-10-22T11:14:00Z`.

The catalogue reports tile-level cloud cover of 27.63% and 48.13%. Those values do not establish clear observation over the study area. Scene-classification masks and an AOI-specific clear-pixel audit are required.

### Sentinel-1

Sentinel-1D acquired a dual-polarization IW GRD scene at `2026-10-21T14:52:30Z`, ascending relative orbit 174. This is a strong temporal baseline but cannot by itself show flood change.

## Requirements to open flood delineation

All conditions are mandatory:

1. at least one post-event acquisition intersects the analytical AOI;
2. a compatible pre-event observation exists with the same relevant acquisition geometry;
3. acquisition time is close enough to retain a plausible flood or aftermath signal;
4. calibration, terrain correction and masks are documented;
5. permanent water and radar shadow/layover are excluded or separately labelled;
6. candidate thresholds are evaluated through sensitivity analysis;
7. results are checked against independent observations and terrain pathways;
8. output language says “change consistent with inundation/wetness” unless validation supports a stronger label.

## Failure modes

- Short-lived water may drain before the next satellite pass.
- Smooth bare soil, irrigation, rainfall-wetted fields and radar geometry can mimic water-related backscatter changes.
- Buildings and vegetation can increase or complicate backscatter during inundation.
- Optical evidence may be obscured by the same storm clouds that produced the flood.
- Pixel spacing is not positional or thematic accuracy.

If these limitations dominate, the scientifically valid output is an observation-gap map and a NO-GO verdict, not a forced flood polygon.

