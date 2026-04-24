# web-api

Flask REST API serving aggregated trends and raw jobs to the Next.js dashboard. Never writes to the
database directly — delegates all reads to `JobDataGateway` / `TrendDataGateway` from `shared/`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check (Fly + smoke tests) |
| GET | `/metrics` | Prometheus-format metrics (expanded in b4-monitoring) |
| GET | `/api/categories` | Distinct job categories in the DB |
| GET | `/api/trends/skills?weeks=N&category=...` | Skill trend rows |
| GET | `/api/trends/companies?weeks=N&category=...` | Company trend rows |
| GET | `/api/jobs?category=&level=&location=&limit=25&offset=0` | Paginated raw jobs |
| POST | `/api/refresh` | Publish a `collect_jobs` AMQP message (Phase A) |

JSON shapes match [../react-app/lib/types.ts](../react-app/lib/types.ts).

## Environment

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | - | Postgres connection string |
| `CORS_ORIGINS` | no | `*` | Comma-separated allow-list for `/api/*` |
| `AMQP_URL` | Phase A only | - | RabbitMQ URL for `/api/refresh` |
| `PORT` | no | `8080` | HTTP port |

## Local

```bash
docker-compose up web-api
# then
curl http://localhost:8080/health
curl http://localhost:8080/api/categories
```

## Production

See [../DEPLOY.md](../DEPLOY.md). Deployed as Fly app `job-market-trend-analyzer`; health check
hits `/health` every 30s.
