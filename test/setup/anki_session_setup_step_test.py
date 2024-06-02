import unittest
import unittest.mock as mock

from anki.collection import Collection

from anki_sync_server.setup.anki_session_setup_step import AnkiSessionSetupStep
from anki_sync_server.setup.credential_storage import CredentialStorage


class TestAnkiSessionSetupStep(unittest.TestCase):
    def test_run(self):
        with mock.patch("builtins.input", side_effect=["username", "password"]):
            collection = mock.Mock(spec=Collection)
            collection.sync_login.return_value = "auth"
            step = AnkiSessionSetupStep(collection)
            step.run()
            collection.sync_login.assert_called_once_with(
                "username", "password", "https://sync.ankiweb.net"
            )
            self.assertEqual("auth", CredentialStorage().get_anki_session())


if __name__ == "__main__":
    unittest.main()
