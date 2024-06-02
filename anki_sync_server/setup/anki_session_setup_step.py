from anki.collection import Collection
from anki.errors import SyncError
from anki.sync import SyncAuth

from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.setup.setup_step import SetupStep
from anki_sync_server.thread import ThreadWithReturnValue


class AnkiSessionSetupStep(SetupStep):
    def __init__(self, collection: Collection):
        self._collection = collection

    def _run(self) -> SyncAuth:
        auth = None
        while auth is None:
            username = input("Enter your AnkiWeb username: ")
            password = input("Enter your AnkiWeb password: ")
            try:
                auth = self._collection.sync_login(
                    username, password, "https://sync.ankiweb.net"
                )
            except SyncError as e:
                print(f"Failed to log in: {e}")
        return auth

    def run(self) -> None:
        login_thread = ThreadWithReturnValue(target=self._run)
        login_thread.start()
        auth = login_thread.join()
        CredentialStorage().set_anki_session(auth)
