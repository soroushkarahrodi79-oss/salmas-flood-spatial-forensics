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

Satellite-derived water or change layers must never overwrite raw imagery. Regenerable outputs belong under `data/processed/` or `outputs/` and remain ignored until a publication package is deliberately released.

