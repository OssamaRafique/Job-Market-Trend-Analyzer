# Build context: project root (code/job-market-trend-analyzer/).

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY data-analyzer/requirements.txt /app/data-analyzer/requirements.txt
RUN pip install -r /app/data-analyzer/requirements.txt

COPY shared /app/shared
COPY data-analyzer /app/data-analyzer

WORKDIR /app/data-analyzer

CMD ["python", "analyzer_consumer.py"]
