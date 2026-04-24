# Job Market Trend Analyzer

Collects job postings from [The Muse API](https://www.themuse.com/developers/api/v2) daily, aggregates them into skill and company trends, and serves the results through a REST API consumed by a Next.js dashboard.

## Architecture

```
Next.js dashboard (react-app)
        |  REST JSON
        v
Flask API (web-api)  ---- reads ----> Postgres <---- writes ---- Data Analyzer (data-analyzer)
                                         ^
                                         |  writes raw jobs
                                Data Collector (data-collector)
                                         |
                                         v
                                The Muse API
```

Phase A adds a RabbitMQ broker with two durable queues between the services so the API can trigger
collection on demand and the analyzer runs immediately after each successful collection:

| Queue | Published by | Consumed by |
|---|---|---|
| `collect_jobs` | `web-api` (`POST /api/refresh`) | `data-collector` (`collector_consumer.py`) |
| `analyze_jobs` | `data-collector` after each run | `data-analyzer` (`analyzer_consumer.py`) |

Messages are persisted (`delivery_mode=2`) on durable queues with `auto_ack=False`, so a consumer
crash re-delivers the message after restart.

## Folders

| Folder | Role |
|---|---|
| `react-app/` | Next.js 16 dashboard (built) |
| `web-api/` | Flask REST API (JSON) |
| `data-collector/` | Python worker that calls The Muse API and inserts raw jobs |
| `data-analyzer/` | Python worker that aggregates raw jobs into skill and company trends |
| `shared/` | SQLAlchemy models and the Data Gateway shared by all Python services |

## Local development

```bash
cp .env.example .env
docker-compose up -d postgres
docker-compose run --rm collector
docker-compose up web-api
# In another terminal:
cd react-app && pnpm install && pnpm dev
```

Visit:
- API: http://localhost:8080/api/categories
- Dashboard: http://localhost:3000

## Deployment

All backend services deploy to Fly.io as separate apps that share a managed `DATABASE_URL`
(and, in Phase A, a shared `AMQP_URL`). Details in each service's own README.
