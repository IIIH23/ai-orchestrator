# syntax=docker/dockerfile:1
FROM python:3.14-slim AS builder
WORKDIR /build
COPY requirements*.txt ./ 2>/dev/null || true
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt 2>/dev/null || true
RUN pip install --no-cache-dir --prefix=/install -r requirements-dev.txt 2>/dev/null || true

FROM python:3.14-slim AS runtime
RUN groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git curl jq ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY --chown=app:app . .
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
USER app
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import sys; sys.exit(0)" || exit 1
CMD ["python", "tools/inventory.py"]
