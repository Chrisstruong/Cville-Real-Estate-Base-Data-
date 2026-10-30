import MapView from "./components/MapView";
import { useState } from "react";
import type { NeighborhoodFeature } from "./api/neighborhoods";
import "./App.css";

function App() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState<NeighborhoodFeature | null>(null);
  return (
    <main className="neighborhood-explorer">
      <MapView
      selectedNeighborhood={selectedNeighborhood}
      onSelectNeighborhood={setSelectedNeighborhood}
      />
      <div className="map-controls">
        {selectedNeighborhood ? (
          <>
          <strong>{selectedNeighborhood.properties.NAME}</strong>
          <button type="button" onClick={() => setSelectedNeighborhood(null)}
          >
            Clear section
          </button>
          <small>Crime locations are approximate.</small>
          </>
          ):(
            <span>Select a neighborhood to explore properties and crime records.</span>
          )}
      </div>
    </main>
  );

}

export default App;
