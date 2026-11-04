import { apiUrl } from "./baseUrl";

export type NeighborhoodOverview = {
    neighborhood: {
        neighborhood_id: number;
        name: string;
        area_acres: number | null;
    };

    properties: {
        property_count: number;
        median_assessed_value: number | null;
        total_assessed_value: number | null;
        median_lot_sqft: number | null;
        median_year_built: number | null;
        assessed_value_valid_count: number;
        assessed_value_excluded_count: number;
        lot_sqft_valid_count: number;
        lot_sqft_excluded_count: number;
    };

    crimes: {
        crime_count: number;
        crime_by_category: Record<string, number>;
        crime_start_date: string | null;
        crime_end_date: string | null;
        missing_crime_category_count: number;
    };
    metadata: {
        membership_basis: "mapped_point";
        category_mapping_version: string;
        ambiguous_property_count: number;
        ambiguous_crime_count: number;
        notes: string[];
    };
}

const CACHE_TTL_MS = 30_000;
const overviewCache = new Map<
    number,
    {
        data: NeighborhoodOverview; 
        expiresAt: number;
    }
>();

export async function fetchNeighborhoodOverview(
    neighborhoodId: number,
    signal: AbortSignal,
): Promise<NeighborhoodOverview> {
    signal.throwIfAborted();

    const cached = overviewCache.get(neighborhoodId);

    if (cached && cached.expiresAt > Date.now()) {
        return cached.data;
    }

    overviewCache.delete(neighborhoodId);
    const response = await fetch(apiUrl(`/api/neighborhoods/${neighborhoodId}/overview`), { signal });

    if (!response.ok) {
        throw new Error(`Could not load neighborhood overview (HTTP ${response.status}).`);
    }

    const data: NeighborhoodOverview = await response.json();

    if (
        data?.neighborhood?.neighborhood_id !== neighborhoodId ||
        !data.properties ||
        !data.crimes ||
        !data.crimes.crime_by_category ||
        !data.metadata
    ) {
        throw new Error("The overview response was incomplete.");
    }
    
    signal.throwIfAborted();

    overviewCache.set(neighborhoodId, {
        data, 
        expiresAt: Date.now() + CACHE_TTL_MS,
    })
    return data;

}