from flask import Flask
from flask_cors import CORS

from anki_sync_server.server.api_v1 import bp
from anki_sync_server.tasks.celery_app import celery_app

app = Flask(__name__)
CORS(app)

# Initialize Celery app with Flask
celery_app.conf.update(app.config)


@app.route("/")
def home():
    return {"status": "ok"}


app.register_blueprint(bp, url_prefix="/api/v1")
