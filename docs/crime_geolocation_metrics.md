# Crime geolocation: 11.4.3 and 11.4.4

Measured October 21, 2026 using one repeatable-read, read-only local database
snapshot for both passes.

| Metric | Baseline | Improved |
| --- | ---: | ---: |
| Total records | 26,418 | 26,418 |
| Mapped | 19,189 | 20,302 |
| Unmapped | 7,229 | 6,116 |
| Coverage | 72.64% | 76.85% |

Gain: 1,113 records, or 4.21 percentage points. All original coordinates were
preserved, checked with a multiset comparison including repeated records.
Baseline eligibility: 23,969 records; eligible coverage: 80.06%.

## Mapping methods

- Single road-block midpoint: 19,189 records.
- Connected block-segment midpoint: 5 records.
- Unique shared GIS endpoint for two streets: 1,108 records.

Block matching requires the exact normalized street and block. Multiple segments
must form one connected open endpoint chain without branches or loops. Identical
or reversed duplicate features count once toward length. Source IDs are retained.
Midpoints are measured along the line in UTM zone 17N and converted to WGS84.

Intersections require two verified streets and exactly one shared road-block
endpoint. Geometric crossings alone are insufficient, since they may represent
overpasses. Shared endpoints provide GIS evidence, not independent field verification.

Endpoint keys round coordinates to seven decimal degrees (roughly one centimeter).
Larger gaps are not bridged; near-identical points across rounding boundaries may
remain unmatched. No fuzzy street matching or nearest-block substitution is used.

## Remaining unmapped records

| Reason | Records |
| --- | ---: |
| Disconnected block segments or looped graph | 3,641 |
| Block not found | 799 |
| Unverified street | 576 |
| Branched block | 311 |
| Intersection without a shared endpoint | 294 |
| Missing block | 247 |
| Intersection with multiple shared endpoints | 126 |
| Unknown location | 98 |
| Closed block segment | 24 |

Most multi-segment blocks remain unresolved. Increasing tolerance or choosing
one segment requires further GIS review. Invalid geometry and intersections
with more than two streets also remain unmapped.

## Reproduce and validate

From `backend`, with its Python environment:

```powershell
python -m scripts.profile_crime_geolocation
python -m unittest discover -s tests -p test_crime_geolocation.py -v
```

Six tests passed covering chains, duplicates, branches, gaps, loops, invalid
geometry, ambiguous junctions, crossings without shared endpoints, and baseline
preservation. The original baseline command remains available:
`python -m scripts.profile_crime_block_matches`.

Coordinates remain approximate and in memory only. No database records or schema
were changed. Persistence is 11.4.5; final persisted coverage is 11.4.6.
No visual map inspection was performed during this implementation.
