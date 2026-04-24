# data-collector

Fetches job postings from [The Muse API](https://www.themuse.com/developers/api/v2) and persists them
to Postgres via `JobDataGateway`. One invocation = one collection run.

## Environment

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | - | Postgres connection string |
| `COLLECTOR_CATEGORIES` | no | `Software Engineer,Data and Analytics,Data Science,DevOps and Sysadmin` | Comma-separated list |
| `COLLECTOR_PAGES` | no | `5` | Pages to fetch per category |
| `MUSE_API_URL` | no | `https://www.themuse.com/api/public/jobs` | Override for testing |
| `LOG_LEVEL` | no | `INFO` | |
| `AMQP_URL` | Phase A only | - | RabbitMQ URL when running as a queue consumer |

## Local (via docker-compose from the project root)

```bash
docker-compose run --rm collector
```

## Production (Fly.io)

Image is built with **project root** as the build context so it can pull in `shared/`. The daily schedule
is managed by a Fly Machine (`fly machine run --schedule daily`). See [../DEPLOY.md](../DEPLOY.md).

Manual on-demand run:

```bash
fly ssh console --app job-market-trend-analyzer-collector -C 'python collector.py'
```

## Layout

```
data-collector/
  collector.py       one-shot entrypoint
  muse_client.py     requests wrapper (mocked in tests)
  collector_consumer.py  Phase A entrypoint (subscribes to collect_jobs)
  tests/             pytest
  Dockerfile         built with context = project root
  fly.toml
  requirements.txt
```
