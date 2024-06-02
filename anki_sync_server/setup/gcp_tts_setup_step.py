from getpass import getpass

from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.setup.setup_step import SetupStep


class GcpTtsSetupStep(SetupStep):
    def run(self) -> None:
        api_key = getpass("Enter your Google Cloud Text-to-Speech API key: ")
        CredentialStorage().set_gcp_tts_api_key(api_key)
