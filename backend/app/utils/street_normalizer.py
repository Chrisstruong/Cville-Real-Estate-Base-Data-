import re

STREET_SUFFIXES = {
    "STREET": "ST",
    "ROAD": "RD",
    "AVENUE": "AVE",
    "LANE": "LN",
    "COURT": "CT",
    "TR": "TRL",
    "PLACE": "PL",
}

STREET_ALIASES = {
    "CASTALIA EXT ST": "CASTALIA ST EXT",
    "MALCOLM CRESENT": "MALCOLM CRES",
}


def normalize_street_name(street_name: str | None) -> str | None:
    """
    Normalize a street name for comparison between datasets.

    Intentionally simple baseline normalizer.
    More advanced normalization will be added after measuring this version.
    """

    if street_name is None:
        return None

    # Normalize capitalization and surrounding whitespace
    # " 123 main street "" -> "123 MAIN STREET"
    normalized = street_name.strip().upper()

    # Remove apostrophe
    normalized = normalized.replace("'", "")

    # Remove periods used in street abbreviations
    # "AVON ST." -> "AVON ST"
    # "E. MARKET ST." -> "E MARKET ST"
    normalized = re.sub(r"(?<=[A-Z])\.", "", normalized)

    # Connect back together exactly 1 space
    normalized = " ".join(normalized.split())

    # Remove crime-data "(CONS)" prefix
    if normalized.startswith("(CONS) "):
        normalized = normalized[len("(CONS) ") :].strip()

    # Crime data someitmes stores unit/sub-location information
    # after a comma, e.g "APPLE TREE RD, A".
    # "APPLE TREE RD, A" -> ['APPLE TREE RD', 'A'] -> "APPLE TREE RD"
    if "," in normalized:
        normalized = normalized.split(",", 1)[0].strip()

    words = normalized.split()

    words = [STREET_SUFFIXES.get(word, word) for word in words]

    # Remove accidental consecutive duplicate words.
    # Example:
    # "BOILING AVE AVE" -> "BOILING AVE"
    # "CARLTON RD RD" -> "CARLTON RD"
    deduplicated_words = []

    for word in words:
        if not deduplicated_words or word != deduplicated_words[-1]:
            deduplicated_words.append(word)

    normalized = " ".join(deduplicated_words)

    normalized = STREET_ALIASES.get(normalized, normalized)

    return normalized


def extract_streets(location: str | None) -> list[str]:
    if location is None:
        return []

    location = location.strip().upper()

    # Split "/" only when it represents an intersection.
    # At least one side of the slash must touch a letter.
    #
    # Splits:
    # "BLENHEIM AVE / 6TH ST SE"
    # "EMMET ST/BARRACKS RD"
    # "10TH ST/ MAIN ST"
    # "JOHN/14TH ST NW"
    #
    # Does NOT split:
    # "10 1/2 ST NW"
    # "29/250"
    slash_pattern = r"(?<=[A-Z])\s*/\s*|\s*/\s*(?=[A-Z])"

    if re.search(slash_pattern, location):
        parts = re.split(slash_pattern, location)

    elif " @ " in location:
        parts = location.split(" @ ")

    elif re.search(r"(?<=[A-Z])@(?=[A-Z0-9])", location):
        parts = re.split(
            r"(?<=[A-Z])@(?=[A-Z0-9])",
            location,
        )

    else:
        parts = [location]

    return [normalize_street_name(part) for part in parts if part.strip()]
