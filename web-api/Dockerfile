# Build context: project root (code/job-market-trend-analyzer/).

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    PORT=8080

WORKDIR /app

COPY web-api/requirements.txt /app/web-api/requirements.txt
RUN pip install -r /app/web-api/requirements.txt

COPY shared /app/shared
COPY web-api /app/web-api

WORKDIR /app/web-api

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "src.app:app"]
