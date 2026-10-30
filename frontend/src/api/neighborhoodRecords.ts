import type {FeatureCollection, Point} from "geojson";
import { apiUrl } from "./baseUrl";
import type { CrimeFeatureCollection } from "./crimes";


type NeighborhoodMetaData = {
    neighborhood_id: number;
    count: number
    ambiguous_excluded: number;
    membership_basis: "mapped_point";
};

export type NeighborhoodProperties = FeatureCollection <
    Point,
    {
        parcel_number: string,
        neighborhood_id: number,
        membership_basis: "mapped_point",
    }
> & {
    metadata: NeighborhoodMetaData;
};

export type NeighborhoodCrimes = CrimeFeatureCollection & {
    metadata: NeighborhoodMetaData;
}

async function fetchRecords (
    neighborhoodId: number,
    dataset: "properties" | "crimes",
    signal: AbortSignal,
): Promise<unknown> {
    const response = await fetch(
        apiUrl(`/api/neighborhoods/${neighborhoodId}/${dataset}`),
        {signal},
    );
    
    if (!response.ok) {
        throw new Error(
            `Could not load neighborhood${dataset}: HTTP ${response.status}`
        );
    }

    const data = await response.json()

    if(
        data?.type !== "FeatureCollection" ||
        !Array.isArray(data.features) ||
        data.metadata?.neighborhood_id !== neighborhoodId ||
        data.metadata?.count !== data.features.length
    ) {
        throw new Error(`Unexpected neighborhood ${dataset} responses.`)
    }
    return data
}

export async function fetchNeighborhoodProperties(
    neighborhoodId: number,
    signal: AbortSignal,
): Promise<NeighborhoodProperties> {
    return await fetchRecords(
        neighborhoodId,
        "properties",
        signal,
    ) as NeighborhoodProperties;
}

export async function fetchNeighborhoodCrimes(neighborhoodId: number, signal: AbortSignal,):
    Promise<NeighborhoodCrimes> {
        return await fetchRecords(
            neighborhoodId,
            "crimes",
            signal
        ) as NeighborhoodCrimes
}




