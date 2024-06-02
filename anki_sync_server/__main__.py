import os
from argparse import ArgumentParser

from anki._backend import RustBackend
from anki.collection import Collection

from anki_sync_server.setup.anki_session_setup_step import AnkiSessionSetupStep
from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.setup.gcp_tts_setup_step import GcpTtsSetupStep
from anki_sync_server.setup.server_api_key_setup_step import ServerApiKeySetupStep
from anki_sync_server.setup.setup_wizard import SetupWizard
from anki_sync_server.thread import ThreadWithReturnValue

def _create_collection() -> Collection:
    data_dir = os.path.join(os.getcwd(), "data")
    return Collection(
        os.path.join(data_dir, "collection.anki2"),
        backend=RustBackend(langs=["en"]),
    )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=["setup"])
    args = parser.parse_args()

    if args.action == "setup":
        collection_thread = ThreadWithReturnValue(target=_create_collection)
        collection_thread.start()
        collection = collection_thread.join()
        wizard = SetupWizard()
        wizard.append(AnkiSessionSetupStep(collection))
        wizard.append(GcpTtsSetupStep())
        wizard.append(ServerApiKeySetupStep())
        wizard.run_all()
        CredentialStorage().save()
