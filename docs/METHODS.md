# Methods protocol

## 1. Evidence and chronology

Preserve each material statement as a source- and time-specific claim. Never silently replace an early operational count with a later one. Original Persian text, translation and analyst interpretation must remain distinguishable.

## 2. Study-area construction

Use the exploratory WGS 84 bounding box only for catalogue discovery. Validate settlement centroids against independent cartography, snap defensible pour points to the derived drainage network and expand the analysis to full upstream catchments in EPSG:32638.

## 3. Terrain analysis

Acquire Copernicus DEM GLO-30 and at least one hydrologically conditioned comparison surface when licensing and coverage permit. Record whether each elevation product is a DSM or terrain model.

Derive, with parameter logs:

- elevation and slope;
- depression treatment;
- D8 or explicitly selected flow direction;
- flow accumulation;
- candidate drainage networks across multiple thresholds;
- upstream catchments;
- Height Above Nearest Drainage (HAND), where defensible;
- longitudinal and cross-valley profiles at verified impact locations.

Report features stable across DEM and threshold choices separately from model-sensitive features.

## 4. Precipitation context

Use IMERG V07 half-hourly estimates for regional 30-minute, 3-hour, 6-hour, 24-hour and antecedent accumulations. Replace near-real-time runs with the Final Run when available and preserve both product identities.

IMERG’s 0.1-degree support is not village-scale rainfall. Local station or pluviograph observations take precedence if their metadata and quality can be verified.

## 5. Sentinel-1

- Search by AOI, time, acquisition mode, polarization, orbit direction and relative orbit.
- Prefer multi-scene pre-event baselines from the same geometry.
- Apply documented calibration, noise handling, radiometric terrain correction and orthorectification.
- Retain incidence-angle, shadow and valid-data masks.
- Test VV, VH, ratios and pre/post dB differences without selecting a threshold solely because it looks plausible.
- Remove or label permanent water and known false-positive land covers.
- Publish threshold sensitivity and minimum mapping-unit effects.

## 6. Sentinel-2

- Audit clear pixels over the AOI using SCL/cloud masks.
- Use true colour, SWIR composites, NDWI and MNDWI as complementary evidence.
- Do not interpolate through clouds and call the result observed.
- Separate pre-event land cover from post-event change.

## 7. Exposure

Audit building and road completeness before counting. Compare candidate footprint sources and perform a stratified visual sample against the best permissible reference imagery.

Intersect validated observations or explicitly labelled evidence envelopes with:

- buildings;
- road and railway segments;
- bridges and culvert candidates;
- agricultural land;
- essential services, when source completeness is documented.

Use “potentially exposed” rather than “damaged” unless ground evidence confirms damage.

## 8. Validation and confidence

Geolocate public photos or video frames only through visible landmarks and with privacy safeguards. Each observation receives location, time, source, media-rights status and confidence fields.

Final evidence classes:

1. **Observed impact** — independently geolocated or authoritative site record.
2. **Probable flood-related change** — compatible satellite change plus terrain support and corroboration.
3. **Possible flood-related change** — partial agreement or weak timing.
4. **Terrain susceptibility only** — model support without event observation.
5. **Insufficient observation** — cloud, radar limitations, temporal gap or missing data.

