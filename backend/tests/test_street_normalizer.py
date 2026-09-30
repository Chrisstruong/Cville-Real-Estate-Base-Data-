from app.utils.street_normalizer import (
    normalize_street_name,
    extract_streets,
)


def test_normalize_street_name_edge_cases():
    cases = {
        "MACAA DR": "MACAA DR",
        "14TH STREET NW": "14TH ST NW",
        "macaa dr": "MACAA DR",
        "  MACAA   DR  ": "MACAA DR",
        "CASTALIA ST EXT": "CASTALIA ST EXT",
        "STONEHENGE AVENUE EXT": "STONEHENGE AVE EXT",
        "14TH ST NW": "14TH ST NW",
        "MAIN STREET": "MAIN ST",
        "123 1/2 MAIN ST": "123 1/2 MAIN ST",
        "MAIN ST @ 5TH ST": "MAIN ST @ 5TH ST",
        "": "",
        None: None,
        "TOTALLY FAKE STREET": "TOTALLY FAKE ST",
    }

    for input_value, expected in cases.items():
        assert normalize_street_name(input_value) == expected


def test_extract_streets_edge_cases():
    cases = {
        "MAIN ST @ 5TH ST": ["MAIN ST", "5TH ST"],
        "MAIN ST@5TH ST": ["MAIN ST", "5TH ST"],
        "BLENHEIM AVE / 6TH ST SE": [
            "BLENHEIM AVE",
            "6TH ST SE",
        ],
        "EMMET ST/BARRACKS RD": [
            "EMMET ST",
            "BARRACKS RD",
        ],
        "10TH ST/ MAIN ST": [
            "10TH ST",
            "MAIN ST",
        ],
        "JOHN/14TH ST NW": [
            "JOHN",
            "14TH ST NW",
        ],
        "10 1/2 ST NW": [
            "10 1/2 ST NW",
        ],
        "29/250": [
            "29/250",
        ],
    }

    for input_value, expected in cases.items():
        assert extract_streets(input_value) == expected
