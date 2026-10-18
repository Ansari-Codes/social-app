# Backend Operations And Scaling

## Runtime Layout

The API has three entrypoints:

- `backend.sqliteback.main:app` uses SQLite and is suitable for local development and a single-host deployment.
- `backend.supaback.main:app` uses PostgreSQL through Supabase.
- `backend.neonback.main:app` uses PostgreSQL through Neon.

All use the same FastAPI routes and domain services. Run one backend entrypoint per process. The browser talks only to FastAPI; database credentials stay in `.env` and are never sent to the frontend.

## Supabase Connection Budget

`PostgresDatabase` uses one bounded `psycopg_pool.ConnectionPool` per Python process. Configure it in `.env`:

| Setting | Default | Meaning |
| --- | --- | --- |
| `B_DB_POOL_MIN_SIZE` | `1` | Connections opened when the pool starts. |
| `B_DB_POOL_MAX_SIZE` | `5` | Hard maximum simultaneous PostgreSQL connections for that process. |
| `B_DB_POOL_TIMEOUT_SECONDS` | `5` | Maximum checkout wait before the request fails fast. |
| `B_DB_POOL_MAX_WAITING` | `20` | Maximum queued checkouts waiting for a connection in that process. |

Budget across every worker and replica, not just one command:

```text
maximum app database connections = replicas × Uvicorn workers per replica × pool max size
```

For a provider pool size of 15, a reasonable first deployment could use two workers with pool max size 5, for a total maximum of 10 connections. That leaves capacity for migrations, dashboards, and other clients. Three replicas with one worker each and a pool max size of 3 also use at most 9. Do not set each worker's pool size to 15.

The pooler's **pool size** is the number of actual PostgreSQL server connections. Its **maximum client connections** is how many application clients it can accept; it does not mean all those clients can execute database work simultaneously. Excess checkouts wait in the bounded queue. Once the configured timeout/queue is exceeded, the API returns HTTP `503` with `Retry-After: 1` instead of opening more database connections.

`B_DB_POOL_MAX_SIZE` applies per process. Recalculate it if the number of workers or replicas changes. With `uvicorn --reload`, use one worker; `--reload` is for development, not production. Production should run without `--reload` and use an explicit worker count.

## Query Efficiency

### Feed

`GET /feed/` uses keyset/cursor pagination:

- Default page size: 20 posts.
- Maximum page size: 50.
- Pass `before_id=<next_cursor>` to fetch the next older page.
- The response includes `next_cursor`, which is `null` when there are no more pages.

The cursor uses descending post IDs and the `idx_posts_feed_cursor` index. Each page loads reactions, author profiles, ancestor posts, and recursive comment totals only for that page. It does not scan every post/reaction in the database to render the main feed.

### Threads And Mutations

Single-post reads and thread reads use queries scoped to the requested post/thread. Recursive CTEs walk only the relevant ancestry or descendants. Deleting a post similarly finds only its descendants before removing the thread. Create/read paths do not rebuild the old global posts context cache.

The legacy `/posts/` and `/posts/me` list routes retain their existing full-list response shape. Prefer `/feed/` for the main public stream; cursor pagination for those account-management views can be added separately if those collections become large.

## Migrations

For local development, `B_AUTO_MIGRATE=true` (the default) creates tables, enables RLS, and applies indexes during API startup for either PostgreSQL provider. The schema migration uses a PostgreSQL advisory lock, so concurrent worker startups serialize the migration, and a `schema_migrations` version row makes subsequent startups skip completed DDL.

For production, run the matching provider migration once as a deployment step and disable startup DDL in `.env`:

```dotenv
B_AUTO_MIGRATE=false
```

Then run:

```powershell
python -m backend.supaback.migrate
python -m uvicorn backend.supaback.main:app --port 8000 --workers 2
```

For Neon, run `python -m backend.neonback.migrate` and start `backend.neonback.main:app` instead.

The migration command is safe to re-run. When changing schema in the future, add a new versioned migration and increment `SCHEMA_VERSION` rather than editing an already-applied migration in place.

## Health And Failure Behavior

- `GET /health` is a liveness check; it reports that the process is serving requests.
- `GET /ready` checks out a pooled connection and executes `SELECT 1`; deployment health checks should use this endpoint.
- A broken connection is discarded so the pool can replace it. Idempotent `SELECT`/read CTE operations get at most one retry on a connection error. Writes are not automatically retried because retrying a successful-but-unacknowledged write could duplicate an operation.
- Pool saturation is reported as `503`; clients should retry with backoff and jitter rather than immediately retrying in a tight loop.

## Row-Level Security

Both PostgreSQL schemas enable RLS on the application tables. The FastAPI application connects as the trusted table-owning server role and applies the application's bearer-token authorization. No client-facing database policies are created. Do not put database URIs or secret API keys in an `F_` variable.

## Deployment Checklist

1. Keep `.env` private; use `B_SUPABASE_DB_URL` and `B_SUPABASE_DB_PASS` for Supabase, or `B_NEON_DB_URL` and `B_NEON_DB_PASS` for Neon.
2. For Supabase, use the Session Pooler URI when the runtime cannot reach its IPv6-only direct database endpoint.
3. Set pool sizes from the total worker/replica formula above and keep spare database connections reserved.
4. For PostgreSQL, run `backend.supaback.migrate` or `backend.neonback.migrate` once during deployment; set `B_AUTO_MIGRATE=false` for API workers.
5. Configure explicit `B_CORS_ORIGINS`, HTTPS termination, and a readiness probe to `/ready`.
6. Run without Uvicorn reload in production.
7. Monitor pool timeout/503 rates and query latency before increasing pool sizes. A larger pool is not automatically faster if it exceeds the database's server connection budget.
