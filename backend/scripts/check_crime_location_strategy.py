from app.services.crime_location_strategy import choose_location_strategy


def main():
    # A small demonstration reference set, not a database query.
    official_streets = {
        "GROVE ST",
        "EMMET ST",
        "BARRACKS RD",
    }

    cases = [
        ("GROVE ST", 1000),
        ("GROVE ST", None),
        ("EMMET ST / BARRACKS RD", None),
        ("EMMET ST / UNRECOGNIZED RD", None),
        ("UNKNOWN", 100),
    ]

    for street_name, block_number in cases:
        decision = choose_location_strategy(
            street_name,
            block_number,
            official_streets,
        )

        print(
            f"{street_name!r}, block={block_number!r}"
            f" -> {decision.next_step}"
            f" | reason={decision.reason}"
            f" | streets={decision.streets}"
        )


if __name__ == "__main__":
    main()
