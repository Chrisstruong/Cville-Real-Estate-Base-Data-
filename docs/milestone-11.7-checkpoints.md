# Milestone 11.7: Neighborhood GIS integration

## Implementation status — October 30, 2026

The first implementation of checkpoints 1–6 is present. Production build, lint, three neighborhood helper tests, source/export count comparison, and Shapely geometry validation pass. Browser verification is still pending; unchecked acceptance items below must not be interpreted as verified. See `docs/neighborhood-gis.md` for provenance, a code-reading guide, and the manual walkthrough. No backend or deployment changes were made.

## Scope and pairing workflow

Display official Charlottesville Planning Neighborhood boundaries, labels, hover highlighting, selection, zoom, and a placeholder details panel. Preserve property and crime interactions.

For each checkpoint: explain the change, implement a small piece together, verify the result, and review before continuing. Check boxes only after verification.

Neighborhood statistics, crime aggregation, property comparisons, building-age analysis, and new AI tools belong to later milestones. Construction-year data must be obtained before building-age analysis. Approximate crime coordinates must not be treated as precise neighborhood assignments.

## Repository review

Confirmed in source code (live services and database were not tested for this review):

- `frontend/src/components/MapView.tsx` initializes MapLibre with an OSM raster basemap, loads property and crime data, renders clusters and individual points, expands clusters, and opens detail popups.
- Crime popups support multiple records at a shared location and explain location precision. Property clicks defer to overlapping crime markers.
- `frontend/src/App.tsx` renders `CrimeDataStatus` and `MapView`; it has no neighborhood state or panel.
- `frontend/src/api/properties.ts` and `crimes.ts` provide map and detail requests.
- `backend/app/main.py` defines property list/largest/map/detail endpoints, crime map/detail endpoints, chat and streaming-chat endpoints, and health endpoints. Endpoint definitions alone do not establish runtime health.
- No neighborhood data asset, map source/layers, selection state, or neighborhood panel was found in the inspected implementation.
- Frontend scripts provide `build` and `lint`; no frontend test script is configured.

The working tree already contains user changes, including changes to `backend/app/main.py`. Preserve them. An unrelated `Wstreet_name` reference in the test-property-street endpoint appears undefined; track separately from this milestone.

## Checkpoints

### 0. Establish the baseline

- [x] Read AGENTS.md and inspect the map, API clients, application component, and endpoint definitions.
- [x] Run frontend build and lint; record pre-existing failures separately.
- [ ] Manually confirm property/crime clusters, zoom, popups, and overlapping-marker behavior in the running application.

Done when: we have a known baseline for regression checks.

### 1. Inspect the official GIS source

- [ ] Read layer metadata: https://gisweb.charlottesville.org/gisweb/rest/services/Layers/MapServer/38
- [ ] Verify the actual ID/name fields, geometry type, source spatial reference, query formats, record limit, and feature count.
- [ ] Query all polygons as GeoJSON with output spatial reference EPSG:4326; account for transfer limits if needed.
- [ ] Validate unique nonempty IDs, nonempty names, Polygon/MultiPolygon geometry, finite longitude/latitude coordinates, closed rings, and geometry validity.
- [ ] Confirm exported feature count matches the source and visually check Charlottesville coverage.

Done when: the dataset and its field mapping are verified, without guessing field names or neighborhood counts.

### 2. Add a reproducible neighborhood asset

- [ ] Save validated data to `frontend/public/data/planning-neighborhoods.geojson`.
- [ ] Record source URL, retrieval date, field mapping, CRS, count, and validation results in `docs/neighborhood-gis.md`.
- [ ] Add typed loading and validation in `frontend/src/api/neighborhoods.ts`.
- [ ] Provide clear loading/error handling and cancel pending requests on unmount.

Done when: the frontend can load the local asset independently of property/crime requests. A checked-in snapshot avoids requiring a new backend endpoint or live GIS availability on every page load.

### 3. Render boundaries and labels

- [ ] Add the neighborhood GeoJSON source with stable feature IDs.
- [ ] Add translucent fills and visible outlines above the basemap and below existing markers.
- [ ] Add labels using the verified name field; verify font/glyph configuration for the existing raster style.
- [ ] Ensure layer order remains correct regardless of which dataset loads first.

Done when: neighborhoods and readable labels appear, with property/crime markers still visible and clickable.

### 4. Implement hover highlighting

- [ ] Track the hovered neighborhood using feature state and update its appearance.
- [ ] Clear hover state on pointer exit and use a suitable cursor.
- [ ] Preserve marker cursor behavior where markers overlap polygons.

Done when: moving between neighborhoods highlights only the intended feature and leaves no stuck highlight.

### 5. Select and zoom

- [ ] Add selected-neighborhood React state in `App.tsx` and connect it to `MapView` through props.
- [ ] Clicking a polygon selects it and keeps a persistent selection highlight.
- [ ] Compute bounds for Polygon and MultiPolygon features and use `fitBounds` with panel-aware padding.
- [ ] Give existing property/crime points and clusters click priority so their clicks do not also select or zoom a neighborhood.

Done when: selecting different neighborhoods updates state and zoom correctly, including repeated selections, without recreating the map.

### 6. Add the placeholder panel and clear selection

- [ ] Create `frontend/src/components/NeighborhoodDetails.tsx` showing the selected name and a clear-selection button.
- [ ] Show a helpful empty-selection prompt and state that statistics are not yet available; do not invent values.
- [ ] Add responsive panel styling and ensure the map resizes if its container changes.
- [ ] Clearing selection removes the selected highlight and panel details; define and verify the intended camera behavior.

Done when: select, switch, and clear work consistently on desktop and narrow screens, and the clear button is keyboard accessible.

### 7. Verify the complete milestone

- [ ] Run frontend build and lint and compare results with the baseline.
- [ ] Verify labels, hover, selection, bounds, panel, and clear behavior.
- [ ] Recheck property/crime clusters and detail popups, including overlapping markers and shared crime locations.
- [ ] Simulate a neighborhood-data failure: show an understandable error while existing datasets still work.
- [ ] Confirm cleanup during unmount/remount and check browser console/network errors.
- [ ] Record results and remaining limitations in `docs/neighborhood-gis.md`.

Done when: all milestone 11.7 behaviors pass and existing map functionality is preserved.

## Expected file changes

Modify:

- `frontend/src/components/MapView.tsx`: neighborhood loading/layers/events and selection props.
- `frontend/src/App.tsx`: selection state and panel composition.
- `frontend/src/App.css`: panel/layout styling, with its import added if needed after inspecting current styles.

Create:

- `frontend/public/data/planning-neighborhoods.geojson`: verified official polygons.
- `frontend/src/api/neighborhoods.ts`: neighborhood types and asset loader.
- `frontend/src/components/NeighborhoodDetails.tsx`: placeholder panel.
- `docs/neighborhood-gis.md`: provenance and verification notes.

No backend, database, AI, or deployment configuration change is expected for this milestone. Add a retrieval script only if needed to make source export/validation reproducible.
