import base64
import hashlib
import os
import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

import bcrypt
from starlette.testclient import TestClient

from anki_sync_server.mcp.oauth import (
    create_oauth_app,
    generate_jwt_token,
    verify_jwt_token,
    verify_pkce,
)
from anki_sync_server.server.main import app as composite_app


class TestOAuthEndpoints(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-secret-api-key"
        self.hashed_api_key = bcrypt.hashpw(self.api_key.encode("utf-8"), bcrypt.gensalt())
        self.server_secret = "test-server-secret-32-chars-long!"

        self.mock_storage = MagicMock()
        self.mock_storage.get_hashed_api_key.return_value = self.hashed_api_key
        self.mock_storage.get_server_secret_key.return_value = self.server_secret

        self.patcher = patch(
            "anki_sync_server.mcp.oauth.CredentialStorage",
            return_value=self.mock_storage,
        )
        self.patcher.start()

        self.client = TestClient(composite_app)

    def tearDown(self):
        self.patcher.stop()

    def test_pkce_verification(self):
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

        self.assertTrue(verify_pkce(verifier, challenge, "S256"))
        self.assertFalse(verify_pkce("wrong_verifier", challenge, "S256"))
        self.assertTrue(verify_pkce("plain_challenge", "plain_challenge", "plain"))
        self.assertFalse(verify_pkce("plain_challenge", "different_challenge", "plain"))

    def test_authorize_get_renders_html_page(self):
        response = self.client.get(
            "/oauth/authorize",
            params={
                "client_id": "gemini-cli",
                "redirect_uri": "http://localhost:7777/oauth/callback",
                "response_type": "code",
                "state": "random_state_123",
                "scope": "mcp",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Authorize Application", response.text)
        self.assertIn("gemini-cli", response.text)
        self.assertIn("Server API Key", response.text)

    def test_authorize_get_missing_redirect_uri(self):
        response = self.client.get("/oauth/authorize?response_type=code")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_request")

    def test_authorize_get_unsupported_response_type(self):
        response = self.client.get(
            "/oauth/authorize",
            params={
                "client_id": "gemini-cli",
                "redirect_uri": "http://localhost:7777/oauth/callback",
                "response_type": "token",
                "state": "xyz",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("error=unsupported_response_type", response.headers["location"])

    def test_authorize_post_invalid_key_returns_401(self):
        response = self.client.post(
            "/oauth/authorize",
            data={
                "client_id": "gemini-cli",
                "redirect_uri": "http://localhost:7777/oauth/callback",
                "response_type": "code",
                "state": "state123",
                "api_key": "wrong-key",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid Server API key", response.text)

    def test_full_oauth_code_flow_with_pkce(self):
        # 1. Setup PKCE challenge
        verifier = "E9Melhoa2OwvFrGMTJguCH5rtx64JQuqT6ZmuM_Imp6"
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

        # 2. Authorize via POST
        redirect_uri = "http://localhost:7777/oauth/callback"
        auth_response = self.client.post(
            "/oauth/authorize",
            data={
                "client_id": "gemini-cli",
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "state": "client_state_abc",
                "scope": "mcp",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "api_key": self.api_key,
            },
            follow_redirects=False,
        )
        self.assertEqual(auth_response.status_code, 302)
        location = auth_response.headers["location"]
        self.assertTrue(location.startswith(redirect_uri))
        self.assertIn("state=client_state_abc", location)
        self.assertIn("code=", location)

        # Extract code
        import urllib.parse
        parsed = urllib.parse.urlparse(location)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs["code"][0]
        self.assertTrue(len(code) > 10)

        # 3. Exchange code with wrong verifier (should fail)
        bad_token_response = self.client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": "gemini-cli",
                "code_verifier": "wrong-verifier",
            },
        )
        self.assertEqual(bad_token_response.status_code, 400)
        self.assertEqual(bad_token_response.json()["error"], "invalid_grant")

        # Re-authorize to get new code (since previous failed/consumed code)
        auth_response2 = self.client.post(
            "/oauth/authorize",
            data={
                "client_id": "gemini-cli",
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "state": "client_state_abc",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "api_key": self.api_key,
            },
            follow_redirects=False,
        )
        code2 = urllib.parse.parse_qs(urllib.parse.urlparse(auth_response2.headers["location"]).query)["code"][0]

        # 4. Exchange code with valid verifier
        token_response = self.client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code2,
                "redirect_uri": redirect_uri,
                "client_id": "gemini-cli",
                "code_verifier": verifier,
            },
        )
        self.assertEqual(token_response.status_code, 200)
        token_data = token_response.json()
        self.assertEqual(token_data["token_type"], "bearer")
        self.assertEqual(token_data["expires_in"], 3600)
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        self.assertTrue(access_token)
        self.assertTrue(refresh_token)

        # Verify access token works with verify_jwt_token
        decoded = verify_jwt_token(access_token, "access")
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "gemini-cli")

        # 5. Refresh token exchange
        refresh_response = self.client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": "gemini-cli",
            },
        )
        self.assertEqual(refresh_response.status_code, 200)
        new_token_data = refresh_response.json()
        self.assertIn("access_token", new_token_data)
        self.assertIn("refresh_token", new_token_data)

    def test_discovery_endpoints(self):
        for path in ["/.well-known/oauth-authorization-server", "/.well-known/openid-configuration"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("authorization_endpoint", data)
            self.assertIn("token_endpoint", data)
            self.assertIn("response_types_supported", data)
            self.assertIn("code", data["response_types_supported"])
            self.assertIn("S256", data["code_challenge_methods_supported"])

    def test_mcp_dual_authentication(self):
        # Generate valid access token
        access_token = generate_jwt_token("access", ttl=timedelta(hours=1), client_id="test-client")

        with patch("anki_sync_server.mcp.auth.CredentialStorage", return_value=self.mock_storage):
            with TestClient(composite_app) as client:
                # 1. MCP request with OAuth Bearer token
                jwt_response = client.post(
                    "/mcp",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                    },
                )
                # Response should be accepted (200 OK)
                self.assertEqual(jwt_response.status_code, 200)

                # 2. MCP request with static API Key
                key_response = client.post(
                    "/mcp",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                    },
                )
                self.assertEqual(key_response.status_code, 200)

                # 3. MCP request with invalid token
                unauth_response = client.post(
                    "/mcp",
                    headers={
                        "Authorization": "Bearer invalid-token-xyz",
                    },
                    json={"jsonrpc": "2.0", "id": 3, "method": "ping"},
                )
                self.assertEqual(unauth_response.status_code, 401)
                self.assertIn("WWW-Authenticate", unauth_response.headers)
                self.assertIn("Bearer", unauth_response.headers["WWW-Authenticate"])


if __name__ == "__main__":
    unittest.main()
