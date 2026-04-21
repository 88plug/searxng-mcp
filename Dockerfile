FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SEARXNG_MCP_RENDER_BROWSER_PATH=/usr/bin/chromium

RUN apt-get update && \
    apt-get install -y --no-install-recommends chromium && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir .

EXPOSE 8811

ENTRYPOINT ["searxng-mcp"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8811"]
