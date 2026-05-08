FROM python:3.14-slim

# Copy uv binary from the official image — faster and more reliable than pip-installing it
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files first so Docker can cache this layer
# and skip reinstalling packages when only app code changes
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no pytest, httpx, etc.)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and assets
COPY app/ ./app/
COPY assets/ ./assets/

# Install the project itself (registers the app package)
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
