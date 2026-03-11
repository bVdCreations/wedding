FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY main.py .

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.4.1.tgz | tar xz -C /tmp \
    && mv /tmp/docker/docker /usr/local/bin/ \
    && rm -rf /tmp/docker \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
