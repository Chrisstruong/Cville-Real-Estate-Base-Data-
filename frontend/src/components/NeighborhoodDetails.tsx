import type { NeighborhoodFeature } from "../api/neighborhoods";

type Props = {
  selected: NeighborhoodFeature | null;
  onClear: () => void;
};

export default function NeighborhoodDetails({ selected, onClear }: Props) {
  return (
    <aside className="neighborhood-panel" aria-label="Neighborhood details">
      <h2>Planning neighborhoods</h2>
      <div aria-live="polite">
        {selected ? <>
          <h3>{selected.properties.NAME}</h3>
          <p>Neighborhood statistics are not yet available.</p>
          <button type="button" onClick={onClear}>Clear selection</button>
        </> : <p>Click a neighborhood boundary on the map to explore it.</p>}
      </div>
      <p>Crime locations are approximate. Boundaries alone do not establish which neighborhood an incident belongs to.</p>
    </aside>
  );
}
