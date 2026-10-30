import { useEffect, useRef, useState } from "react";
import * as maplibregl from 'maplibre-gl';
import "maplibre-gl/dist/maplibre-gl.css";
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type { FeatureCollection, Point } from "geojson";

import { fetchPropertyByParcelNumber } from "../api/properties";
import { fetchCrimeDetails } from "../api/crimes";
import type { CrimeFeature } from "../api/crimes";
import {
  fetchNeighborhoodProperties,
  fetchNeighborhoodCrimes,
} from "../api/neighborhoodRecords"
import { fetchNeighborhoods, neighborhoodBounds } from "../api/neighborhoods";
import type { NeighborhoodFeature } from "../api/neighborhoods";

const NEIGHBORHOOD_PALETTE = [
  "#A8C9B0", // Sage Green
  "#A9C8E8", // Soft Blue
  "#F1D39B", // Warm Sand
  "#C8B7DF", // Muted Lavender
  "#9BD3D0", // Soft Teal
  "#E8B7AE", // Dusty Rose
];

// MapLibre v6 needs an explicit worker URL when bundled by Vite.
maplibregl.setWorkerUrl(maplibreWorkerUrl);

type Props = {
  selectedNeighborhood: NeighborhoodFeature | null;
  onSelectNeighborhood: (feature: NeighborhoodFeature) => void;
};
const DETAIL_LAYERS = [
  "property-clusters",
  "property-cluster-count",
  "property-points",
  "crime-clusters",
  "crime-points",
];
const EMPTY_POINTS: FeatureCollection<Point> = {
  type: "FeatureCollection",
  features: [],
}
function locationKey(longitude: number, latitude: number) {
  return `${longitude},${latitude}`
}
function setDetailVisibility(
  map: maplibregl.Map,
  visible: boolean,
) {
  for (const id of DETAIL_LAYERS) {
    if (map.getLayer(id)) {
      map.setLayoutProperty(
        id,
        "visibility",
        visible ? "visible" : "none",
      )
    }
  }
}

function MapView({ selectedNeighborhood, onSelectNeighborhood }: Props) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [neighborhoodStatus, setNeighborhoodStatus] = useState("Loading neighborhoods…");
  const [neighborhoodError, setNeighborhoodError] = useState(false);
  const [recordsStatus, setRecordsStatus] = useState("");
  const [recordsError, setRecordsError] = useState(false);

  //Incremented whenever selection changes
  const recordsVersion = useRef(0)

  //Click handlers read the latest records from these refs
  const crimesById = useRef(new Map<number, CrimeFeature>());
  const crimesByLocation = useRef(new Map<string, CrimeFeature[]>());

  //Track open marker popups so switching closes them
  const recordPopups = useRef(new Set<maplibregl.Popup>());

  //Serialize source updates so older write cannot finish last
  const sourceWrites = useRef<Promise<void>>(Promise.resolve());




  // Synchronize React selection with the existing map, without rebuilding it.
  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getSource("neighborhoods")) return;
    if (!selectedNeighborhood) {
      map.easeTo({ center: [-78.4767, 38.0293], zoom: 12 });
      return;
    }
    map.setFeatureState({ source: "neighborhoods", id: selectedNeighborhood.id }, { selected: true });
    map.fitBounds(neighborhoodBounds(selectedNeighborhood), { padding: 40, maxZoom: 16 });
    return () => {
      if (mapRef.current === map && map.getSource("neighborhoods")) {
        map.setFeatureState({ source: "neighborhoods", id: selectedNeighborhood.id }, { selected: false });
      }
    };
  }, [selectedNeighborhood]);

  useEffect(() => {
    if (!mapContainer.current) return;
    const crimeController = new AbortController()

    const map = new maplibregl.Map({
      container: mapContainer.current,

      // Temporary OSM raster basemap 
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            // Reuse zoom-19 tiles when zooming beyond OSM's tile coverage.
            maxzoom: 19,
            attribution:
              "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
            paint: {
              "raster-saturation": -0.65,
              "raster-contrast": -0.15,
              "raster-brightness-min": 0.15,
            },
          },
        ],
      },

      center: [-78.4767, 38.0293],
      zoom: 12,
    });
    mapRef.current = map;
    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(mapContainer.current);

    map.on("load", async () => {
      try {
        const neighborhoods = await fetchNeighborhoods(crimeController.signal);
        if (crimeController.signal.aborted) return;
        const sortedIds = neighborhoods.features
          .map(feature => feature.id)
          .sort((a, b) => a - b);

        for (const feature of neighborhoods.features) {
          const colorIndex = sortedIds.indexOf(feature.id);

          Object.assign(feature.properties, {
            color: NEIGHBORHOOD_PALETTE[
              colorIndex % NEIGHBORHOOD_PALETTE.length
            ],
          });
        }
        map.addSource("neighborhoods", { type: "geojson", data: neighborhoods });
        // Insert before whichever marker layer arrived first.
        const before = map.getStyle().layers.find(layer => layer.id !== "osm")?.id;
        map.addLayer({
          id: "neighborhood-fills", type: "fill", source: "neighborhoods",
          paint: {
            "fill-color": ["get", "color"],

            "fill-opacity": [
              "case",
              ["boolean", ["feature-state", "selected"], false], 0.23,
              ["boolean", ["feature-state", "hover"], false], 0.4,
              0.35,
            ],
          },
        }, before);
        map.addLayer({
          id: "neighborhood-outlines", type: "line", source: "neighborhoods",
          paint: {
            "line-color": [
              "case",

              ["boolean", ["feature-state", "selected"], false],
              "#2563EB",

              ["boolean", ["feature-state", "hover"], false],
              "#2563EB",

              "#475569",
            ],

            "line-width": [
              "case",

              ["boolean", ["feature-state", "selected"], false],
              3.5,

              ["boolean", ["feature-state", "hover"], false],
              2.5,

              1.75,
            ],
          },
        }, before);
        map.addLayer({
          id: "neighborhood-labels", type: "symbol", source: "neighborhoods",
          layout: {
            "text-field": ["get", "NAME"],
            "text-font": ["Open Sans Regular"],

            "text-size": [
              "interpolate",
              ["linear"],
              ["zoom"],
              11, 13,
              14, 16,
            ],

            "text-max-width": 12,
            "text-padding": 4,
          },

          paint: {
            "text-color": "#172B4D",
            "text-halo-color": "#FFFFFF",
            "text-halo-width": 2,
            "text-halo-blur": 0.5,
          },

        }, before);

        const markerLayers = ["property-points", "property-clusters", "crime-points", "crime-clusters"];
        function markerAt(point: maplibregl.Point) {
          const layers = markerLayers.filter(id => map.getLayer(id));
          return layers.length > 0 && map.queryRenderedFeatures(point, { layers }).length > 0;
        }
        let hovered: number | null = null;
        function clearHover() {
          if (hovered !== null) map.setFeatureState({ source: "neighborhoods", id: hovered }, { hover: false });
          hovered = null;
        }
        map.on("mousemove", "neighborhood-fills", event => {
          clearHover();
          if (!markerAt(event.point)) {
            hovered = Number(event.features?.[0]?.id);
            if (Number.isInteger(hovered)) map.setFeatureState({ source: "neighborhoods", id: hovered }, { hover: true });
          }
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "neighborhood-fills", () => {
          clearHover();
          map.getCanvas().style.cursor = "";
        });
        map.on("click", "neighborhood-fills", event => {
          if (markerAt(event.point)) return;
          const feature = neighborhoods.features.find(item => item.id === event.features?.[0]?.id);
          if (feature) {
            onSelectNeighborhood(feature);
            // Also zoom when clicking the already-selected feature.
            map.fitBounds(neighborhoodBounds(feature), { padding: 40, maxZoom: 16 });
          }
        });
        setNeighborhoodStatus(`${neighborhoods.features.length} planning neighborhoods loaded.`);
      } catch (error) {
        if (crimeController.signal.aborted) return;
        setNeighborhoodError(true);
        setNeighborhoodStatus(error instanceof Error ? error.message : "Could not load neighborhoods.");
      }
    });

    map.on("load", async () => {
      try {
        const geojson: FeatureCollection<Point> = {
          type: "FeatureCollection",
          features: [],
        }

        map.addSource("properties", {
          type: "geojson",
          data: geojson,

          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 50,
        });

        map.addLayer({
          id: "property-clusters",
          type: "circle",
          source: "properties",
          layout: {
            visibility: "none",
          },

          filter: ["has", "point_count"],

          paint: {
            "circle-radius": [
              "step",
              ["get", "point_count"],
              18,
              100,
              24,
              500,
              30,
            ],
            "circle-color": "#2563eb",
            "circle-opacity": 0.85,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          }
        });

        map.addLayer({
          id: "property-cluster-count",
          type: "symbol",
          source: "properties",

          filter: ["has", "point_count"],

          layout: {
            visibility: "none", // Add this line.
            "text-field": "{point_count_abbreviated}",
            "text-size": 12,
          },

          paint: {
            "text-color": "#ffffff",
          }
        })


        map.addLayer({
          id: "property-points",
          type: "circle",
          source: "properties",
          layout: {
            visibility: "none",
          },

          filter: ["!", ["has", "point_count"]],

          paint: {
            "circle-radius": [
              "interpolate",
              ["linear"],
              ["zoom"],
              12, 3,
              15, 5,
              18, 8,
            ],

            "circle-color": "#0f766e",
            "circle-opacity": 0.85,

            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
          },
        });
        for (const layer of ["crime-clusters", "crime-points"]) {
          if (map.getLayer(layer)) {
            map.moveLayer(layer);
          }
        }


        map.on("click", "property-points", async (event) => {
          const crimeLayers = ["crime-clusters", "crime-points"].filter(
            (layer) => map.getLayer(layer) !== undefined,
          );

          if (
            crimeLayers.length > 0 &&
            map.queryRenderedFeatures(event.point, {
              layers: crimeLayers,
            }).length > 0
          ) {
            return;
          }
          const feature = event.features?.[0];

          if (!feature) return;

          const parcelNumber = feature.properties?.parcel_number;

          if (!parcelNumber) return
          const requestVersion = recordsVersion.current;

          try {
            const property = await fetchPropertyByParcelNumber(parcelNumber);
            if (crimeController.signal.aborted ||
              requestVersion !== recordsVersion.current
            ) {
              return
            }

            if (
              property.longitude === null ||
              property.latitude === null
            ) {
              return;
            }
            const address = [
              property.st_number,
              property.st_name,
              property.st_unit,
            ].filter(Boolean).join(" ");

            const assessedValue = property.current_assessed_value.toLocaleString();

            const lotSize = property.lot_sqft.toLocaleString();

            const popup = new maplibregl.Popup({
              offset: 12,
            }).setLngLat([
              property.longitude!,
              property.latitude!,
            ]).setHTML(`
              <div>
              <strong>${address}</strong>

              <p>
              Assessed Value: $${assessedValue}
              </p>

              <p> Lot Size: ${lotSize} sq ft</p>

              <p> Parcel: ${property.parcel_number}</p>

            </div>
            `).addTo(map);
            recordPopups.current.add(popup);
            popup.on("close", () => {
              recordPopups.current.delete(popup);
            });

            console.log("Fetched property:", property);
          } catch (error) {
            console.error("Failed to fetch property:", error);
          }
        });

        map.on("click", "property-clusters", async (event) => {
          const crimeLayers = ["crime-clusters", "crime-points"].filter(
            (layer) => map.getLayer(layer) !== undefined,
          );

          if (
            crimeLayers.length > 0 &&
            map.queryRenderedFeatures(event.point, {
              layers: crimeLayers,
            }).length > 0
          ) {
            return;
          }
          const feature = event.features?.[0]

          if (!feature) return;

          const clusterId = feature.properties?.cluster_id;

          if (clusterId === undefined) return;

          const source = map.getSource(
            "properties"
          ) as maplibregl.GeoJSONSource;

          const requestVersion = recordsVersion.current;
          try {
            const zoom = await source.getClusterExpansionZoom(clusterId);
            if (crimeController.signal.aborted || requestVersion !== recordsVersion.current) return;

            const coordinates = (feature.geometry as Point).coordinates as [number, number];
            map.easeTo({ center: coordinates, zoom });
          } catch (error) {
            if (!crimeController.signal.aborted && requestVersion === recordsVersion.current) {
              console.error("Could not expand property cluster:", error);
            }
          }
        })

        map.on("mouseenter", "property-points", () => {
          map.getCanvas().style.cursor = "pointer";
        });

        map.on("mouseleave", "property-points", () => {
          map.getCanvas().style.cursor = "";
        })

        map.on("mouseenter", "property-clusters", () => {
          map.getCanvas().style.cursor = "pointer";
        });

        map.on("mouseleave", "property-clusters", () => {
          map.getCanvas().style.cursor = "";
        });

        console.log("GEOJSON FEATURES:", geojson.features.length);
      }
      catch (error) {
        console.error("Failed to load properties:", error)
      }
    });

    map.on("load", async () => {
      try {


        map.addSource("crimes", {
          type: "geojson",
          data: EMPTY_POINTS,
          cluster: true,
          clusterMaxZoom: 16,
          clusterRadius: 45,
        });

        // Circles representing groups of crime records.
        map.addLayer({
          id: "crime-clusters",
          type: "circle",
          source: "crimes",
          layout: {
            visibility: "none",
          },
          filter: ["has", "point_count"],
          paint: {
            "circle-color": "#c2410c",
            "circle-radius": [
              "step",
              ["get", "point_count"],
              16,
              100,
              22,
              500,
              28,
            ],
            "circle-opacity": 0.85,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        });

        // Individual records that are not currently clustered.
        map.addLayer({
          id: "crime-points",
          type: "circle",
          source: "crimes",
          layout: {
            visibility: "none",
          },
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-color": "#ea580c",
            "circle-radius": [
              "interpolate",
              ["linear"],
              ["zoom"],
              12, 4,
              16, 6,
              19, 9,
            ],
            "circle-opacity": 0.8,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
          },
        });

        map.on("click", "crime-points", (event) => {
          const clickedFeature = event.features?.[0];

          if (!clickedFeature) return;

          const recordId = Number(clickedFeature.properties.record_id);

          // Use original GeoJSON coordinates, avoiding rendered-coordinate rounding.
          const originalFeature = crimesById.current.get(recordId);

          if (!originalFeature) return;

          const [longitude, latitude] = originalFeature.geometry.coordinates;
          const key = locationKey(longitude, latitude);
          const records = crimesByLocation.current.get(key) ?? [];

          if (records.length === 0) return;

          const container = document.createElement("div");
          container.style.minWidth = "220px";

          const heading = document.createElement("strong");
          heading.textContent =
            records.length === 1
              ? "1 crime record at this location"
              : `${records.length.toLocaleString()} crime records at this location`;

          const explanation = document.createElement("p");
          explanation.textContent =
            "Approximate mapped location—not an exact incident address.";

          const label = document.createElement("label");
          label.textContent = "Choose a record: ";
          label.style.display = "block";

          const select = document.createElement("select");
          select.style.width = "100%";

          for (const record of records) {
            const option = document.createElement("option");

            option.value = String(record.properties.record_id);
            option.textContent = `Record #${record.properties.record_id}`;

            select.appendChild(option);
          }

          select.value = String(recordId);
          label.appendChild(select);

          const selection = document.createElement("p");
          const detailStatus = document.createElement("p");
          detailStatus.setAttribute("role", "status");

          const detailContent = document.createElement("div");

          function addDetail(label: string, value: string) {
            const row = document.createElement("p");
            row.style.margin = "6px 0";

            const title = document.createElement("strong");
            title.textContent = `${label}: `;

            row.append(title, document.createTextNode(value));
            detailContent.appendChild(row);
          }

          let detailController: AbortController | null = null;

          async function showSelection() {
            // Stop the previous request when the user changes selection.
            detailController?.abort();

            const selectedId = Number(select.value);
            const selected = records.find(
              (record) => record.properties.record_id === selectedId,
            );

            if (!selected || crimeController.signal.aborted) return;

            const precision = selected.properties.location_precision;

            selection.textContent =
              `Selected record #${selectedId}. Location precision: ` +
              (precision === "block_approximate"
                ? "approximate block location."
                : precision === "intersection_approximate"
                  ? "approximate intersection location."
                  : precision);

            detailContent.replaceChildren();
            detailStatus.textContent = "Loading record details…";

            const controller = new AbortController();
            detailController = controller;

            try {
              const details = await fetchCrimeDetails(
                selectedId,
                controller.signal,
              );

              // An older response must not replace the current selection.
              if (
                controller.signal.aborted ||
                crimeController.signal.aborted ||
                detailController !== controller
              ) {
                return;
              }

              detailStatus.textContent = "";
              detailContent.replaceChildren();

              addDetail("Record", String(details.record_id));

              addDetail(
                "Offense",
                details.offense?.trim() || "Not provided",
              );

              let reportedDate = "Not provided";

              if (details.date_reported) {
                const parsedDate = new Date(details.date_reported);

                if (!Number.isNaN(parsedDate.getTime())) {
                  reportedDate = new Intl.DateTimeFormat("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                    timeZone: "America/New_York",
                    timeZoneName: "short",
                  }).format(parsedDate);
                } else {
                  reportedDate = "Unavailable";
                }
              }

              addDetail("Reported", reportedDate);

              addDetail(
                "Street",
                details.street_name?.trim() || "Not provided",
              );

              addDetail(
                "Block",
                details.block_number !== null
                  ? String(details.block_number)
                  : "Not provided",
              );

              const precisionLabel =
                details.location_precision === "block_approximate"
                  ? "Approximate block location"
                  : details.location_precision === "intersection_approximate"
                    ? "Approximate intersection location"
                    : "Precision unavailable";

              addDetail("Location precision", precisionLabel);
            } catch (error) {
              if (
                controller.signal.aborted ||
                crimeController.signal.aborted ||
                detailController !== controller
              ) {
                return;
              }

              detailStatus.textContent =
                error instanceof Error
                  ? error.message
                  : "Could not load crime details.";
            }
          }

          select.addEventListener("change", () => {
            void showSelection();
          });

          container.append(
            heading,
            explanation,
            label,
            selection,
            detailStatus,
            detailContent,
          );

          const popup = new maplibregl.Popup({
            offset: 12,
            maxWidth: "340px",
          })
            .setLngLat([longitude, latitude])
            .setDOMContent(container)
            .addTo(map);

          recordPopups.current.add(popup);

          function cancelDetails() {
            detailController?.abort();
          }

          // Cancel pending details when the component unmounts.
          crimeController.signal.addEventListener(
            "abort",
            cancelDetails,
            { once: true },
          );

          // Also cancel when this popup closes.
          popup.on("close", () => {
            recordPopups.current.delete(popup);
            cancelDetails();
            crimeController.signal.removeEventListener(
              "abort",
              cancelDetails,
            );
          });

          void showSelection();
        });

        map.on("click", "crime-clusters", async (event) => {
          const feature = event.features?.[0];

          if (!feature || feature.geometry.type !== "Point") return;

          const clusterId = Number(feature.properties.cluster_id);
          const count = Number(feature.properties.point_count);

          if (!Number.isFinite(clusterId)) return;

          const coordinates: [number, number] = [
            feature.geometry.coordinates[0],
            feature.geometry.coordinates[1],
          ];

          const requestVersion = recordsVersion.current;
          try {
            const source = map.getSource("crimes") as maplibregl.GeoJSONSource;

            const zoom = await source.getClusterExpansionZoom(clusterId);

            if (crimeController.signal.aborted || requestVersion !== recordsVersion.current) return;

            map.easeTo({
              center: coordinates,
              zoom,
            });

            const popup = new maplibregl.Popup({ offset: 12 })
              .setLngLat(coordinates)
              .setText(
                `${count.toLocaleString()} crime records in this cluster. ` +
                "Locations are approximate.",
              )
              .addTo(map);
            recordPopups.current.add(popup);
            popup.on("close", () => recordPopups.current.delete(popup));
          } catch (error) {
            if (!crimeController.signal.aborted && requestVersion === recordsVersion.current) {
              console.error("Could not expand crime cluster:", error);
            }
          }
        });

        for (const layer of ["crime-clusters", "crime-points"]) {
          map.on("mouseenter", layer, () => {
            map.getCanvas().style.cursor = "pointer";
          });

          map.on("mouseleave", layer, () => {
            map.getCanvas().style.cursor = "";
          });
        }

      } catch (error) {
        if (!crimeController.signal.aborted) {
          console.error("Failed to load crime locations:", error);
        }
      }
    });

    return () => {
      crimeController.abort();
      resizeObserver.disconnect();
      mapRef.current = null;
      map.remove();
    };
  }, [onSelectNeighborhood]);
  useEffect(() => {
    const currentMap = mapRef.current;
    if (!currentMap) return;
    const map: maplibregl.Map = currentMap;

    const controller = new AbortController();
    const version = ++recordsVersion.current;
    let started = false;

    function isCurrent() {
      return (
        !controller.signal.aborted &&
        recordsVersion.current === version &&
        mapRef.current === map
      );
    }

    function clearLookupsAndPopups() {
      crimesById.current.clear();
      crimesByLocation.current.clear();

      for (const popup of recordPopups.current) {
        popup.remove();
      }

      recordPopups.current.clear();
    }

    // Hide immediately; setData is asynchronous.
    setDetailVisibility(map, false);
    clearLookupsAndPopups();

    async function startLoading() {
      if (started || !isCurrent()) return;

      const propertiesSource = map.getSource(
        "properties",
      ) as maplibregl.GeoJSONSource | undefined;

      const crimesSource = map.getSource(
        "crimes",
      ) as maplibregl.GeoJSONSource | undefined;

      if (!propertiesSource || !crimesSource) return;

      started = true;
      setRecordsError(false);

      function writeSources(
        properties: FeatureCollection<Point>,
        crimes: FeatureCollection<Point>,
      ) {
        const operation = sourceWrites.current.then(async () => {
          if (!isCurrent()) return;

          const results = await Promise.allSettled([
            propertiesSource!.setData(properties),
            crimesSource!.setData(crimes),
          ]);

          for (const result of results) {
            if (result.status === "rejected") {
              throw result.reason;
            }
          }
        });

        // Keep the queue usable after a failed update.
        sourceWrites.current = operation.catch(() => { });
        return operation;
      }

      try {
        await writeSources(EMPTY_POINTS, EMPTY_POINTS);
        if (!isCurrent()) return;

        if (!selectedNeighborhood) {
          setRecordsStatus("");
          return;
        }

        const id = selectedNeighborhood.id;
        const name = selectedNeighborhood.properties.NAME;

        setRecordsStatus(`Loading properties and crime records for ${name}…`);

        // Both must succeed before either dataset becomes visible.
        const [properties, crimes] = await Promise.all([
          fetchNeighborhoodProperties(id, controller.signal),
          fetchNeighborhoodCrimes(id, controller.signal),
        ]);

        if (!isCurrent()) return;

        await writeSources(properties, crimes);
        if (!isCurrent()) return;

        for (const feature of crimes.features) {
          crimesById.current.set(
            feature.properties.record_id,
            feature,
          );

          const [longitude, latitude] = feature.geometry.coordinates;
          const key = locationKey(longitude, latitude);
          const records = crimesByLocation.current.get(key) ?? [];

          records.push(feature);
          crimesByLocation.current.set(key, records);
        }

        const propertyCount = properties.features.length;
        const crimeCount = crimes.features.length;

        setDetailVisibility(map, true);

        setRecordsStatus(
          `${name}: ` +
          `${propertyCount === 0 ? "No properties" : `${propertyCount.toLocaleString()} properties`}; ` +
          `${crimeCount === 0 ? "no mapped crime records" : `${crimeCount.toLocaleString()} mapped crime records`}.`,
        );
      } catch (error) {
        if (!isCurrent()) return;

        setDetailVisibility(map, false);
        clearLookupsAndPopups();

        // Clear any partially updated source before reporting failure.
        try {
          await writeSources(EMPTY_POINTS, EMPTY_POINTS);
        } catch {
          // Layers remain hidden even if clearing fails.
        }

        if (!isCurrent()) return;

        setRecordsError(true);
        setRecordsStatus(
          error instanceof Error
            ? error.message
            : "Could not load neighborhood records.",
        );

        // Cancel the other fetch if one request failed.
        controller.abort();
      }
    }

    // Handles both an already-loaded map and sources added later.
    const onStyleData = () => {
      void startLoading();
    };

    map.on("styledata", onStyleData);
    void startLoading();

    return () => {
      controller.abort();
      recordsVersion.current = version + 1;
      map.off("styledata", onStyleData);

      if (mapRef.current === map) {
        setDetailVisibility(map, false);
      }

      clearLookupsAndPopups();
    };
  }, [selectedNeighborhood]);





  return (
    <section className="neighborhood-map" aria-label="Property, crime, and neighborhood map">
      <p className="neighborhood-load-status" role={neighborhoodError || recordsError ? "alert" : "status"}>
        {neighborhoodStatus}
        {recordsStatus && <><br />{recordsStatus}</>}
      </p>
      <div
        ref={mapContainer}
        style={{
          width: "100%",
          height: "100%",
        }}
      />
    </section>
  );
}

export default MapView;
