import MapView from "./components/MapView";
import ExplorerAI from "./components/ExplorerAI";
import { useStreetQuery } from "./hooks/useStreetQuery";
import { useCallback, useRef, useState } from "react";
import type { NeighborhoodFeature } from "./api/neighborhoods";
import type { MapContext } from "./api/chatContext";
import NeighborhoodOverviewPanel from "./components/NeighborhoodOverviewPanel";
import CrimeLocationPanel from "./components/CrimeLocationPanel";
import "./App.css";

function App() {
  const {
    result: streetResult,
    load: streetLoad,
    beginChatRequest,
    invalidateStreetQuery,
    acceptAction,
    cancelStreetLoading,
  } = useStreetQuery();
  const [aiOpen, setAiOpen] = useState(false);
  const askAIButtonRef = useRef<HTMLButtonElement>(null);

  function closeAI() {
    setAiOpen(false);
    askAIButtonRef.current?.focus();
  }
  const [selectedNeighborhood, setSelectedNeighborhood] = useState<NeighborhoodFeature | null>(null);
  const [overviewOpen, setOverviewOpen] = useState(false);
  const [selectedCrimeIds, setSelectedCrimeIds] =
    useState<number[] | null>(null);
  const appliedMapContext = useRef<MapContext | null>(null);

  const handleMapContextChange = useCallback((context: MapContext | null) => {
    appliedMapContext.current = context;
  }, []);

  const getMapContext = useCallback((): MapContext | null => {
    if (streetLoad.status === "loading") return null;

    const applied = appliedMapContext.current;
    if (!applied) return null;

    if (streetResult) {
      if (
        applied.mode !== "street" ||
        applied.street_id !== streetResult.street.street_id ||
        applied.filters.start_date !== streetResult.filters.start_date ||
        applied.filters.end_date !== streetResult.filters.end_date ||
        applied.filters.category !== streetResult.filters.category
      ) {
        return null;
      }

      return {
        mode: "street",
        street_id: applied.street_id,
        filters: { ...applied.filters },
      };
    }

    if (selectedNeighborhood) {
      return (
        applied.mode === "neighborhood" &&
        applied.neighborhood_id === selectedNeighborhood.id
      )
        ? { ...applied }
        : null;
    }

    return applied.mode === "city" ? { mode: "city" } : null;
  }, [streetLoad.status, streetResult, selectedNeighborhood]);

  const [crimeCategories, setCrimeCategories] = useState<Record<number, string>>({});
  const handleSelectCrimeLocation = useCallback((recordIds: number[], categories: Record<number, string>) => {
    setCrimeCategories(categories);
    setSelectedCrimeIds(recordIds);
    setOverviewOpen(false);
  }, []);

  const showNeighborhoodOverview = useCallback(() => {
    setSelectedCrimeIds(null);
    setOverviewOpen(true);
  }, []);

  const clearCrimeSelection = useCallback(() => {
    setSelectedCrimeIds(null);
  }, []);

  const returnToNeighborhoods = useCallback(() => {
    invalidateStreetQuery();
    setSelectedCrimeIds(null);
  }, [invalidateStreetQuery]);

  const handleSelectNeighborhood = useCallback(
    (neighborhood: NeighborhoodFeature | null) => {
      invalidateStreetQuery();
      setSelectedNeighborhood(neighborhood);
      setSelectedCrimeIds(null);
      setOverviewOpen(neighborhood !== null);
    },
    [invalidateStreetQuery],
  );
  return (
    <main
      className={`neighborhood-explorer${aiOpen ? " ai-open" : ""}`}
    >
      <div className="map-workspace">
        <button
          ref={askAIButtonRef}
          type="button"
          className="ask-ai-button"
          aria-controls="explorer-ai"
          aria-expanded={aiOpen}
          onClick={() => {
            if (aiOpen) closeAI();
            else setAiOpen(true);
          }}
        >
          <span aria-hidden="true">✦</span>
          {aiOpen ? "Close AI" : "Ask AI"}
        </button>
        <MapView
          streetResult={streetResult}
          selectedCrimeIds={selectedCrimeIds}
          selectedNeighborhood={selectedNeighborhood}
          onSelectNeighborhood={handleSelectNeighborhood}
          onSelectCrimeLocation={handleSelectCrimeLocation}
          onClearCrimeSelection={clearCrimeSelection}
          onMapContextChange={handleMapContextChange}
        />
        {!streetResult && selectedNeighborhood && overviewOpen && !selectedCrimeIds && (
          <NeighborhoodOverviewPanel
            neighborhoodId={selectedNeighborhood.id}
            neighborhoodName={selectedNeighborhood.properties.NAME}
            onClose={() => setOverviewOpen(false)}
          />
        )}
        {selectedCrimeIds && (streetResult || selectedNeighborhood) && (
          <CrimeLocationPanel
            key={selectedCrimeIds.join(",")}
            recordIds={selectedCrimeIds}
            categories={crimeCategories}
            contextName={
              streetResult?.street.name ??
              selectedNeighborhood!.properties.NAME
            }
            backLabel={
              streetResult ? "Back to street" : "Back to neighborhood"
            }
            onBack={
              streetResult ? clearCrimeSelection : showNeighborhoodOverview
            }
            onClose={clearCrimeSelection}
          />
        )}
        <div className="map-controls">
          {streetLoad.status === "loading" && (
            <div role="status">
              Loading street records…{" "}
              <button type="button" onClick={cancelStreetLoading}>
                Cancel
              </button>
            </div>
          )}

          {streetLoad.status === "error" && (
            <p role="alert">{streetLoad.message}</p>
          )}

          {streetResult && (
            <>
              <strong>{streetResult.street.name}</strong>

              <button type="button" onClick={returnToNeighborhoods}>
                Back to neighborhoods
              </button>

              <small>
                {streetResult.filters.start_date && streetResult.filters.end_date
                  ? `Reported ${streetResult.filters.start_date} through ${streetResult.filters.end_date}.`
                  : "All available reporting dates."}
                {" "}
                Category: {streetResult.filters.category?.replaceAll("_", " ") ?? "all"}.
              </small>

              <small>
                {streetResult.summary.associated_record_count.toLocaleString()} associated
                records;{" "}
                {streetResult.summary.mapped_record_count.toLocaleString()} mapped;{" "}
                {streetResult.summary.unmapped_record_count.toLocaleString()} without usable
                coordinates.
              </small>

              <small>
                Locations may be approximate. Highlight shows available official road blocks.
              </small>
            </>
          )}
          {!streetResult && (selectedNeighborhood ? (
            <>
              <strong>{selectedNeighborhood.properties.NAME}</strong>
              <button type="button" onClick={() => handleSelectNeighborhood(null)}
              >
                Clear selection
              </button>
              {!overviewOpen && (
                <button type="button" onClick={showNeighborhoodOverview}>
                  Show overview
                </button>
              )}
              <small>Crime locations are approximate.</small>
            </>
          ) : (
            <span>Select a neighborhood to explore properties and crime records.</span>
          ))}
        </div>
      </div>
      <ExplorerAI
        open={aiOpen}
        onClose={closeAI}
        beginChatRequest={beginChatRequest}
        onMapAction={acceptAction}
        getMapContext={getMapContext}
      />
    </main>
  );

}

export default App;
