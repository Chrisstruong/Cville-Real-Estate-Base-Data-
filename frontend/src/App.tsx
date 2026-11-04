import MapView from "./components/MapView";
import { useCallback, useState } from "react";
import type { NeighborhoodFeature } from "./api/neighborhoods";
import NeighborhoodOverviewPanel from "./components/NeighborhoodOverviewPanel";
import "./App.css";

function App() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState<NeighborhoodFeature | null>(null);
  const [overviewOpen, setOverviewOpen] = useState(false);

  const handleSelectNeighborhood = useCallback(
    (neighborhood: NeighborhoodFeature | null) => {
      setSelectedNeighborhood(neighborhood);
      setOverviewOpen(neighborhood !== null);
    },
    [],
  );
  return (
    <main className="neighborhood-explorer">
      <MapView
        selectedNeighborhood={selectedNeighborhood}
        onSelectNeighborhood={handleSelectNeighborhood}
      />
      {selectedNeighborhood && overviewOpen && (
        <NeighborhoodOverviewPanel
          neighborhoodId={selectedNeighborhood.id}
          neighborhoodName={selectedNeighborhood.properties.NAME}
          onClose={() => setOverviewOpen(false)}
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
              <button type="button" onClick={() => setOverviewOpen(true)}>
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
