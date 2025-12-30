FROM python:3.10.12-slim

WORKDIR /app

ADD . /app/

RUN apt-get update && apt-get install -y build-essential

RUN python -m pip install pip --upgrade && \
    pip install --no-cache-dir -r requirements.txt

RUN rm -Rf /root/.cache/pip

RUN apt-get remove -y build-essential && \
    apt-get autoremove -y

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*

RUN mkdir -p /app/data/

CMD uwsgi --http 0.0.0.0:5000 --master -p 4 --lazy-apps -w anki_sync_server.server.main:app
