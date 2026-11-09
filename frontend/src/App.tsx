import MapView from "./components/MapView";
import { useCallback, useState } from "react";
import type { NeighborhoodFeature } from "./api/neighborhoods";
import NeighborhoodOverviewPanel from "./components/NeighborhoodOverviewPanel";
import CrimeLocationPanel from "./components/CrimeLocationPanel";
import "./App.css";

function App() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState<NeighborhoodFeature | null>(null);
  const [overviewOpen, setOverviewOpen] = useState(false);
  const [selectedCrimeIds, setSelectedCrimeIds] =
    useState<number[] | null>(null);

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

  const handleSelectNeighborhood = useCallback(
    (neighborhood: NeighborhoodFeature | null) => {
      setSelectedNeighborhood(neighborhood);
      setSelectedCrimeIds(null); // Add this.
      setOverviewOpen(neighborhood !== null);
    },
    [],
  );
  return (
    <main className="neighborhood-explorer">
      <MapView
        selectedCrimeIds={selectedCrimeIds}
        selectedNeighborhood={selectedNeighborhood}
        onSelectNeighborhood={handleSelectNeighborhood}
        onSelectCrimeLocation={handleSelectCrimeLocation}
        onClearCrimeSelection={clearCrimeSelection}
      />
      {selectedNeighborhood && overviewOpen && !selectedCrimeIds && (
        <NeighborhoodOverviewPanel
          neighborhoodId={selectedNeighborhood.id}
          neighborhoodName={selectedNeighborhood.properties.NAME}
          onClose={() => setOverviewOpen(false)}
        />
      )}
      {selectedNeighborhood && selectedCrimeIds && (
        <CrimeLocationPanel
          key={selectedCrimeIds.join(",")}
          recordIds={selectedCrimeIds}
          categories={crimeCategories}
          neighborhoodName={selectedNeighborhood.properties.NAME}
          onBack={showNeighborhoodOverview}
          onClose={clearCrimeSelection}
        />
      )}
      <div className="map-controls">
        {selectedNeighborhood ? (
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
        )}
      </div>
    </main>
  );

}

export default App;
