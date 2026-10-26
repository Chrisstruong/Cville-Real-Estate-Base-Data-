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

If the frontend is hosted separately on Vercel, set `CORS_ORIGINS` in Render to
the exact Vercel site origin (for example, `https://your-site.vercel.app`).
For multiple allowed origins, separate them with commas. Set
`VITE_API_BASE_URL` in the Vercel frontend project to the Render API origin
(for example, `https://cville-real-estate-base-data.onrender.com`, without
`/api`). Redeploy the frontend after changing it: Vite embeds this value at
build time. Both values are public origins, not credentials.

This configuration deploys only the backend. Without `VITE_API_BASE_URL`, the
frontend continues to use same-origin `/api` URLs for local Vite development or
the Vercel Services configuration in `vercel.json`.

After deployment, verify `/health`, `/api/properties/map/all`, and
`/api/crimes/map`, then test both detail endpoints. A successful configuration
check does not prove dependency installation or database connectivity in Render.

Reference: https://render.com/docs/blueprint-spec
