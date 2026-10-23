# Data policy

Large acquired datasets are deliberately excluded from Git.

## Expected local layout

```text
data/
├── raw/          # Immutable acquired inputs
├── interim/      # Reprojected, clipped or analysis-ready inputs
├── processed/    # Derived analytical products
└── reference/    # Small reviewable reference tables
```

Every acquired input must have:

1. a row in `provenance/source_manifest.csv`;
2. an immutable source identifier or URL;
3. acquisition timestamp in UTC;
4. license or access condition;
5. SHA-256 checksum when a file is downloaded;
6. declared spatial and temporal support;
7. a statement of what the dataset cannot establish.

Satellite-derived water or change layers must never overwrite raw imagery. Regenerable analytical intermediates remain ignored under `data/processed/`. Only deliberately reviewed, lightweight publication artifacts may be tracked under `outputs/publication/`.

The local machine-readable acquisition log is `data/raw/acquisition_manifest.json`; it is regenerated from validated downloads and excluded from Git. The reviewable inventory in `provenance/acquisition_inventory.csv` records provider, product/version, immutable identifier, exact query or URL, retrieval time, coverage, CRS, resolution, terms, size, SHA-256, analytical role and limitations. The repository MIT license covers code and repository-authored text only; third-party data retain their own terms.

