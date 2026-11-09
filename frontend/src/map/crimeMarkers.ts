import type { Map as MapLibreMap } from "maplibre-gl";
import type {
  CrimeFeatureCollection,
} from "../api/crimes";
import {
  CRIME_CATEGORIES,
  normalizeCrimeCategory,
  type CrimeCategory,
} from "../config/crimeCategories";

function ensureMarkerImage(
  map: MapLibreMap,
  category: CrimeCategory,
  count: number,
): string {
  const multiple = count > 1;
  const imageId = multiple
    ? `crime-location-count-${count}`
    : `crime-category-${category}`;

  if (map.hasImage(imageId)) return imageId;

  // Render at double resolution for sharper markers.
  const canvas = document.createElement("canvas");
  canvas.width = 72;
  canvas.height = 72;

  const context = canvas.getContext("2d");
  if (!context) throw new Error("Could not create crime marker image.");

  context.scale(2, 2);

  const config = CRIME_CATEGORIES[category];

  context.fillStyle = multiple ? "#e23b3b" : config.background;
  context.beginPath();
  context.roundRect(0, 0, 36, 36, 8);
  context.fill();

  context.fillStyle = "#FFFFFF";

  if (multiple) {
    const text = String(count);
    let fontSize = 15;

    context.font = `700 ${fontSize}px sans-serif`;
    while (context.measureText(text).width > 30 && fontSize > 8) {
      fontSize -= 1;
      context.font = `700 ${fontSize}px sans-serif`;
    }

    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(text, 18, 18);
  } else {
    const [width, height, , , pathData] = config.icon.icon;
    const scale = 20 / Math.max(width, height);

    context.save();
    context.translate(
      (36 - width * scale) / 2,
      (36 - height * scale) / 2,
    );
    context.scale(scale, scale);

    const paths = Array.isArray(pathData) ? pathData : [pathData];
    for (const path of paths) {
      context.fill(new Path2D(path));
    }

    context.restore();
  }

  map.addImage(
    imageId,
    context.getImageData(0, 0, 72, 72),
    { pixelRatio: 2 },
  );

  return imageId;
}

export function prepareCrimeMarkers(
  map: MapLibreMap,
  data: CrimeFeatureCollection,
) {
  const groups = new Map<string, {
    count: number;
    firstRecordId: number;
  }>();

  for (const feature of data.features) {
    const [longitude, latitude] = feature.geometry.coordinates;
    const key = `${longitude},${latitude}`;
    const group = groups.get(key);

    if (group) {
      group.count += 1;
    } else {
      groups.set(key, {
        count: 1,
        firstRecordId: feature.properties.record_id,
      });
    }
  }

  return {
    ...data,
    features: data.features.map(feature => {
      const [longitude, latitude] = feature.geometry.coordinates;
      const group = groups.get(`${longitude},${latitude}`)!;
      const category = normalizeCrimeCategory(
        feature.properties.category,
      );

      return {
        ...feature,
        properties: {
          ...feature.properties,
          location_count: group.count,
          show_location_marker:
            feature.properties.record_id === group.firstRecordId,
          marker_image: ensureMarkerImage(
            map,
            category,
            group.count,
          ),
        },
      };
    }),
  };
}