# Vercel deployment

Import the repository as one project with Root Directory set to the repository
root. `vercel.json` defines the Vite `frontend` at `/` and FastAPI `backend`
(`app.main:app`) at `/api/*`. The API prefix is preserved.

Browser requests use same-origin `/api/...` URLs. No service bindings are needed:
the frontend has no server-side functions calling the backend, and the backend
does not call another Vercel service. Bindings are runtime function variables;
do not expose them through Vite build variables. PostgreSQL is external to these
services and requires its own hosted database.

## Environment

Set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and
`OPENAI_API_KEY` in Vercel for the intended deployment environment. The backend
currently requires the API key even for map-only use. Keep secrets out of Git
and frontend code. Use a PostgreSQL database reachable from Vercel; localhost
on your computer is not reachable there. Import the schema, records, and saved
coordinates if needed. Configure your provider's required TLS settings through
libpq environment variables such as `PGSSLMODE`, and account for connection
pools across multiple backend instances. This configuration does not provision
or migrate the database.

## Routing and verification

- Confirm service names and public routing before deploying. All `/api/*` routes,
  including chat and the test-property-street route, are exposed by this rule.
- `/health`, `/db-health`, `/docs`, and `/openapi.json` are not routed to FastAPI.
- For a manager-only demo, configure Deployment Protection and manager access.
- Install/authenticate the Vercel CLI, then run `vercel dev` from the repo root
  to test both services together. Check property/crime maps and detail popups.
- Run `npm run build` in `frontend` to verify the production frontend build.
- After confirmation, create a preview deployment. Repeat map and API checks
  with the hosted database and inspect runtime logs before sharing the URL.
- For standalone development, run FastAPI on port 8000 and Vite with
  `npm run dev`; Vite's local proxy forwards `/api` to FastAPI.

References:
- https://vercel.com/docs/services
- https://vercel.com/docs/services/routing
- https://vercel.com/docs/services/bindings
