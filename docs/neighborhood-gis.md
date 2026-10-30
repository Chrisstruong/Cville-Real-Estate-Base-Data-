# Neighborhood GIS integration and learning guide

## Source

- Official layer: https://gisweb.charlottesville.org/gisweb/rest/services/Layers/MapServer/38
- Retrieved: October 30, 2026.
- Layer name: Planning Neighborhoods; polygon geometry.
- Source spatial reference: EPSG:2284 (legacy WKID 102747).
- Export: `query?where=1%3D1&outFields=OBJECTID%2CNAME&outSR=4326&f=geojson`.
- ID: `OBJECTID`, also provided as GeoJSON feature `id`. Display name: `NAME`.
- Source count query and export both contain 19 features, below the service's 1,000-record limit. All exported geometries are Polygon.
- Output coordinates: longitude/latitude, EPSG:4326.
- Bounds: west -78.523773, south 38.009682, east -78.446364, north 38.070533.
- Validation: unique IDs, nonempty names, closed rings, finite local coordinates; all 19 geometries pass Shapely `is_valid` using the existing backend virtual environment.

The checked-in GeoJSON is a snapshot, not an automatically updated feed. Refresh using the export URL, recheck the count and geometry, and update this record.

## Read the code in this order

1. `frontend/src/api/neighborhoods.ts`: GeoJSON types describe the expected data. Runtime validation checks the downloaded payload because TypeScript types do not validate network responses. Bounds scan all polygon parts, so a future MultiPolygon still zooms correctly.
2. `frontend/src/App.tsx`: `useState` holds the selected feature. Passing the setter to the map and the value to the panel lets both components share one selection.
3. `frontend/src/components/MapView.tsx`: the map-creation effect loads neighborhoods independently of property/crime requests. A separate selection effect updates feature state on the existing map. The state setter passed from App is stable, so selecting a feature does not recreate the map.
4. In the map style, a source supplies geometry; fill, line, and symbol layers present that same geometry differently. Layers are placed beneath markers regardless of request completion order. Label glyphs use the MapLibre demo font endpoint, an external runtime dependency.
5. Hover/selection use `setFeatureState`. Paint expressions read those flags. Clicking checks for existing markers first, preserving their popup/cluster behavior.
6. `NeighborhoodDetails.tsx` renders the selection. Clearing sets it to null, removes the selection highlight, and leaves the camera where it is. Hover highlighting can still appear under the pointer.

The panel is beside the map, or above it on narrow screens; it does not cover the viewport. `ResizeObserver` keeps MapLibre's canvas aligned with its container.

## Verification

Baseline build and lint passed. Vite requires execution outside this Windows sandbox because its subprocess otherwise fails with EPERM. The baseline also emits a large-bundle warning.

Automated helper tests: `cd frontend` then `node --test tests/neighborhoods.test.mjs`.

After implementation: production build and lint pass; all three helper tests pass. The existing large-bundle warning remains.

Browser interaction verification remains manual in this environment:

1. Run the normal frontend/backend development setup.
2. Confirm 19 neighborhoods load and labels appear; inspect the network panel for glyph failures.
3. Hover boundaries, select Greenbrier and Fry's Spring, switch selection, select the same neighborhood again, and clear. Confirm zoom encloses the selected boundary.
4. Click property/crime markers and clusters within a neighborhood; they should retain their previous behavior without selecting the polygon underneath.
5. Check narrow-screen layout and keyboard focus on Clear selection.
6. Block the neighborhood GeoJSON request and reload: an error should appear while existing property/crime loading continues.
7. Check console errors and development StrictMode unmount/remount behavior.

Neighborhood selection currently changes highlighting, camera, and panel only. It does not filter points or assign approximate crime records to neighborhoods. Statistics and AI changes remain out of scope.
