import { apiUrl } from "./baseUrl";

export type CrimeFeature = {
  type: "Feature";
  id: number;
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: {
    record_id: number;
    location_precision: string;
  };
};

export type CrimeFeatureCollection = {
  type: "FeatureCollection";
  features: CrimeFeature[];
};

export async function fetchMapCrimes(
  signal?: AbortSignal,
): Promise<CrimeFeatureCollection> {
  const response = await fetch(
    apiUrl("/api/crimes/map"),
    { signal },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch crime locations: HTTP ${response.status}`,
    );
  }

  const data: CrimeFeatureCollection = await response.json();

  if (
    data.type !== "FeatureCollection" ||
    !Array.isArray(data.features)
  ) {
    throw new Error("Unexpected crime map response.");
  }

  return data;
}


export type CrimeDetails = {
  record_id: number;
  offense: string | null;
  date_reported: string | null;
  block_number: number | null;
  street_name: string | null;
  latitude: number | null;
  longitude: number | null;
  mapping_method: string | null;
  location_precision: string | null;
};

export async function fetchCrimeDetails(
  recordId: number,
  signal?: AbortSignal,
): Promise<CrimeDetails> {
  const response = await fetch(
    apiUrl(`/api/crimes/${recordId}`),
    { signal },
  );

  if (response.status === 404) {
    throw new Error("This crime record could not be found.");
  }

  if (!response.ok) {
    throw new Error(
      `Failed to fetch crime details: HTTP ${response.status}`,
    );
  }

  return response.json();
}
