import { useEffect, useState } from "react";
import { fetchMapCrimes } from "../api/crimes";
import type { CrimeFeatureCollection } from "../api/crimes";

export default function CrimeDataStatus() {
  const [data, setData] = useState<CrimeFeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCrimes() {
      try {
        const result = await fetchMapCrimes(controller.signal);

        if (!controller.signal.aborted) {
          setData(result);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load crime locations.",
          );
        }
      }
    }

    void loadCrimes();

    return () => controller.abort();
  }, []);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  return (
    <p role="status">
      {data === null
        ? "Loading crime locations…"
        : `${data.features.length.toLocaleString()} crime records loaded with approximate locations.`}
    </p>
  );
}