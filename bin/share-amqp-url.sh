#!/usr/bin/env bash
# Propagate AMQP_URL from the RabbitMQ app to the backend apps that need it.

set -euo pipefail

RABBITMQ_APP="job-market-trend-analyzer-rabbitmq"
CONSUMERS=(
  "job-market-trend-analyzer"
  "job-market-trend-analyzer-collector"
  "job-market-trend-analyzer-analyzer"
)

AMQP_USER="jmta"
AMQP_PASS="$(fly ssh console --app "$RABBITMQ_APP" -C 'printenv RABBITMQ_DEFAULT_PASS' | tr -d '\r\n')"

if [[ -z "$AMQP_PASS" ]]; then
  echo "Could not read RABBITMQ_DEFAULT_PASS from $RABBITMQ_APP." >&2
  exit 1
fi

AMQP_URL="amqp://${AMQP_USER}:${AMQP_PASS}@${RABBITMQ_APP}.internal:5672/%2F"

for app in "${CONSUMERS[@]}"; do
  echo "==> Setting AMQP_URL on $app"
  fly secrets set AMQP_URL="$AMQP_URL" --app "$app"
done

echo "==> AMQP_URL is now wired to all consumer/producer apps."
