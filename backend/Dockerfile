# ── Stage 1: build + install deps ─────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies (cached layer — only re-runs when lock file changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy source and install the project
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ── Stage 2: runtime image ─────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

# Non-root user
RUN groupadd -r appgroup \
    && useradd -r -g appgroup -u 1001 appuser

WORKDIR /app

# Copy only what's needed from the builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "document_processor.main:app", "--host", "0.0.0.0", "--port", "8000"]
