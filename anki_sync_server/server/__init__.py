import os
from threading import Lock

from anki_sync_server import CREDENTIAL_FILE_PATH
from anki_sync_server.anki.anki import Anki
from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.thread import ThreadWithReturnValue
from anki_sync_server.tts.google import GcpTtsService
from anki_sync_server.utils import create_anki_collection

if not os.path.exists(CREDENTIAL_FILE_PATH):
    raise Exception(
        "Credential file not found. Please run the setup script by running "
        + "`python -m anki_sync_server setup`"
    )

print("Loading credentials from", CREDENTIAL_FILE_PATH)
CredentialStorage().load(CREDENTIAL_FILE_PATH)

# Lazy initialization to support multi-process workers
_anki = None
_anki_lock = Lock()


def _get_anki():
    """Get or create the Anki instance (lazy initialization for multi-process support)."""
    global _anki
    if _anki is None:
        with _anki_lock:
            # Double-check locking pattern
            if _anki is None:
                print("Creating Anki collection")
                _collection_thread = ThreadWithReturnValue(target=create_anki_collection)
                _collection_thread.start()
                collection = _collection_thread.join()
                
                print("Loading Anki wrapper")
                tts_service = GcpTtsService(CredentialStorage().get_gcp_tts_api_key())
                _anki = Anki(collection, tts_service)
    return _anki


# Provide a property-like access pattern for backwards compatibility
class _AnkiProxy:
    """Proxy object that provides lazy initialization of the Anki instance."""
    
    def __getattr__(self, name):
        return getattr(_get_anki(), name)


anki = _AnkiProxy()
