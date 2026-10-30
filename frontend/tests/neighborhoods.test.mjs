import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import { test } from "node:test";
import ts from "typescript";

// Exercise the real loader helpers without adding a browser test dependency.
const source = readFileSync(new URL("../src/api/neighborhoods.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2023 },
});
const { validateNeighborhoods, neighborhoodBounds } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);
const asset = JSON.parse(readFileSync(new URL("../public/data/planning-neighborhoods.geojson", import.meta.url), "utf8"));

test("official snapshot has 19 valid features within Charlottesville", () => {
  const data = validateNeighborhoods(asset);
  assert.equal(data.features.length, 19);
  for (const feature of data.features) {
    const [[west, south], [east, north]] = neighborhoodBounds(feature);
    assert.ok(west > -79 && east < -78 && south > 38 && north < 39);
  }
});

test("rejects duplicate IDs, missing names, open rings, and invalid coordinates", () => {
  const mutations = [
    data => { data.features.push(structuredClone(data.features[0])); },
    data => { data.features[0].properties.NAME = ""; },
    data => { data.features[0].geometry.coordinates[0].pop(); },
    data => { data.features[0].geometry.coordinates[0][1][0] = Infinity; },
  ];
  for (const mutate of mutations) {
    const data = structuredClone(asset);
    mutate(data);
    assert.throws(() => validateNeighborhoods(data));
  }
});

test("bounds include every part of a MultiPolygon", () => {
  const feature = structuredClone(asset.features[0]);
  feature.geometry = { type: "MultiPolygon", coordinates: [
    [[[0, 0], [1, 0], [1, 1], [0, 0]]],
    [[[4, 4], [5, 4], [5, 5], [4, 4]]],
  ] };
  validateNeighborhoods({ type: "FeatureCollection", features: [feature] });
  assert.deepEqual(neighborhoodBounds(feature), [[0, 0], [5, 5]]);
});
