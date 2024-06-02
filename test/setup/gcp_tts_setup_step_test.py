import unittest
import unittest.mock as mock

from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.setup.gcp_tts_setup_step import GcpTtsSetupStep


class GcpTtsSetupStepTest(unittest.TestCase):
    def test_run(self):
        with mock.patch(
            "anki_sync_server.setup.gcp_tts_setup_step.getpass", return_value="api_key"
        ):
            step = GcpTtsSetupStep()
            step.run()
            self.assertEqual("api_key", CredentialStorage().get_gcp_tts_api_key())


if __name__ == "__main__":
    unittest.main()
