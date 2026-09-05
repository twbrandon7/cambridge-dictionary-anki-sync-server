FROM python:3.10.12-slim

RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ADD . /app/

RUN uv sync

RUN mkdir -p /app/data/

CMD ["uv", "run", "uvicorn", "anki_sync_server.server.main:app", "--host", "0.0.0.0", "--port", "5000"]
