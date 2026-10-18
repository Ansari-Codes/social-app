# DotMuted

![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f.svg)](LICENSE)

DotMuted is a Vue 3 and TypeScript application with three interchangeable FastAPI backends: local SQLite, Supabase PostgreSQL, and Neon PostgreSQL. All backends implement the same HTTP routes and response envelope; the frontend only needs its configured backend URL.

## Requirements

- Node.js 22.12 or newer and npm
- Python 3.10 or newer
- A Supabase or Neon project and its PostgreSQL connection URI when using a hosted database backend

## Configuration

Create one local environment file from the example:

```powershell
Copy-Item .env.example .env
```

`.env` is ignored by Git. Backend variables use the `B_` prefix and frontend variables use `F_`. Vite reads only the `F_` values and embeds only the app name and backend URL; backend settings and credentials stay server-side.

### Backend variables

| Setting | Default | Purpose |
| --- | --- | --- |
| `B_BACKEND` | `sqlite` | Backend runner selection: `sqlite`, `supabase`, or `neon`. |
| `B_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated, explicit frontend origins. Wildcards and URL paths are rejected. |
| `B_SQLITE_DB_PATH` | `AppData/db.sqlite` | SQLite file path; relative paths resolve from the repository root. |
| `B_SESSION_LIFETIME_DAYS` | `7` | Lifetime for newly issued login sessions; must be positive. |
| `B_SUPABASE_DB_URL` / `B_SUPABASE_DB_PASS` | Unset | Supabase PostgreSQL URI and optional `{pass}` substitution password. |
| `B_NEON_DB_URL` / `B_NEON_DB_PASS` | Unset | Neon PostgreSQL URI and optional `{pass}` substitution password. |
| `B_DB_POOL_MIN_SIZE` | `1` | Minimum PostgreSQL connections per API process. |
| `B_DB_POOL_MAX_SIZE` | `5` | Maximum PostgreSQL connections per process. Budget across workers and replicas. |
| `B_DB_POOL_TIMEOUT_SECONDS` | `5` | Maximum time a request waits for a pooled connection. |
| `B_DB_POOL_MAX_WAITING` | `20` | Maximum queued connection checkouts per process. |
| `B_AUTO_MIGRATE` | `true` | Run the versioned PostgreSQL migration at startup. Disable in production and migrate once during deployment. |
| `B_SLOW_REQUEST_LOG_MS` | `750` | Log slow requests without query strings or request bodies. |

Configure the provider-specific PostgreSQL settings in `.env`. For Supabase, use a database URI from the project's **Connect** settings (a session-pooler URI is a good default for IPv4 networks):

```dotenv
B_SUPABASE_DB_URL=postgresql://postgres.<project-ref>:[{pass}]@<pooler-host>:5432/postgres
B_SUPABASE_DB_PASS=your-database-password
```

For Neon, copy the PostgreSQL connection URI from the Neon console and set `B_NEON_DB_URL` and `B_NEON_DB_PASS`. Do not use provider API URLs, publishable keys, or secret API keys as database credentials.

### Frontend variables

```dotenv
F_APP_NAME=DotMuted
F_BACKEND_URL=http://127.0.0.1:8000
F_BASE_PATH=/
```

`F_APP_NAME` sets the browser title and visible brand. `F_BACKEND_URL` is the API origin, without a trailing slash. `F_BASE_PATH` defaults to `/`; the Pages workflow sets the correct root or repository path automatically. Production builds require `F_BACKEND_URL`.

## Local Development

Install dependencies and create the Python environment:

```powershell
npm ci
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start exactly one backend in a terminal:

```powershell
# SQLite
python -m uvicorn backend.sqliteback.main:app --reload --port 8000

# Or Supabase PostgreSQL
python -m uvicorn backend.supaback.main:app --reload --port 8000

# Or Neon PostgreSQL
python -m uvicorn backend.neonback.main:app --reload --port 8000
```

For production PostgreSQL deploys, run the provider's migration once before starting API workers, then set `B_AUTO_MIGRATE=false`:

```powershell
python -m backend.supaback.migrate
python -m uvicorn backend.supaback.main:app --port 8000 --workers 2
```

For Neon, use `python -m backend.neonback.migrate` and `backend.neonback.main:app` instead.

Budget database connections across every process: `replicas × workers × B_DB_POOL_MAX_SIZE`. Pool exhaustion waits up to `B_DB_POOL_TIMEOUT_SECONDS`, then returns HTTP `503` with `Retry-After`.

Start the Vue development server in another terminal:

```powershell
npm run dev
```

Vite prints the local frontend URL. The default `F_BACKEND_URL` points to the local API at `http://127.0.0.1:8000`.

## Build And Preview

Create the production frontend bundle:

```powershell
npm run build
```

The command runs `vue-tsc -b` followed by `vite build`; generated files are written to `dist/`. Frontend config is embedded at build time, and `dist/404.html` supports static-host fallback paths.

Preview the generated bundle locally:

```powershell
npm run preview
```

## Deployment

### GitHub Pages frontend

1. In the GitHub repository, open **Settings → Pages** and select **GitHub Actions** as the deployment source.
2. Open **Settings → Secrets and variables → Actions → Variables** and add `F_BACKEND_URL` with the Render API origin, for example `https://dotmuted-api.onrender.com` (no trailing slash).
3. Push to `main` or run the **Deploy frontend to GitHub Pages** workflow manually. The workflow calculates the correct base path for project sites and `username.github.io` user sites.

The production router uses hash URLs, so refreshing a nested route works on static hosting. The generated `404.html` also serves the app shell for older/direct history-style links. If your default branch is not `main`, update the workflow trigger.

### Render backend

1. Create a Neon PostgreSQL database, then create a Render Blueprint from this repository using [render.yaml](render.yaml). It starts the Neon backend by default.
2. Set `B_NEON_DB_URL` and `B_NEON_DB_PASS` in Render. Use a PostgreSQL connection URI with `{pass}` where the password belongs, and the database password as the separate value.
3. Set `B_CORS_ORIGINS` to the frontend **origin**, for example `https://username.github.io`. Do not append the project path such as `/silence/`. For a custom Pages domain, use that domain's origin instead.
4. Copy the Render service origin into the GitHub Actions variable `F_BACKEND_URL` and deploy the frontend workflow.

The Render blueprint uses `B_BACKEND=neon`, automatic versioned migrations, one Uvicorn process, and `/health`. To use Supabase instead, switch `B_BACKEND` to `supabase` and configure `B_SUPABASE_DB_URL` / `B_SUPABASE_DB_PASS`. SQLite on Render requires a persistent disk; its default filesystem is ephemeral. Render's free web services may sleep between requests, causing a cold-start delay.

The Python API is deployed separately. Keep database credentials in Render or another backend host, not GitHub Pages variables. Never expose database credentials or secret API keys through frontend config.

## Tests And Checks

Run all backend test suites:

```powershell
npm test
```

Run one suite directly when iterating:

```powershell
npm run test:sqliteback
npm run test:supaback
npm run test:neonback
```

Check the frontend build and dependency audit:

```powershell
npm run build
npm audit
```

## Backend Details

- `backend.sqliteback.main:app` uses SQLite and stores its database at `B_SQLITE_DB_PATH`.
- `backend.supaback.main:app` uses the shared PostgreSQL adapter with Supabase credentials.
- `backend.neonback.main:app` uses the same PostgreSQL adapter with Neon credentials.
- PostgreSQL migrations are provider-specific entrypoints under `backend.supaback.migrate` and `backend.neonback.migrate`.
- PostgreSQL connections use a bounded per-process pool; `/health` is liveness and `/ready` checks database readiness.
- `GET /feed/` returns 20 posts by default, accepts `limit` (up to 50) and `before_id`, and returns `next_cursor` for the next page.
- Feed, single-post, and thread reads are scoped to a page or thread; mutation requests remain authenticated.
- All three apps expose the same users, sessions, profiles, posts, feed, notifications, and analytics APIs.
- The Supabase app uses the existing FastAPI bearer-token authorization. Client-role access through the Supabase Data API has no policies and is denied by default.
- Run one backend entrypoint per process; the route and service modules are shared.
- See [docs/technical.md](docs/technical.md) for pool budgeting, migrations, pagination, and operations guidance.

## Security Notes

- Passwords use salted PBKDF2-HMAC-SHA256. Bearer session tokens are stored as SHA-256 digests.
- The browser stores tokens in `sessionStorage` by default; “Remember me” uses `localStorage`.
- Use explicit CORS origins. Do not use `*` with credentials.
- Never commit `.env`. Rotate any API key or database password that has been exposed.
- Put login rate limiting and TLS termination at a trusted reverse proxy.

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
