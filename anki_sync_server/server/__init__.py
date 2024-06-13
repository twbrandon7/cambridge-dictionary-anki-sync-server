import os

from anki_sync_server.anki.anki import Anki
from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.thread import ThreadWithReturnValue
from anki_sync_server.tts.google import GcpTtsService
from anki_sync_server.utils import create_anki_collection

CREDENTIAL_FILE_PATH = os.path.join(os.getcwd(), "data", ".credentials")

if not os.path.exists(CREDENTIAL_FILE_PATH):
    raise Exception(
        "Credential file not found. Please run the setup script by running "
        + "`python -m anki_sync_server setup`"
    )

print("Loading credentials from", CREDENTIAL_FILE_PATH)
CredentialStorage().load(CREDENTIAL_FILE_PATH)

print("Creating Anki collection")
_collection_thread = ThreadWithReturnValue(target=create_anki_collection)
_collection_thread.start()
collection = _collection_thread.join()

print("Loading Anki wrapper")
tts_service = GcpTtsService(CredentialStorage().get_gcp_tts_api_key())
anki = Anki(collection, tts_service)
