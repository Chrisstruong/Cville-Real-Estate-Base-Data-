import { useEffect, useRef } from "react";
import * as maplibregl from 'maplibre-gl';
import "maplibre-gl/dist/maplibre-gl.css";
import type { FeatureCollection, Point } from "geojson";

import { fetchAllMapProperties, fetchPropertyByParcelNumber, } from "../api/properties";

function MapView() {
  const mapContainer = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,

      // Temporary OSM raster basemap 
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution:
              "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
          },
        ],
      },

      center: [-78.4767, 38.0293],
      zoom: 12,
    });

    map.on("load", async () => {
      try {
        const data = await fetchAllMapProperties();

        console.log("PROPERTY COUNT:", data.count);
        const geojson: FeatureCollection<Point> = {
          type: "FeatureCollection",

          features: data.properties.map((property) => ({
            type: "Feature",

            geometry: {
              type: "Point",
              coordinates: [
                property.longitude,
                property.latitude,
              ],
            },

            properties: {
              parcel_number: property.parcel_number,
            },
          })),
        };

        console.log("PROPERTY COUNT:", data.count);
        console.log("GEOJSON FEATURES:", geojson.features.length);

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

        map.on("click", "property-points", async (event) => {
          const feature = event.features?.[0];

          if (!feature) return;

          const parcelNumber = feature.properties?.parcel_number;

          if (!parcelNumber) return

          try {
            const property = await fetchPropertyByParcelNumber(parcelNumber);

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

            new maplibregl.Popup({
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

            console.log("Fetched property:", property);
          } catch (error) {
            console.error("Failed to fetch property:", error);
          }
        });

        map.on("click", "property-clusters", async (event) => {
          const feature = event.features?.[0]

          if (!feature) return;

          const clusterId = feature.properties?.cluster_id;

          if (clusterId === undefined) return;

          const source = map.getSource(
            "properties"
          ) as maplibregl.GeoJSONSource;

          const zoom = await source.getClusterExpansionZoom(clusterId);

          const coordinates = (
            feature.geometry as Point
          ).coordinates as [number, number];

          map.easeTo({
            center: coordinates,
            zoom: zoom,
          })
        })

        map.on("mouseenter", "property-points", (event) => {
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

    return () => {
      map.remove();
    };
  }, []);

  return (
    <div
      ref={mapContainer}
      style={{
        width: "100%",
        height: "100vh",
      }}
    />
  );
}

export default MapView;