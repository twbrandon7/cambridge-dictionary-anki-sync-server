import unittest
import unittest.mock as mock

import bcrypt

from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.setup.server_api_key_setup_step import ServerApiKeySetupStep


class ServerApiKeySetupStepTest(unittest.TestCase):
    def test_run(self):
        step = ServerApiKeySetupStep()
        with mock.patch(
            "anki_sync_server.setup.server_api_key_setup_step.secrets.token_urlsafe",
            side_effect=["api_key", "server_key"],
        ):
            step.run()
            self.assertTrue(
                bcrypt.checkpw(
                    "api_key".encode(),
                    CredentialStorage().get_hashed_api_key(),
                )
            )
            self.assertEqual("server_key", CredentialStorage().get_server_secret_key())


if __name__ == "__main__":
    unittest.main()
