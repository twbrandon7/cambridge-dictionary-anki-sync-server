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

CMD ["uv", "run", "uwsgi", "--http", "0.0.0.0:5000", "--master", "-p", "4", "--lazy-apps", "-w", "anki_sync_server.server.main:app"]
