import { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faChevronDown, faChevronUp, faArrowLeft, faXmark } from "@fortawesome/free-solid-svg-icons";
import { fetchCrimeDetails, type CrimeDetails } from "../api/crimes";
import CrimeCategoryIcon from "./CrimeCategoryIcon";
import "./CrimeLocationPanel.css";

type Props = {
  recordIds: number[];
  categories: Record<number, string>;
  neighborhoodName: string;
  onBack: () => void;
  onClose: () => void;
};
const PAGE_SIZE = 10;

function display(value: string | number | null | undefined) {
  return value === null || value === undefined || value === "" ? "Not available" : String(value);
}

function reportedDate(value: string | null) {
  if (!value) return "Reported date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return `Invalid timestamp: ${value}`;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York", year: "numeric", month: "short", day: "numeric",
    hour: "numeric", minute: "2-digit", timeZoneName: "short",
  }).format(date);
}

function TechnicalValue({ value }: { value: string | null }) {
  if (!value) return <>Not available</>;
  const label = value.replaceAll("_", " ");
  return <>{label.charAt(0).toUpperCase() + label.slice(1)}<small>Source: {value}</small></>;
}

function RecordCard({ record, category, selected, onSelect }: {
  record: CrimeDetails; category?: string; selected: boolean; onSelect: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const detailsId = `crime-details-${record.record_id}`;
  const address = [record.block_number == null ? null : `${record.block_number} block`, record.street_name].filter(Boolean).join(" of ") || "Address unavailable";
  return (
    <article className={`incident-card${selected ? " is-selected" : ""}`} onFocus={onSelect} onClick={onSelect} aria-label={`Record ${record.record_id}${selected ? ", selected" : ""}`}>
      <div className="incident-heading">
        <CrimeCategoryIcon category={category} />
        <div><h3>{record.offense || "Offense unavailable"}</h3><p className="incident-secondary">Record {record.record_id}{selected && <span> (Selected)</span>}</p></div>
      </div>
      <p className="incident-address" title="Approximate reported address">{address}</p>
      <p className="incident-secondary">{reportedDate(record.date_reported)}</p>
      <button className="incident-toggle" type="button" aria-expanded={expanded} aria-controls={detailsId} onClick={() => setExpanded(value => !value)}>
        {expanded ? "Hide details" : "View details"}
        <FontAwesomeIcon icon={expanded ? faChevronUp : faChevronDown} aria-hidden="true" />
      </button>
      <div id={detailsId} className="incident-details" hidden={!expanded}>
        <h4>Incident Information</h4>
        <dl>
          <div><dt>Incident ID</dt><dd>{display(record.incident_id)}</dd></div>
          <div><dt>Agency</dt><dd>{display(record.agency)}</dd></div>
          <div><dt>Reporting officer</dt><dd>{display(record.reporting_officer)}</dd></div>
          <div><dt>Reported timestamp</dt><dd>{reportedDate(record.date_reported)}<small>Source: {display(record.date_reported)}</small></dd></div>
          <div><dt>Hour reported</dt><dd>{display(record.hour_reported)}<small>Separate source field</small></dd></div>
        </dl>
        <h4>Location Information</h4>
        <dl>
          <div><dt>Block number</dt><dd>{display(record.block_number)}</dd></div>
          <div><dt>Street name</dt><dd>{display(record.street_name)}</dd></div>
          <div><dt>Latitude</dt><dd>{display(record.latitude)}</dd></div>
          <div><dt>Longitude</dt><dd>{display(record.longitude)}</dd></div>
          <div><dt>Mapping method</dt><dd><TechnicalValue value={record.mapping_method} /></dd></div>
          <div><dt>Location precision</dt><dd><TechnicalValue value={record.location_precision} /></dd></div>
        </dl>
      </div>
    </article>
  );
}

function RecordPage({
  recordIds,
  page,
  onRetry,
  categories,
  selectedRecord,
  onSelect,
}: {
  recordIds: number[];
  page: number;
  onRetry: () => void;
  categories: Record<number, string>;
  selectedRecord: number | null;
  onSelect: (id: number) => void;
}) {
  const [records, setRecords] = useState<CrimeDetails[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const ids = recordIds.slice(
      page * PAGE_SIZE,
      (page + 1) * PAGE_SIZE,
    );

    void Promise.all(
      ids.map(id => fetchCrimeDetails(id, controller.signal)),
    )
      .then(results => {
        if (!controller.signal.aborted) {
          setRecords(results);
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not load records.",
          );
        }
      });

    return () => controller.abort();
  }, [recordIds, page]);

  if (error) {
    return (
      <div role="alert">
        <p>{error}</p>
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      </div>
    );
  }

  if (records === null) {
    return <p role="status">Loading records…</p>;
  }

  return (
    <>
      {records.map(record => (
        <RecordCard key={record.record_id} record={record} category={categories[record.record_id]} selected={selectedRecord === record.record_id} onSelect={() => onSelect(record.record_id)} />
      ))}
    </>
  );
}

export default function CrimeLocationPanel({ recordIds, categories, neighborhoodName, onBack, onClose }: Props) {
  const [page, setPage] = useState(0);
  const [attempt, setAttempt] = useState(0);
  const [selectedRecord, setSelectedRecord] = useState<number | null>(null);
  const pageCount = Math.max(1, Math.ceil(recordIds.length / PAGE_SIZE));
  return (
    <aside className="crime-location-panel" aria-labelledby="crime-location-title">
      <header className="crime-location-header">
        <div className="crime-location-title-row">
          <div><p className="incident-secondary">{neighborhoodName}</p><h2 id="crime-location-title">Records at this location</h2><p className="incident-secondary">{recordIds.length.toLocaleString()} {recordIds.length === 1 ? "record" : "records"}</p></div>
          <button type="button" className="crime-location-close" aria-label="Close crime location overview" onClick={onClose}><FontAwesomeIcon icon={faXmark} /></button>
        </div>
        <button type="button" className="crime-location-back" onClick={onBack}><FontAwesomeIcon icon={faArrowLeft} aria-hidden="true" /> Back to neighborhood</button>
        <p className="crime-location-notice">Locations may be approximate. Records may include service calls and police activity.</p>
      </header>
      <div className="crime-location-list" role="region" aria-label="Incident records" tabIndex={0}>
        {recordIds.length === 0 ? <p>No records at this location.</p> : <RecordPage key={`${page}-${attempt}`} recordIds={recordIds} page={page} categories={categories} selectedRecord={selectedRecord} onSelect={setSelectedRecord} onRetry={() => setAttempt(value => value + 1)} />}
      </div>
      {pageCount > 1 && <nav className="crime-location-pagination" aria-label="Location record pages">
        <button type="button" disabled={page === 0} onClick={() => { setPage(value => value - 1); setSelectedRecord(null); }}>Previous</button>
        <span aria-live="polite">{page + 1} / {pageCount}</span>
        <button type="button" disabled={page >= pageCount - 1} onClick={() => { setPage(value => value + 1); setSelectedRecord(null); }}>Next</button>
      </nav>}
    </aside>
  );
}
