REVOKE UPDATE (
    latitude,
    longitude,
    mapping_method,
    location_precision,
    gis_source_ids,
    unmapped_reason,
    geolocation_version,
    geolocation_checked_at
)
ON TABLE public.crime
FROM ai_reader;