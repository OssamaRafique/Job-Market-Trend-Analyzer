# Build context is the project root (code/job-market-trend-analyzer/), so we can
# copy both the service folder and the shared/ package into the same image.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY data-collector/requirements.txt /app/data-collector/requirements.txt
RUN pip install -r /app/data-collector/requirements.txt

COPY shared /app/shared
COPY data-collector /app/data-collector

WORKDIR /app/data-collector

CMD ["python", "collector_consumer.py"]
