def normalize_street_name(street_name: str | None) -> str | None:
    """
    Normalize a street name for comparison between datasets.

    Intentionally simple baseline normalizer.
    More advanced normalization will be added after measuring this version.
    """

    if street_name is None:
        return None

    # Normalize capitalization and surrounding whitespace
    normalized = street_name.strip().upper()

    # Collapse repeated whitespace
    normalized = " ".join(normalized.split())

    # Crime data someitmes stores unit/sub-location information
    # after a comma, e.g "APPLE TREE RD, A".
    if "," in normalized:
        normalized = normalized.split(",", 1)[0].strip()

    return normalized
