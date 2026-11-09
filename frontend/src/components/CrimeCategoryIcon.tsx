import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import {
    CRIME_CATEGORIES,
    normalizeCrimeCategory,
} from "../config/crimeCategories";

type Props = {
    category?: string | null;
    count?: number;
};

export default function CrimeCategoryIcon({
    category,
    count = 1,
}: Props) {
    const config = CRIME_CATEGORIES[normalizeCrimeCategory(category)];
    const multiple = count > 1;
    const label = multiple ? `${count} records at this mapped location` :config.label;

    return (
        <span
        role="img"
        aria-label={label}
        title={label}
        style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 36,
            height: 36,
            flexShrink: 0,
            borderRadius: 8,
            backgroundColor: multiple ? "#334155" : config.background,
            color: "#FFFFFF",
            fontSize: count > 999 ? 11 : 14,
            fontWeight: 700,
            lineHeight: 1,
        }}
        >
            {multiple ? (
                count
            ): (
                <FontAwesomeIcon
                icon={config.icon}
                aria-hidden="true"
                style={{width:20, height:20}}
            />
            )}

        </span>
    )
}