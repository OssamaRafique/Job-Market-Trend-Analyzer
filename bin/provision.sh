#!/usr/bin/env bash
# One-shot provisioning script. Run once per Fly org to create all apps +
# Postgres + attach DATABASE_URL to the backend services.
#
# Usage:  ./bin/provision.sh
# Prereq: flyctl installed, `fly auth login` already run.

set -euo pipefail

cd "$(dirname "$0")/.."

ORG="${FLY_ORG:-fantisco}"
REGION="${FLY_REGION:-iad}"
DB_APP="job-market-trend-analyzer-db"
API_APP="job-market-trend-analyzer"
COLLECTOR_APP="job-market-trend-analyzer-collector"
ANALYZER_APP="job-market-trend-analyzer-analyzer"
FRONTEND_APP="job-market-trend-analyzer-frontend"

echo "==> Creating Postgres cluster $DB_APP in $REGION (org=$ORG)"
fly postgres create \
  --name "$DB_APP" \
  --region "$REGION" \
  --org "$ORG" \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1

for app in "$API_APP" "$COLLECTOR_APP" "$ANALYZER_APP" "$FRONTEND_APP"; do
  echo "==> Creating app $app"
  fly apps create "$app" --org "$ORG" || echo "    (already exists)"
done

for app in "$API_APP" "$COLLECTOR_APP" "$ANALYZER_APP"; do
  echo "==> Attaching $DB_APP to $app"
  fly postgres attach "$DB_APP" --app "$app" || echo "    (already attached)"
done

RABBITMQ_APP="job-market-trend-analyzer-rabbitmq"
if [[ "${SKIP_RABBITMQ:-0}" != "1" ]]; then
  echo "==> Creating RabbitMQ app $RABBITMQ_APP (set SKIP_RABBITMQ=1 to skip)"
  fly apps create "$RABBITMQ_APP" --org "$ORG" || echo "    (already exists)"
  fly volumes create rabbitmq_data --app "$RABBITMQ_APP" --region "$REGION" --size 1 --yes \
    || echo "    (volume already exists)"
  PASS="$(openssl rand -hex 16)"
  fly secrets set \
    RABBITMQ_DEFAULT_USER=jmta \
    RABBITMQ_DEFAULT_PASS="$PASS" \
    --app "$RABBITMQ_APP"
  echo "    RabbitMQ password stored as a Fly secret on $RABBITMQ_APP."
  echo "    After ./bin/deploy.sh finishes, run ./bin/share-amqp-url.sh to wire"
  echo "    AMQP_URL into the backend apps."
fi

echo "==> Provisioning complete. Run ./bin/deploy.sh to deploy images."
