# data-analyzer

Reads recent postings from the `jobs` table, aggregates them by ISO week into `skill_trends` and
`company_trends`, and persists the aggregates via `TrendDataGateway`.

One run is idempotent — existing rows for a given `(skill, week, category)` or
`(company, week, category)` tuple are overwritten via upsert.

## Environment

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | - | Postgres connection string |
| `ANALYZER_WINDOW_DAYS` | no | `28` | How many days of raw jobs to aggregate per run |
| `LOG_LEVEL` | no | `INFO` | |
| `AMQP_URL` | Phase A only | - | RabbitMQ URL for queue mode |

## Local

```bash
docker-compose run --rm analyzer
```

## What it produces

For each job title, the analyzer looks up the set of canonical skills mentioned (see
[aggregations.py](aggregations.py) `KNOWN_SKILLS`) and counts them per ISO week. Rows are written
twice — once with `category=NULL` (global rollup) and once per job `category`, so the API can serve
both the unfiltered and category-filtered chart views without recomputation.

## Production

Scheduled the same way as the collector in C-level. See [../DEPLOY.md](../DEPLOY.md).
