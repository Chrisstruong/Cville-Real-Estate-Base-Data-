import type { Feature, FeatureCollection, MultiPolygon, Polygon } from "geojson";

export type NeighborhoodFeature = Feature<Polygon | MultiPolygon, {
  OBJECTID: number;
  NAME: string;
}> & { id: number };

export type NeighborhoodCollection = Omit<FeatureCollection<Polygon | MultiPolygon,
  NeighborhoodFeature["properties"]>, "features"> & { features: NeighborhoodFeature[] };

// Types describe our contract; validation checks what actually arrived over HTTP.
export function validateNeighborhoods(value: unknown): NeighborhoodCollection {
  const data = value as NeighborhoodCollection;
  if (!data || data.type !== "FeatureCollection" || !Array.isArray(data.features) || !data.features.length) {
    throw new Error("Neighborhood data must be a nonempty GeoJSON collection.");
  }
  const ids = new Set<number>();
  for (const feature of data.features) {
    if (feature.type !== "Feature" || !Number.isInteger(feature.id) ||
      feature.id !== feature.properties?.OBJECTID || ids.has(feature.id) ||
      typeof feature.properties?.NAME !== "string" || !feature.properties.NAME.trim()) {
      throw new Error("Neighborhood IDs or names are invalid.");
    }
    ids.add(feature.id);
    const geometry = feature.geometry;
    if (!geometry || !["Polygon", "MultiPolygon"].includes(geometry.type)) {
      throw new Error("Neighborhood geometry must be Polygon or MultiPolygon.");
    }
    const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
    if (!Array.isArray(polygons) || !polygons.length) throw new Error("Empty neighborhood geometry.");
    for (const polygon of polygons) {
      if (!Array.isArray(polygon) || !polygon.length) throw new Error("Empty neighborhood polygon.");
      for (const ring of polygon) {
        if (!Array.isArray(ring) || ring.length < 4 || ring.some(point =>
          !Array.isArray(point) || point.length < 2 ||
          !Number.isFinite(point[0]) || !Number.isFinite(point[1]) ||
          Math.abs(point[0]) > 180 || Math.abs(point[1]) > 90
        )) throw new Error("Invalid neighborhood coordinates.");
        const first = ring[0];
        const last = ring[ring.length - 1];
        if (first[0] !== last[0] || first[1] !== last[1]) throw new Error("Neighborhood ring is not closed.");
      }
    }
  }
  return data;
}

export async function fetchNeighborhoods(signal?: AbortSignal) {
  const response = await fetch(`${import.meta.env.BASE_URL}data/planning-neighborhoods.geojson`, { signal });
  if (!response.ok) throw new Error(`Could not load neighborhoods: HTTP ${response.status}`);
  return validateNeighborhoods(await response.json());
}

export function neighborhoodBounds(feature: NeighborhoodFeature): [[number, number], [number, number]] {
  const polygons = feature.geometry.type === "Polygon"
    ? [feature.geometry.coordinates] : feature.geometry.coordinates;
  let west = Infinity, south = Infinity, east = -Infinity, north = -Infinity;
  for (const polygon of polygons) for (const ring of polygon) for (const [lng, lat] of ring) {
    west = Math.min(west, lng);
    south = Math.min(south, lat);
    east = Math.max(east, lng);
    north = Math.max(north, lat);
  }
  return [[west, south], [east, north]];
}
