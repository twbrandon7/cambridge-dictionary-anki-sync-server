import tempfile
import unittest

from anki_sync_server.setup.credential_storage import CredentialStorage


class CredentialStorageTest(unittest.TestCase):
    def setUp(self):
        CredentialStorage._instance = None

    def test_get_anki_session(self):
        credential_storage = CredentialStorage()
        self.assertIsNone(credential_storage.get_anki_session())

    def test_get_gcp_tts_api_key(self):
        credential_storage = CredentialStorage()
        self.assertIsNone(credential_storage.get_gcp_tts_api_key())

    def test_get_hashed_api_key(self):
        credential_storage = CredentialStorage()
        self.assertIsNone(credential_storage.get_hashed_api_key())

    def test_get_server_secret_key(self):
        credential_storage = CredentialStorage()
        self.assertIsNone(credential_storage.get_server_secret_key())

    def test_get_refresh_token_created_at(self):
        credential_storage = CredentialStorage()
        self.assertIsNone(credential_storage.get_refresh_token_created_at())

    def test_set_anki_session(self):
        credential_storage = CredentialStorage()
        credential_storage.set_anki_session("session")
        self.assertEqual("session", credential_storage.get_anki_session())

    def test_set_gcp_tts_api_key(self):
        credential_storage = CredentialStorage()
        credential_storage.set_gcp_tts_api_key("api_key1")
        self.assertEqual("api_key1", credential_storage.get_gcp_tts_api_key())

    def test_set_hashed_api_key(self):
        credential_storage = CredentialStorage()
        credential_storage.set_hashed_api_key(b"api_key2")
        self.assertEqual(b"api_key2", credential_storage.get_hashed_api_key())

    def test_set_server_secret_key(self):
        credential_storage = CredentialStorage()
        credential_storage.set_server_secret_key("server_secret")
        self.assertEqual("server_secret", credential_storage.get_server_secret_key())

    def test_set_refresh_token_created_at(self):
        credential_storage = CredentialStorage()
        credential_storage.set_refresh_token_created_at(123456)
        self.assertEqual(123456, credential_storage.get_refresh_token_created_at())

    def test_save_and_load(self):
        credential_storage = CredentialStorage()
        credential_storage.set_anki_session("session")
        credential_storage.set_gcp_tts_api_key("api_key1")
        credential_storage.set_hashed_api_key("api_key2")

        with tempfile.TemporaryDirectory() as tmpdirname:
            credential_storage.save(tmpdirname + "/.credentials")
            credential_storage.set_anki_session(None)
            credential_storage.set_gcp_tts_api_key(None)
            credential_storage.set_hashed_api_key(None)
            credential_storage.load(tmpdirname + "/.credentials")

            self.assertEqual("session", credential_storage.get_anki_session())
            self.assertEqual("api_key1", credential_storage.get_gcp_tts_api_key())
            self.assertEqual("api_key2", credential_storage.get_hashed_api_key())


if __name__ == "__main__":
    unittest.main()
