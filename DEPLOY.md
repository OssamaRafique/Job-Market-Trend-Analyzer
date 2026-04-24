# Deployment Runbook — Fly.io

All four services plus a managed Postgres cluster live on Fly.io in the `iad` region under the
`fantisco` organization (matches the existing [web-api/fly.toml](web-api/fly.toml)).

## Quick start

```bash
# First-time only
./bin/provision.sh

# Every release
./bin/deploy.sh
```

The sections below document what those scripts do in case you want to run the commands by hand.


## Prerequisites

- `flyctl` installed and authenticated (`fly auth login`)
- Fly account with billing set up (Postgres free tier is limited but sufficient)

## 1. Provision the Postgres cluster (one-time)

```bash
fly postgres create \
  --name job-market-trend-analyzer-db \
  --region iad \
  --org fantisco \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1
```

This creates a cluster and prints an internal `DATABASE_URL`. Save it — you'll attach it to each app below.

## 2. Create each Fly app (one-time)

Run each from its service folder:

```bash
# API
cd web-api && fly apps create job-market-trend-analyzer && cd ..

# Collector
cd data-collector && fly apps create job-market-trend-analyzer-collector && cd ..

# Analyzer
cd data-analyzer && fly apps create job-market-trend-analyzer-analyzer && cd ..

# Frontend
cd react-app && fly apps create job-market-trend-analyzer-frontend && cd ..
```

## 3. Attach Postgres to the backend apps (one-time)

```bash
fly postgres attach job-market-trend-analyzer-db --app job-market-trend-analyzer
fly postgres attach job-market-trend-analyzer-db --app job-market-trend-analyzer-collector
fly postgres attach job-market-trend-analyzer-db --app job-market-trend-analyzer-analyzer
```

`fly postgres attach` creates a dedicated DB user per app and injects `DATABASE_URL` as a secret.

## 4. Deploy each service

Each Python service Dockerfile copies both `shared/` and its own folder, so the **build context must
be the project root** (not the service folder). From `code/job-market-trend-analyzer/`:

```bash
fly deploy --config web-api/fly.toml        --dockerfile web-api/Dockerfile        --remote-only
fly deploy --config data-collector/fly.toml --dockerfile data-collector/Dockerfile --remote-only
fly deploy --config data-analyzer/fly.toml  --dockerfile data-analyzer/Dockerfile  --remote-only

# React app builds in its own folder (no shared/ dependency)
cd react-app && fly deploy --remote-only && cd ..
```

## 5. Schedule the collector daily (C-level fallback)

If you want the cron model instead of Phase A queues, point the `[processes]` block in
`data-collector/fly.toml` back at `python collector.py`, remove the `[http_service]` block,
and schedule the machine:

```bash
fly machine run registry.fly.io/job-market-trend-analyzer-collector:latest \
  --schedule daily \
  --app job-market-trend-analyzer-collector

fly machine run registry.fly.io/job-market-trend-analyzer-analyzer:latest \
  --schedule daily \
  --app job-market-trend-analyzer-analyzer
```

## 6. RabbitMQ (Phase A)

The `rabbitmq/` folder deploys `rabbitmq:3-management-alpine` as a fifth Fly app with a
persistent volume. Two helper scripts wrap the provisioning:

```bash
./bin/provision.sh            # creates the rmq app + volume + user/pass secrets
./bin/deploy.sh rabbitmq      # deploys the broker
./bin/share-amqp-url.sh       # copies the AMQP_URL to the three backend apps
```

Once the secret is set, the collector and analyzer boot as always-on consumers (see the
`[processes]` block in their respective `fly.toml`), and the API's `POST /api/refresh` publishes
to the `collect_jobs` queue.

## Manual collector run

```bash
# From the API: publish one `collect_jobs` message (Phase A).
curl -X POST https://job-market-trend-analyzer.fly.dev/api/refresh

# Or SSH in and run the one-shot collector directly.
fly ssh console --app job-market-trend-analyzer-collector -C 'python collector.py'
```

## Smoke test after deploy

```bash
curl https://job-market-trend-analyzer.fly.dev/health
# -> {"status":"healthy"}

curl https://job-market-trend-analyzer.fly.dev/api/categories
# -> ["Software Engineer","Data and Analytics","Data Science",...]
```

## Continuous deployment

`.github/workflows/deploy.yml` deploys all four apps automatically whenever `ci.yml`
succeeds on `main`. To enable it:

1. Generate a deploy token: `fly auth token`
2. In GitHub, add it as a repository secret named `FLY_API_TOKEN`
3. Push to `main`

The workflow runs `flyctl deploy --remote-only` for each app in parallel and then
smoke-tests the API's `/health` and `/api/categories` endpoints before marking the
deploy successful. You can also trigger it manually via the "Run workflow" button
(`workflow_dispatch`).
