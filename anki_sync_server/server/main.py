from flask import Flask
from flask_cors import CORS

from anki_sync_server.server.api_v1 import bp

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return {"status": "ok"}


app.register_blueprint(bp, url_prefix="/api/v1")
