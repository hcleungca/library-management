# 1. Builder Stage
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Copy dependency specifications
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies into virtual environment
RUN uv venv /app/.venv && uv sync --frozen --no-dev --no-install-project

# 2. Runtime Stage
FROM python:3.11-slim AS runtime
WORKDIR /app

# Install curl for healthcheck and libpq runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 && rm -rf /var/lib/apt/lists/*

# Non-root user with home directory for container security and cache access
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV FASTEMBED_CACHE_PATH="/app/.cache/fastembed"

# Copy backend application source and database scripts
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini
COPY backend/scripts /app/scripts

# Pre-create cache dir and ensure appuser ownership
RUN mkdir -p /app/.cache/fastembed && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

