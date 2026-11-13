import {
  CRIME_CATEGORIES,
  type CrimeCategory,
} from "../config/crimeCategories";

export type CrimeFilters = {
  start_date: string | null;
  end_date: string | null;
  category: CrimeCategory | null;
};

export type ShowStreetCrimesAction = {
  type: "SHOW_STREET_CRIMES";
  street_id: string;
  filters: CrimeFilters;
};

export type MapAction = ShowStreetCrimesAction;

function requireObject(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("Expected an object.");
  }

  return value as Record<string, unknown>;
}

function requireKeys(
  value: Record<string, unknown>,
  expected: readonly string[],
): void {
  const actual = Object.keys(value);

  if (
    actual.length !== expected.length ||
    expected.some(key => !Object.prototype.hasOwnProperty.call(value, key))
  ) {
    throw new Error("Unexpected or missing action fields.");
  }
}

function parseDate(value: unknown): string | null {
  if (value === null) return null;

  if (
    typeof value !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(value) ||
    value < "0001-01-01"
  ) {
    throw new Error("Dates must use YYYY-MM-DD.");
  }

  const parsed = new Date(`${value}T00:00:00Z`);

  if (
    !Number.isFinite(parsed.getTime()) ||
    parsed.toISOString().slice(0, 10) !== value
  ) {
    throw new Error("Invalid calendar date.");
  }

  return value;
}

export function parseMapAction(value: unknown): MapAction {
  const action = requireObject(value);
  requireKeys(action, ["type", "street_id", "filters"]);

  if (action.type !== "SHOW_STREET_CRIMES") {
    throw new Error("Unsupported map action.");
  }

  if (
    typeof action.street_id !== "string" ||
    action.street_id.length === 0 ||
    action.street_id.length > 200 ||
    action.street_id !== action.street_id.trim()
  ) {
    throw new Error("Invalid street identifier.");
  }

  const rawFilters = requireObject(action.filters);
  requireKeys(rawFilters, ["start_date", "end_date", "category"]);

  const start = parseDate(rawFilters.start_date);
  const end = parseDate(rawFilters.end_date);

  if ((start === null) !== (end === null)) {
    throw new Error("Provide both dates or neither.");
  }

  if (start !== null && end !== null) {
    if (start > end) {
      throw new Error("Start date must not follow end date.");
    }

    if (end === "9999-12-31") {
      throw new Error("End date must be earlier than 9999-12-31.");
    }
  }

  const category = rawFilters.category;

  if (
    category !== null &&
    (
      typeof category !== "string" ||
      !Object.prototype.hasOwnProperty.call(CRIME_CATEGORIES, category)
    )
  ) {
    throw new Error("Unsupported crime category.");
  }

  return {
    type: "SHOW_STREET_CRIMES",
    street_id: action.street_id,
    filters: {
      start_date: start,
      end_date: end,
      category: category as CrimeCategory | null,
    },
  };
}