import type { FeatureCollection, LineString } from "geojson";
import { apiUrl } from "./baseUrl";
import type { CrimeFeature, CrimeFeatureCollection } from "./crimes";
import { parseMapAction, type ShowStreetCrimesAction } from "./mapActions";
import {
  CRIME_CATEGORIES,
  type CrimeCategory,
} from "../config/crimeCategories";

export type StreetCrimeResult = {
  street: {
    street_id: string;
    name: string;
  };
  filters: ShowStreetCrimesAction["filters"];
  summary: {
    associated_record_count: number;
    mapped_record_count: number;
    unmapped_record_count: number;
    records_by_category: Record<CrimeCategory, number>;
  };
  record_ids: number[];
  crimes: CrimeFeatureCollection;
  road_blocks: FeatureCollection<
    LineString,
    { objectid: number; block_number: number | null }
  >;
};

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Invalid street result object.");
  }
  return value as Record<string, unknown>;
}

function integer(value: unknown): number {
  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value < 0
  ) {
    throw new Error("Invalid street result count or identifier.");
  }
  return value;
}

function position(value: unknown): [number, number] {
  if (
    !Array.isArray(value) ||
    value.length !== 2 ||
    typeof value[0] !== "number" ||
    typeof value[1] !== "number" ||
    !Number.isFinite(value[0]) ||
    !Number.isFinite(value[1]) ||
    Math.abs(value[0]) > 180 ||
    Math.abs(value[1]) > 90
  ) {
    throw new Error("Invalid street result coordinates.");
  }
  return [value[0], value[1]];
}

function features(value: unknown): unknown[] {
  const collection = object(value);
  if (
    collection.type !== "FeatureCollection" ||
    !Array.isArray(collection.features) ||
    collection.features.length > 10_000
  ) {
    throw new Error("Invalid street feature collection.");
  }
  return collection.features;
}

function category(value: unknown): CrimeCategory {
  if (
    typeof value !== "string" ||
    !Object.prototype.hasOwnProperty.call(CRIME_CATEGORIES, value)
  ) {
    throw new Error("Invalid street crime category.");
  }
  return value as CrimeCategory;
}

export function validateStreetCrimeResult(
  value: unknown,
  requested: ShowStreetCrimesAction,
): StreetCrimeResult {
  const data = object(value);
  const street = object(data.street);

  const returned = parseMapAction({
    type: "SHOW_STREET_CRIMES",
    street_id: street.street_id,
    filters: data.filters,
  });

  if (
    returned.street_id !== requested.street_id ||
    returned.filters.start_date !== requested.filters.start_date ||
    returned.filters.end_date !== requested.filters.end_date ||
    returned.filters.category !== requested.filters.category
  ) {
    throw new Error("Street results do not match the requested filters.");
  }

  if (typeof street.name !== "string" || !street.name.trim()) {
    throw new Error("The street name is missing.");
  }

  if (!Array.isArray(data.record_ids) || data.record_ids.length > 10_000) {
    throw new Error("Invalid street record list.");
  }

  const recordIds = data.record_ids.map(integer);
  const recordSet = new Set(recordIds);

  if (recordSet.size !== recordIds.length) {
    throw new Error("Street results contain duplicate records.");
  }

  const summary = object(data.summary);
  const associated = integer(summary.associated_record_count);
  const mapped = integer(summary.mapped_record_count);
  const unmapped = integer(summary.unmapped_record_count);
  const rawCounts = object(summary.records_by_category);

  const categoryKeys = Object.keys(CRIME_CATEGORIES) as CrimeCategory[];
  if (Object.keys(rawCounts).length !== categoryKeys.length) {
    throw new Error("Unexpected category totals.");
  }

  const counts = Object.fromEntries(
    categoryKeys.map(key => [key, integer(rawCounts[key])]),
  ) as Record<CrimeCategory, number>;

  if (
    associated !== recordIds.length ||
    mapped + unmapped !== associated ||
    Object.values(counts).reduce((sum, count) => sum + count, 0) !== associated
  ) {
    throw new Error("Street record totals do not reconcile.");
  }

  if (
    requested.filters.category !== null &&
    categoryKeys.some(
      key => key !== requested.filters.category && counts[key] !== 0,
    )
  ) {
    throw new Error("Street totals include an unrequested category.");
  }

  const pointIds = new Set<number>();
  const mappedCounts = new Map<CrimeCategory, number>();

  const points: CrimeFeature[] = features(data.crimes).map(value => {
    const feature = object(value);
    const geometry = object(feature.geometry);
    const properties = object(feature.properties);
    const id = integer(feature.id);
    const crimeCategory = category(properties.category);

    if (
      feature.type !== "Feature" ||
      geometry.type !== "Point" ||
      properties.record_id !== id ||
      !recordSet.has(id) ||
      pointIds.has(id) ||
      typeof properties.location_precision !== "string" ||
      (
        requested.filters.category !== null &&
        crimeCategory !== requested.filters.category
      )
    ) {
      throw new Error("Invalid street crime feature.");
    }

    pointIds.add(id);
    mappedCounts.set(
      crimeCategory,
      (mappedCounts.get(crimeCategory) ?? 0) + 1,
    );

    return {
      type: "Feature",
      id,
      geometry: {
        type: "Point",
        coordinates: position(geometry.coordinates),
      },
      properties: {
        record_id: id,
        category: crimeCategory,
        location_precision: properties.location_precision,
      },
    };
  });

  if (
    points.length !== mapped ||
    categoryKeys.some(key => (mappedCounts.get(key) ?? 0) > counts[key])
  ) {
    throw new Error("Mapped record counts do not reconcile.");
  }

  const blockIds = new Set<number>();

  const blocks: StreetCrimeResult["road_blocks"]["features"] =
    features(data.road_blocks).map(value => {
      const feature = object(value);
      const geometry = object(feature.geometry);
      const properties = object(feature.properties);
      const id = integer(feature.id);

      if (
        feature.type !== "Feature" ||
        geometry.type !== "LineString" ||
        properties.objectid !== id ||
        blockIds.has(id) ||
        !Array.isArray(geometry.coordinates) ||
        geometry.coordinates.length < 2
      ) {
        throw new Error("Invalid street road geometry.");
      }

      const coordinates = geometry.coordinates.map(position);
      const [firstX, firstY] = coordinates[0];

      if (!coordinates.some(([x, y]) => x !== firstX || y !== firstY)) {
        throw new Error("Street road geometry has no usable length.");
      }

      blockIds.add(id);

      return {
        type: "Feature",
        id,
        geometry: { type: "LineString", coordinates },
        properties: {
          objectid: id,
          block_number:
            properties.block_number === null
              ? null
              : integer(properties.block_number),
        },
      };
    });

  if (blocks.length === 0) {
    throw new Error("No usable official road geometry is available.");
  }

  return {
    street: {
      street_id: returned.street_id,
      name: street.name,
    },
    filters: returned.filters,
    summary: {
      associated_record_count: associated,
      mapped_record_count: mapped,
      unmapped_record_count: unmapped,
      records_by_category: counts,
    },
    record_ids: recordIds,
    crimes: { type: "FeatureCollection", features: points },
    road_blocks: { type: "FeatureCollection", features: blocks },
  };
}

export async function fetchStreetCrimes(
  action: ShowStreetCrimesAction,
  signal: AbortSignal,
): Promise<StreetCrimeResult> {
  const requested = parseMapAction(action);

  const response = await fetch(apiUrl("/api/streets/crimes/query"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(requested),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Could not load street records (HTTP ${response.status}).`);
  }

  const value: unknown = await response.json();
  signal.throwIfAborted();

  return validateStreetCrimeResult(value, requested);
}