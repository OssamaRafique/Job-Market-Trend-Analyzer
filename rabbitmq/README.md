# rabbitmq

Managed RabbitMQ broker for the `collect_jobs` and `analyze_jobs` queues.

## First-time provisioning

```bash
# From the project root:
fly apps create job-market-trend-analyzer-rabbitmq --org fantisco
fly volumes create rabbitmq_data --app job-market-trend-analyzer-rabbitmq --region iad --size 1

# Set admin credentials (used by both the UI and the AMQP URL below).
fly secrets set \
  RABBITMQ_DEFAULT_USER=jmta \
  RABBITMQ_DEFAULT_PASS="$(openssl rand -hex 16)" \
  --app job-market-trend-analyzer-rabbitmq

fly deploy --config rabbitmq/fly.toml --remote-only
```

## Sharing AMQP_URL with the other services

Each sibling app reaches RabbitMQ over the private Fly network at
`job-market-trend-analyzer-rabbitmq.internal`. Pull the creds back out and set
them as a secret on every consumer/producer app:

```bash
AMQP_USER=$(fly secrets list --app job-market-trend-analyzer-rabbitmq | grep RABBITMQ_DEFAULT_USER | awk '{print $2}')
AMQP_PASS=$(fly ssh console --app job-market-trend-analyzer-rabbitmq \
  -C 'printenv RABBITMQ_DEFAULT_PASS')
AMQP_URL="amqp://${AMQP_USER}:${AMQP_PASS}@job-market-trend-analyzer-rabbitmq.internal:5672/%2F"

for app in job-market-trend-analyzer job-market-trend-analyzer-collector job-market-trend-analyzer-analyzer; do
  fly secrets set AMQP_URL="$AMQP_URL" --app "$app"
done
```

## Management UI

Once deployed, the RabbitMQ web UI is available at
`https://job-market-trend-analyzer-rabbitmq.fly.dev/` (basic auth with the
credentials above).
