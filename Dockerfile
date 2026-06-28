# Lead Discovery & Enrichment Engine — runtime image (Python 3.11).
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching).
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config

RUN pip install --upgrade pip && pip install .

# Runtime data lives under /app/data and /app/output (mount as volumes).
RUN mkdir -p /app/data /app/output /app/logs

# Default: run a single discovery+enrichment pass. Override as needed, e.g.
#   docker run --rm leadengine list-sources
ENTRYPOINT ["leadengine"]
CMD ["run", "--once"]
