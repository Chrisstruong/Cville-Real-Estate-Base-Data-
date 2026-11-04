import { useEffect, useState } from "react";
import {
    fetchNeighborhoodOverview,
    type NeighborhoodOverview,
} from "../api/neighborhoodOverview";
import "./NeighborhoodOverviewPanel.css";

type Props = {
    neighborhoodId: number;
    neighborhoodName: string;
    onClose: () => void;
};

type LoadState =
    | { status: "loading" }
    | { status: "success"; data: NeighborhoodOverview }
    | { status: "error"; message: string };

const integer = new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
});

const currency = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
});

function formatNumber(value: number | null, suffix = "") {
    return value === null
        ? "Not available"
        : `${integer.format(value)}${suffix}`;
}

function formatMoney(value: number | null) {
    return value === null ? "Not available" : currency.format(value);
}

function categoryLabel(key: string) {
    if (key === "other") return "Other / unclassified";

    return key
        .split("_")
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

// The keyed inner component resets its request and state on selection changes.
export default function NeighborhoodOverviewPanel(props: Props) {
    return <OverviewContent key={props.neighborhoodId} {...props} />;
}

function OverviewContent({
    neighborhoodId,
    neighborhoodName,
    onClose,
}: Props) {
    const [state, setState] = useState<LoadState>({ status: "loading" });
    const [attempt, setAttempt] = useState(0);

    useEffect(() => {
        const controller = new AbortController();

        fetchNeighborhoodOverview(neighborhoodId, controller.signal)
            .then(data => {
                if (!controller.signal.aborted) {
                    setState({ status: "success", data });
                }
            })
            .catch((error: unknown) => {
                if (!controller.signal.aborted) {
                    setState({
                        status: "error",
                        message:
                            error instanceof Error
                                ? error.message
                                : "Could not load neighborhood overview.",
                    });
                }
            });

        return () => controller.abort();
    }, [neighborhoodId, attempt]);

    const data = state.status === "success" ? state.data : null;
    const categories = data
        ? Object.entries(data.crimes.crime_by_category).sort(
            ([a, countA], [b, countB]) =>
                countB - countA || a.localeCompare(b),
        )
        : [];

    return (
        <aside
            className="overview-panel"
            aria-labelledby="overview-title"
            aria-busy={state.status === "loading"}
        >
            <header className="overview-header">
                <div>
                    <p className="overview-eyebrow">Neighborhood overview</p>
                    <h2 id="overview-title">{neighborhoodName}</h2>
                </div>

                <button
                    type="button"
                    className="overview-close"
                    onClick={onClose}
                    aria-label="Close neighborhood overview"
                >
                    ×
                </button>
            </header>

            <div className="overview-body">
                {state.status === "loading" && (
                    <p role="status">Loading neighborhood overview…</p>
                )}

                {state.status === "error" && (
                    <div role="alert">
                        <p>{state.message}</p>
                        <button
                            type="button"
                            onClick={() => {
                                setState({ status: "loading" });
                                setAttempt(value => value + 1);
                            }}
                        >
                            Try again
                        </button>
                    </div>
                )}

                {data && (
                    <>
                        <div className="overview-cards">
                            <div className="overview-card">
                                <span>Properties</span>
                                <strong>
                                    {integer.format(data.properties.property_count)}
                                </strong>
                            </div>

                            <div className="overview-card">
                                <span>Crime Records</span>
                                <strong>{integer.format(data.crimes.crime_count)}</strong>
                            </div>

                            <div className="overview-card">
                                <span>Area</span>
                                <strong>
                                    {data.neighborhood.area_acres === null
                                        ? "Not available"
                                        : `${data.neighborhood.area_acres.toLocaleString(
                                            "en-US",
                                            { maximumFractionDigits: 2 },
                                        )} acres`}
                                </strong>
                            </div>
                        </div>

                        <p className="overview-note">
                            {data.crimes.crime_start_date && data.crimes.crime_end_date
                                ? `Reporting dates: ${data.crimes.crime_start_date} through ${data.crimes.crime_end_date}.`
                                : "All available reporting dates."}
                            {" "}
                            Categories include reported offenses, service calls, and police activity.
                        </p>

                        <section className="overview-section">
                            <h3>Crime Summary</h3>
                            <p className="overview-note">
                                Crime totals include approximate mapped locations, not only precise
                                incident locations. Records without usable coordinates are excluded.
                            </p>

                            {data.crimes.crime_count === 0 ? (
                                <p>No mapped crime records for this neighborhood.</p>
                            ) : (
                                <ul className="overview-categories">
                                    {categories.map(([category, count]) => (
                                        <li key={category}>
                                            <div className="overview-category-label">
                                                <span>{categoryLabel(category)}</span>
                                                <strong>{integer.format(count)}</strong>
                                            </div>
                                            <div className="overview-bar" aria-hidden="true">
                                                <span
                                                    style={{
                                                        width: `${(count / data.crimes.crime_count) * 100
                                                            }%`,
                                                    }}
                                                />
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>

                        <section className="overview-section">
                            <h3>Property Overview</h3>

                            {data.properties.property_count === 0 && (
                                <p>No mapped properties for this neighborhood.</p>
                            )}

                            <dl className="overview-metrics">
                                <div>
                                    <dt>Median assessed value</dt>
                                    <dd>
                                        {formatMoney(data.properties.median_assessed_value)}
                                    </dd>
                                </div>
                                <div>
                                    <dt>Median lot size</dt>
                                    <dd>
                                        {formatNumber(data.properties.median_lot_sqft, " sq ft")}
                                    </dd>
                                </div>
                                <div>
                                    <dt>Median year built</dt>
                                    <dd>{formatNumber(data.properties.median_year_built)}</dd>
                                </div>
                                <div>
                                    <dt>Total assessed value — valid records</dt>
                                    <dd>
                                        {formatMoney(data.properties.total_assessed_value)}
                                    </dd>
                                </div>
                            </dl>

                            <p className="overview-note">
                                Assessment values available for{" "}
                                {integer.format(data.properties.assessed_value_valid_count)}
                                {" of "}
                                {integer.format(data.properties.property_count)} parcels.
                                Valid lot sizes available for{" "}
                                {integer.format(data.properties.lot_sqft_valid_count)}.
                                Reliable year-built data is not yet available.
                            </p>
                        </section>

                        <p className="overview-note">
                            Ambiguous assignments excluded:{" "}
                            {integer.format(data.metadata.ambiguous_property_count)}
                            {" properties and "}
                            {integer.format(data.metadata.ambiguous_crime_count)}
                            {" crime records."}
                        </p>
                    </>
                )}
            </div>
        </aside>
    );
}
