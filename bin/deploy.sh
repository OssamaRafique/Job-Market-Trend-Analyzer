#!/usr/bin/env bash
# Deploy all four Fly apps. Runs from the project root so each Python service
# Dockerfile can reach the shared/ package via the monorepo build context.
#
# Usage:  ./bin/deploy.sh          # deploy everything
#         ./bin/deploy.sh web-api  # deploy a single service

set -euo pipefail

cd "$(dirname "$0")/.."

deploy_web_api() {
  echo "==> Deploying web-api"
  fly deploy --config web-api/fly.toml --dockerfile web-api/Dockerfile --remote-only
}

deploy_collector() {
  echo "==> Deploying data-collector"
  fly deploy --config data-collector/fly.toml --dockerfile data-collector/Dockerfile --remote-only
}

deploy_analyzer() {
  echo "==> Deploying data-analyzer"
  fly deploy --config data-analyzer/fly.toml --dockerfile data-analyzer/Dockerfile --remote-only
}

deploy_frontend() {
  echo "==> Deploying react-app"
  (cd react-app && fly deploy --remote-only)
}

deploy_rabbitmq() {
  echo "==> Deploying rabbitmq"
  fly deploy --config rabbitmq/fly.toml --remote-only
}

smoke_test() {
  echo "==> Smoke-testing API"
  curl -fsS https://job-market-trend-analyzer.fly.dev/health | jq .
}

target="${1:-all}"
case "$target" in
  web-api)        deploy_web_api ;;
  collector)      deploy_collector ;;
  analyzer)       deploy_analyzer ;;
  frontend)       deploy_frontend ;;
  rabbitmq)       deploy_rabbitmq ;;
  all)
    if [[ "${SKIP_RABBITMQ:-0}" != "1" ]]; then
      deploy_rabbitmq
    fi
    deploy_web_api
    deploy_collector
    deploy_analyzer
    deploy_frontend
    smoke_test
    ;;
  *)
    echo "Unknown target: $target" >&2
    echo "Valid: web-api | collector | analyzer | frontend | rabbitmq | all" >&2
    exit 1
    ;;
esac
