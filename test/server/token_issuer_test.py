import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from anki_sync_server.server.token_issuer import TokenIssuer
from anki_sync_server.setup.credential_storage import CredentialStorage


class TestTokenIssuer(unittest.TestCase):
    def setUp(self):
        self.secret_key = "test_secret"
        self.token_ttl = timedelta(minutes=5)
        self.issuer = TokenIssuer(self.secret_key)

    def test_issue_access_token(self):
        token = self.issuer.issue("access", self.token_ttl)
        self.assertIsInstance(token, str)

    def test_issue_refresh_token(self):
        token = self.issuer.issue("refresh", self.token_ttl)
        self.assertIsInstance(token, str)

    def test_verify_valid_token(self):
        token = self.issuer.issue("access", self.token_ttl)
        is_valid, error = self.issuer.verify(token, "access")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @patch("anki_sync_server.server.token_issuer.datetime")
    def test_verify_expired_token(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1)
        token = self.issuer.issue("access", self.token_ttl)
        mock_datetime.now.return_value = datetime(2022, 12, 31)
        is_valid, error = self.issuer.verify(token, "access")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Token has expired")

    def test_verify_invalid_token(self):
        token = "invalid_token"
        is_valid, error = self.issuer.verify(token, "access")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Invalid token")

    def test_verify_invalid_issuer(self):
        with patch("anki_sync_server.server.token_issuer.APP_NAME", "RealApp"):
            token = self.issuer.issue("access", self.token_ttl)
        with patch("anki_sync_server.server.token_issuer.APP_NAME", "FakeApp"):
            is_valid, error = self.issuer.verify(token, "access")
            self.assertFalse(is_valid)
            self.assertEqual(error, "Invalid token")

    def test_verify_invalid_type(self):
        token = self.issuer.issue("access", self.token_ttl)
        is_valid, error = self.issuer.verify(token, "refresh")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Invalid token")

    def test_verify_refresh_token(self):
        token = self.issuer.issue("refresh", self.token_ttl)
        is_valid, error = self.issuer.verify(token, "refresh")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_verify_refresh_token_created_at(self):
        token = self.issuer.issue("refresh", self.token_ttl)
        CredentialStorage().set_refresh_token_created_at(None)
        is_valid, error = self.issuer.verify(token, "refresh")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Invalid token")


if __name__ == "__main__":
    unittest.main()
