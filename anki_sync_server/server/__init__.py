import os

from flask import Flask

from anki_sync_server.anki.anki import Anki
from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.thread import ThreadWithReturnValue
from anki_sync_server.tts.google import GcpTtsService
from anki_sync_server.utils import create_anki_collection

CREDENTIAL_FILE_PATH = os.path.join(os.getcwd(), ".credentials")

if not os.path.join(CREDENTIAL_FILE_PATH):
    raise Exception(
        "Credential file not found. Please run the setup script by running "
        + "`python -m anki_sync_server setup`"
    )


app = Flask(__name__)
CredentialStorage().load(CREDENTIAL_FILE_PATH)
_collection_thread = ThreadWithReturnValue(target=create_anki_collection)
_collection_thread.start()
collection = _collection_thread.join()
tts_service = GcpTtsService(CredentialStorage().get_gcp_tts_api_key())
anki = Anki(collection, tts_service)


@app.route("/")
def home():
    return {"status": "ok"}
