import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faBagShopping,
  faCar,
  faKey,
  faMask,
  faMoneyBillWave,
  faHandFist,
  faSkull,
  faShieldHalved,
  faCommentDots,
  faPersonCircleExclamation,
  faCreditCard,
  faSprayCan,
  faFire,
  faHouse,
  faPills,
  faCrosshairs,
  faTrafficLight,
  faTriangleExclamation,
  faPeopleGroup,
  faEye,
  faHeart,
  faPersonCircleQuestion,
  faMagnifyingGlass,
  faPaw,
  faBell,
  faClipboard,
  faQuestion,
} from "@fortawesome/free-solid-svg-icons";

type CategoryStyle = {
  label: string;
  icon: IconDefinition;
  background: string;
};

export const CRIME_CATEGORIES = {
  theft: {
    label: "Theft",
    icon: faBagShopping,
    background: "#A16207",
  },
  motor_vehicle_theft: {
    label: "Motor vehicle theft",
    icon: faCar,
    background: "#B45309",
  },
  unauthorized_vehicle_use: {
    label: "Unauthorized vehicle use",
    icon: faKey,
    background: "#9A3412",
  },
  burglary: {
    label: "Burglary",
    icon: faMask,
    background: "#7C3AED",
  },
  robbery: {
    label: "Robbery",
    icon: faMoneyBillWave,
    background: "#9333EA",
  },
  assault: {
    label: "Assault",
    icon: faHandFist,
    background: "#BE123C",
  },
  homicide: {
    label: "Homicide",
    icon: faSkull,
    background: "#881337",
  },
  sex_related_offenses: {
    label: "Sex-related offenses",
    icon: faShieldHalved,
    background: "#86198F",
  },
  threats_harassment_stalking: {
    label: "Threats, harassment and stalking",
    icon: faCommentDots,
    background: "#A21CAF",
  },
  kidnapping_abduction: {
    label: "Kidnapping / abduction",
    icon: faPersonCircleExclamation,
    background: "#9F1239",
  },
  fraud_financial_offenses: {
    label: "Fraud / financial offenses",
    icon: faCreditCard,
    background: "#047857",
  },
  vandalism: {
    label: "Vandalism",
    icon: faSprayCan,
    background: "#C2410C",
  },
  arson: {
    label: "Arson",
    icon: faFire,
    background: "#B91C1C",
  },
  other_property_offenses: {
    label: "Other property offenses",
    icon: faHouse,
    background: "#92400E",
  },
  drug_alcohol_records: {
    label: "Drug / alcohol records",
    icon: faPills,
    background: "#6D28D9",
  },
  weapons_shots_fired: {
    label: "Weapons / shots fired",
    icon: faCrosshairs,
    background: "#991B1B",
  },
  traffic_vehicle_records: {
    label: "Traffic / vehicle records",
    icon: faTrafficLight,
    background: "#0369A1",
  },
  disturbances_public_order: {
    label: "Disturbances / public order",
    icon: faTriangleExclamation,
    background: "#A16207",
  },
  family_juvenile_records: {
    label: "Family / juvenile records",
    icon: faPeopleGroup,
    background: "#4338CA",
  },
  suspicious_activity: {
    label: "Suspicious activity",
    icon: faEye,
    background: "#475569",
  },
  mental_health_welfare: {
    label: "Mental health / welfare",
    icon: faHeart,
    background: "#0F766E",
  },
  missing_persons_runaway: {
    label: "Missing persons / runaway",
    icon: faPersonCircleQuestion,
    background: "#1D4ED8",
  },
  assistance_investigations: {
    label: "Assistance / investigations",
    icon: faMagnifyingGlass,
    background: "#0369A1",
  },
  animal_related: {
    label: "Animal-related",
    icon: faPaw,
    background: "#4D7C0F",
  },
  fire_alarm_records: {
    label: "Fire / alarm records",
    icon: faBell,
    background: "#C2410C",
  },
  police_operations_community: {
    label: "Police operations / community",
    icon: faShieldHalved,
    background: "#1E40AF",
  },
  other_specified_records: {
    label: "Other specified records",
    icon: faClipboard,
    background: "#475569",
  },
  other: {
    label: "Other / unclassified",
    icon: faQuestion,
    background: "#64748B",
  },
} satisfies Record<string, CategoryStyle>;

export type CrimeCategory = keyof typeof CRIME_CATEGORIES;

export function normalizeCrimeCategory(
  value: string | null | undefined,
): CrimeCategory {
  return value && Object.prototype.hasOwnProperty.call(CRIME_CATEGORIES, value)
    ? (value as CrimeCategory)
    : "other";
}