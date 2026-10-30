# Charlottesville Real Estate AI Assistant — Project Update

I want to update you on the current progress and new direction of this project. Please read this carefully before making any code changes.

## 1. Project Background

This is a proof-of-concept application I'm developing during my internship with the City of Charlottesville's IT Department.

The potential future users are the City Manager's Office and Police Department.

Our main research objectives are to explore:

- Relationships between crime patterns and assessed property values.
- Whether neighborhood building age is associated with crime patterns.
- Differences in property assessments and reported crime between Charlottesville neighborhoods.
- How AI can help city employees analyze these datasets through natural-language questions.

This is an exploratory analytics platform, not a system for declaring whether a particular neighborhood is safe or unsafe.

## 2. Existing Technology

- Frontend: React, TypeScript, Vite, MapLibre
- Backend: Python, FastAPI
- Database: PostgreSQL
- AI: OpenAI Agents SDK
- Deployment: Vercel frontend, Render backend and PostgreSQL

Deployed frontend:
https://cville-real-estate-base-data.vercel.app/

## 3. Existing Progress

The application already has:

- A deployed React frontend and FastAPI backend.
- Working frontend-to-backend API requests.
- A PostgreSQL database containing property assessment records.
- Crime data from 2021 to the present.
- Official Charlottesville road centerline and road-block datasets.
- Street normalization and crime geolocation work.
- A MapLibre interactive map displaying properties and crime records.
- Property selection and detail functionality.

Please inspect the repository to verify which features and endpoints are actually implemented before modifying anything.

## 4. Updated Project Direction

We are moving toward neighborhood-level analysis.

The intended experience is:

1. Users open the application and see official Charlottesville Planning Neighborhood boundaries.
2. Users click a neighborhood, such as Fry's Spring or Greenbrier.
3. The map zooms to that neighborhood and displays relevant property and crime information.
4. A side panel displays neighborhood statistics, such as property counts, median assessed value, incident totals, and crime categories.
5. Users select individual properties to view details and compare assessed values with the neighborhood median.
6. Users can manually select multiple properties for comparison.
7. An AI assistant can explain the differences between selected properties using verified database information.
8. An AI research assistant can analyze neighborhood-level relationships between crime patterns, assessed values, and building ages.

Important data limitation: The existing real estate database does not currently contain property construction years. We need to obtain and integrate an official dataset containing year-built information before performing building-age analysis.

Crime locations may be approximate. Do not assume all records have precise coordinates or can be uniquely assigned to a neighborhood.

## 5. Current Milestone — 11.7 Neighborhood GIS Integration

We are currently working on displaying Charlottesville's official Planning Neighborhood boundaries.

Official GIS layer:
https://gisweb.charlottesville.org/gisweb/rest/services/Layers/MapServer/38

Tasks:

- Inspect the official GIS layer and verify its fields.
- Retrieve official neighborhood polygons as GeoJSON.
- Validate polygon geometry, IDs, names, and coordinate reference system.
- Add the GeoJSON source to the existing MapLibre map.
- Render semi-transparent neighborhood fills and visible outlines.
- Display neighborhood labels.
- Implement hover highlighting.
- Implement click-to-select and zoom-to-neighborhood.
- Add selected-neighborhood React state.
- Add a neighborhood details placeholder panel.
- Add a clear-selection button.
- Preserve existing property and crime functionality.

Do not implement neighborhood crime aggregation, property statistics, statistical analysis, or additional AI tools yet. Those are future milestones.

## 6. Instructions Before Coding

First, inspect the actual repository and provide:

1. What is already implemented.
2. What is missing for milestone 11.7.
3. Which existing files should be modified.
4. Which new files, if any, should be created.
5. A step-by-step implementation plan.

Do not assume features are implemented simply because they appear in this project update.

Do not overwrite or refactor unrelated working code.

After the review, implement milestone 11.7 incrementally, testing each checkpoint.

Keep the existing deployment architecture and API functionality unchanged unless a modification is necessary and explained.