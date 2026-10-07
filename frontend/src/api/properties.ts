export type MapProperty = {
    parcel_number: string;
    current_assessed_value: number;
    st_number: string | null;
    st_name: string;
    st_unit: string | null;
    lot_sqft: number;
    latitude: number;
    longitude: number;
}

export type PropertyDetails = {
    parcel_number: string;
    current_assessed_value: number;
    object_id: string;
    st_number: string | null;
    st_name: string;
    st_unit: string | null;
    legal_description: string | null;
    lot_sqft: number;
    latitude: number | null;
    longitude: number | null;
}


type MapPropertiesResponse = {
    count: number;
    properties: MapProperty[];
};

export async function fetchMapProperties(
    limit = 10
): Promise<MapPropertiesResponse> {
    const response = await fetch(`http://127.0.0.1:8000/api/properties/map?limit=${limit}`);
    
    if (!response.ok) {
        throw new Error('Failed to fetch map properties: ${response.data}');
    }

    return response.json();
}


export async function fetchAllMapProperties(): Promise<MapPropertiesResponse> {
    const response = await fetch ("http://127.0.0.1:8000/api/properties/map/all");

    if (!response.ok) {
        throw new Error(`Failed to fetch all map properties: ${response.status}`);
    }

    return response.json();
}

export async function fetchPropertyByParcelNumber(parcel_number: string): Promise<PropertyDetails> {
    const response = await fetch(`http://127.0.0.1:8000/api/properties/${encodeURIComponent(parcel_number)}`);

    if (!response.ok) {
        throw new Error(`Failed to fetch property: ${response.status}`)
    }
    return response.json();
}