import secrets

import bcrypt

from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.setup.setup_step import SetupStep


class ServerApiKeySetupStep(SetupStep):
    def run(self) -> None:
        api_key = secrets.token_urlsafe(32)
        server_secret_key = secrets.token_urlsafe(32)
        CredentialStorage().set_hashed_api_key(
            bcrypt.hashpw(api_key.encode(), bcrypt.gensalt())
        )
        CredentialStorage().set_server_secret_key(server_secret_key)
        print(f"Server API key: {api_key}")
