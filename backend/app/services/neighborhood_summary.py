"""Database summaries using the map's existing mapped-point membership rules."""

import asyncio
from datetime import date

from fastapi import HTTPException
from psycopg import sql
from psycopg.rows import dict_row

from app.database.connection import pool
from app.services.neighborhoods import (
    DATASETS,
    MAX_CANDIDATES,
    load_neighborhoods,
    select_unique_members,
)

# Application-defined groups, not official police classifications.
# Preserve source spelling so each value matches the database.
CATEGORIES = {
    "theft": (
        "Larceny - All Other",
        "Larceny - From Coin Oper Device",
        "Larceny - From Motor Vehicle",
        "Larceny - Of Veh Parts/Access",
        "Larceny - Pocket Picking",
        "Larceny - Purse Snatching",
        "Larceny - Shoplifitng",
        "Larceny - Theft from Building",
    ),
    "motor_vehicle_theft": ("Motor Vehicle Theft",),
    "unauthorized_vehicle_use": ("Unauthorized Use of Motor Veh",),
    "burglary": ("Burglary",),
    "robbery": (
        "Robbery - Armed",
        "Robbery - Strong Arm",
    ),
    "assault": (
        "Assault Aggravated",
        "Assault Intimidation",
        "Assault Simple",
    ),
    "homicide": (
        "Homicide-murder/non-negligent",
        "Homicide-negligent manslaughter",
    ),
    "sex_related_offenses": (
        "Sex Offense",
        "Sex Offense-forcible fondling",
        "Sex Offense-statutory rape",
        "Sex Offense - Assault w/Object",
        "Sex Offense - Forcible Rape",
        "Sex Offense - Forcible Sodomy",
        "Pornography",
        "Prostitution",
        "Prowler - Peeping  Tom",
    ),
    "threats_harassment_stalking": (
        "Harassment",
        "Stalking",
        "Phone Calls - Annoying",
        "Phone Calls - Threat or Obscene",
        "Bomb Threat",
    ),
    "kidnapping_abduction": ("Kidnap/Abduction",),
    "fraud_financial_offenses": (
        "Fraud-credit card",
        "Fraud-false pretense",
        "Fraud-impersonation",
        "Fraud-welfare",
        "Fraud-wire fraud",
        "Forgery/Counterfeiting",
        "Embezzelment",
        "Extortion/Blackmail",
        "Computer Crime",
        "Impersonating a Police Officer",
    ),
    "vandalism": ("Vandalism",),
    "arson": ("Arson",),
    "other_property_offenses": (
        "Trespass",
        "Stolen Property Offenses",
    ),
    "drug_alcohol_records": (
        "Drug/Narcotics Violation",
        "Drug Equipment Violation",
        "Drug Investigation",
        "Narcotics",
        "Drunkeness DIP",
        "Liquor Law Violation",
    ),
    "weapons_shots_fired": (
        "Weapons Violations",
        "Shots Fired/Illegal Hunting",
    ),
    "traffic_vehicle_records": (
        "Hit and Run",
        "Driving Under the Influence",
        "Accident - w/out Injuries",
        "Accident Private Property",
        "Accident Property Damage",
        "Accident w/Injuries",
        "Traffic Stops",
        "Traffic - Abandoned Vehicle",
        "Traffic - Traffic Hazard",
        "Towed Vehicle",
    ),
    "disturbances_public_order": (
        "Disorderly Conduct",
        "Domestic Disturbance",
        "Disturbance - Non Domestic",
        "Noise Complaint",
        "Littering/Illegal Dumping",
        "Fireworks Violation",
    ),
    "family_juvenile_records": (
        "Family Offense - Non-Violent",
        "Child Ab - Contr to Delinquency",
        "Juvenile Investigation",
    ),
    "suspicious_activity": (
        "Suspicious Activity",
        "Suspicious Person",
        "Suspicious Vehicle",
    ),
    "mental_health_welfare": (
        "Assist Citizen - Mental/TDO/ECO",
        "Assist Citizen - Welfare Check",
        "Crisis Assessment",
        "Attemped Suicide",
        "Suicide Investigation",
    ),
    "missing_persons_runaway": (
        "Missing Person-adult",
        "Missing Person-juvenile",
        "Runaway",
    ),
    "assistance_investigations": (
        "Assist Citizen - Medical",
        "Assist Citizen - Misc",
        "Death Investigation - DOA",
        "911 Investigation",
        "Lost/FoundProperty",
    ),
    "animal_related": (
        "Animal Complaint",
        "Animal - Bite",
    ),
    "fire_alarm_records": (
        "Fires Not Arson",
        "Fire Code Violation",
        "Alarm - True",
        "Alarm-Accidental",
    ),
    "police_operations_community": (
        "Assist Agency - Arrest/warrant",
        "Assist Agency - Backup/Assist",
        "Assist Agency - Other",
        "Warrant Service",
        "Stop w/o Search/Frisk",
        "Comm Relations Initiative - CRI",
        "Crime Prevent Initiative - CPI",
        "Problem Solving Project - PSP",
        "Tactical Crime Initiative - TCI",
    ),
    "other_specified_records": (
        "Misc - Criminal Call",
        "Misc - Non-Criminal Call",
        "False Report of Crime",
    ),
    # Existing SQL sends missing and unrecognized values here.
    "other": (),
}

# Inclusive local calendar dates, with an exclusive next-day upper bound.
DATE_FILTER = """
    (%(date_start)s::date IS NULL OR date_reported >=
        (%(date_start)s::date::timestamp AT TIME ZONE 'America/New_York'))
    AND (%(date_end)s::date IS NULL OR date_reported <
        ((%(date_end)s::date + 1)::timestamp AT TIME ZONE 'America/New_York'))
"""

PROPERTY_SQL = """
WITH parcels AS (
    SELECT parcel_number,
        CASE WHEN current_assessed_value > 0 THEN current_assessed_value END AS value,
        CASE WHEN lot_sqft > 0 AND lot_sqft < 'Infinity'::float8
            THEN lot_sqft END AS lot
    FROM public.real_estate_current_assessment
    WHERE parcel_number = ANY(%(ids)s::text[])
)
SELECT count(DISTINCT parcel_number) AS property_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY value) AS median_assessed_value,
    sum(value) AS total_assessed_value,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY lot) AS median_lot_sqft,
    count(value) AS assessed_value_valid_count,
    count(*) - count(value) AS assessed_value_excluded_count,
    count(lot) AS lot_sqft_valid_count,
    count(*) - count(lot) AS lot_sqft_excluded_count
FROM parcels
"""

CRIME_SQL = (
    """
WITH category_map AS (
    SELECT * FROM unnest(%(offenses)s::text[], %(categories)s::text[])
        AS mapping(offense, category)
), normalized AS (
    SELECT record_id, lower(btrim(offense)) AS offense
    FROM public.crime
    WHERE record_id = ANY(%(ids)s::integer[]) AND
"""
    + DATE_FILTER
    + """
), classified AS (
    SELECT n.record_id, coalesce(m.category, 'other') AS category,
        n.offense IS NULL OR n.offense = '' AS missing
    FROM normalized n LEFT JOIN category_map m ON n.offense = m.offense
)
SELECT category, count(*) AS count,
    count(*) FILTER (WHERE missing) AS missing_count,
    sum(count(*)) OVER () AS total_count
FROM classified GROUP BY category
"""
)


async def summarize_connection(conn, neighborhood_id, date_start=None, date_end=None):
    """Caller supplies a repeatable-read transaction for a consistent snapshot.

    Current assessment parcel_number and crime record_id are primary keys.
    No real_estate join is needed: all requested metrics live in assessment.
    """
    if (date_start is None) != (date_end is None):
        raise ValueError("Supply both date_start and date_end, or neither.")
    if date_start is not None:
        if type(date_start) is not date or type(date_end) is not date:
            raise ValueError("Date bounds must be calendar dates.")
        if date_start > date_end or date_end == date.max:
            raise ValueError("Invalid reporting-date range.")

    neighborhoods = load_neighborhoods()
    if neighborhood_id not in neighborhoods:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")
    west, south, east, north = neighborhoods[neighborhood_id].bounds
    params = dict(
        west=west,
        east=east,
        south=south,
        north=north,
        date_start=date_start,
        date_end=date_end,
        limit=MAX_CANDIDATES + 1,
    )
    ids = {}
    ambiguous = {}
    async with conn.cursor(row_factory=dict_row) as cur:
        for dataset in ("properties", "crimes"):
            table, key, _ = DATASETS[dataset]
            query = sql.SQL("""
                SELECT {key}, longitude, latitude FROM {table}
                WHERE longitude BETWEEN %(west)s AND %(east)s
                    AND latitude BETWEEN %(south)s AND %(north)s
                    {dates}
                ORDER BY {key} LIMIT %(limit)s
            """).format(
                key=sql.Identifier(key),
                table=sql.Identifier("public", table),
                dates=sql.SQL("AND " + DATE_FILTER if dataset == "crimes" else ""),
            )
            await cur.execute(query, params)
            rows = await cur.fetchall()
            if len(rows) > MAX_CANDIDATES:
                raise HTTPException(
                    status_code=422, detail="Too many summary candidates."
                )
            accepted, ambiguous[dataset] = await asyncio.to_thread(
                select_unique_members,
                rows,
                neighborhood_id,
                neighborhoods,
            )
            ids[dataset] = sorted({row[key] for row in accepted})

        await cur.execute(PROPERTY_SQL, {"ids": ids["properties"]})
        result = dict(await cur.fetchone())
        # PostgreSQL SUM(bigint) returns Decimal; preserve an exact integer total.
        if result["total_assessed_value"] is not None:
            result["total_assessed_value"] = int(result["total_assessed_value"])
        mapping = [
            (offense.lower().strip(), category)
            for category, offenses in CATEGORIES.items()
            for offense in offenses
        ]
        await cur.execute(
            CRIME_SQL,
            {
                **params,
                "ids": ids["crimes"],
                "offenses": [entry[0] for entry in mapping],
                "categories": [entry[1] for entry in mapping],
            },
        )
        groups = await cur.fetchall()

    counts = dict.fromkeys(CATEGORIES, 0)
    for group in groups:
        counts[group["category"]] = group["count"]
    total = int(groups[0]["total_count"]) if groups else 0
    if sum(counts.values()) != total or total != len(ids["crimes"]):
        raise RuntimeError("Crime summary counts do not reconcile.")
    return {
        **result,
        "neighborhood_id": neighborhood_id,
        "date_start": date_start,
        "date_end": date_end,
        "crime_count": total,
        "crime_by_category": counts,
        "missing_crime_category_count": sum(g["missing_count"] for g in groups),
        "ambiguous_property_count": ambiguous["properties"],
        "ambiguous_crime_count": ambiguous["crimes"],
        "membership_basis": "mapped_point",
        "category_mapping_version": "1",
    }


async def fetch_neighborhood_summary(neighborhood_id, date_start=None, date_end=None):
    """Public service entry point; no route or existing map behavior is changed."""
    async with pool.connection() as conn:
        async with conn.transaction():
            await conn.execute(
                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
            )
            return await summarize_connection(
                conn, neighborhood_id, date_start, date_end
            )
