# Render backend deployment

The backend requirements and application live in `backend`, not the repository
root. Configure an existing Render Web Service with:

| Setting | Value |
| --- | --- |
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

Deploy a Git branch containing the Linux-compatible requirements change
(`pywin32` has a Windows-only marker). The local deployment branch is
`configure-vercel-deployment`; push it before selecting it in Render, or merge
the reviewed changes into the branch Render already deploys.

For Blueprint-managed setup, the repository's `render.yaml` supplies these
settings. Adding that file alone does not reconfigure an existing manually
created service. Update that service's settings directly, or deliberately
connect it to a Blueprint. Match the service name before adopting a Blueprint
if you intend to update an existing service instead of creating another one.

Set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and
`OPENAI_API_KEY` in Render's environment settings. Keep `backend/.env` local
and untracked. PostgreSQL must be reachable from Render; a local database
on your computer will not work. Apply the database provider's TLS requirements.

This configuration deploys only the backend. The frontend currently uses
same-origin `/api` URLs for Vercel Services. Hosting it separately requires
an API reverse proxy or a configurable backend URL plus appropriate CORS;
deploying this Render backend alone does not connect the frontend to it.

After deployment, verify `/health`, `/api/properties/map/all`, and
`/api/crimes/map`, then test both detail endpoints. A successful configuration
check does not prove dependency installation or database connectivity in Render.

Reference: https://render.com/docs/blueprint-spec
