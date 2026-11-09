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

OFFENSE_TO_CATEGORY = {
    offense.lower().strip(): category
    for category, offenses in CATEGORIES.items()
    for offense in offenses
}


def category_for_offense(offense: str | None) -> str:
    return OFFENSE_TO_CATEGORY.get(
        (offense or "").lower().strip(),
        "other",
    )
