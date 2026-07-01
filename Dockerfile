# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m pip install \
    --no-cache-dir \
    --disable-pip-version-check \
    --prefix=/install \
    -r requirements.txt

FROM python:3.12-slim AS runtime

RUN groupadd --system orchestrator \
    && useradd --system --gid orchestrator --home /app orchestrator

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=orchestrator:orchestrator orchestrator_api ./orchestrator_api
COPY --chown=orchestrator:orchestrator projects ./projects

ENV ORCHESTRATOR_ENV=production \
    ORCHESTRATOR_PORT=8080 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER orchestrator
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-m", "orchestrator_api.healthcheck"]

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--access-logfile", "-", "orchestrator_api.app:create_app()"]
