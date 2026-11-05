FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen || uv sync --no-dev
COPY services/api ./services/api
CMD ["uv", "run", "uvicorn", "main:app", "--app-dir", "services/api", "--host", "0.0.0.0", "--port", "8001"]
