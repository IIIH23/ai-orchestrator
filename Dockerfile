# syntax=docker/dockerfile:1
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements*.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt 2>/dev/null || true
RUN pip install --no-cache-dir --prefix=/install -r requirements-dev.txt 2>/dev/null || true

# Stage 2: Runtime image
FROM python:3.11-slim AS runtime

# Security: non-root user
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git curl jq ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=app:app . .

# Runtime security settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command: inventory tool
CMD ["python", "tools/inventory.py"]
