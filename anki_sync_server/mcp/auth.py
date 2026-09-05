import urllib.parse
from typing import Callable, Optional, Set

import bcrypt
from starlette.responses import JSONResponse

from anki_sync_server.mcp.oauth import verify_jwt_token
from anki_sync_server.setup.credential_storage import CredentialStorage


class ApiKeyAuthMiddleware:
    """
    ASGI middleware that validates requests against either:
    1. A valid OAuth 2.0 Bearer JWT access token
    2. The server's hashed API key
    Supports credentials via:
    - Authorization: Bearer <token_or_key>
    - Authorization: <key>
    - X-API-Key: <key>
    - Query parameter: ?api_key=<key> or ?key=<key>
    """

    def __init__(
        self,
        app,
        credential_storage_getter: Optional[Callable[[], CredentialStorage]] = None,
    ):
        self.app = app
        self._credential_storage_getter = credential_storage_getter or (
            lambda: CredentialStorage()
        )
        self._valid_keys_cache: Set[str] = set()

    def _extract_credential(self, scope: dict) -> Optional[str]:
        headers = dict(scope.get("headers", []))

        auth_header = headers.get(b"authorization", b"").decode("utf-8").strip()
        if auth_header:
            if auth_header.startswith("Bearer "):
                return auth_header[7:].strip()
            return auth_header

        x_api_key = headers.get(b"x-api-key", b"").decode("utf-8").strip()
        if x_api_key:
            return x_api_key

        query = scope.get("query_string", b"").decode("utf-8")
        if query:
            params = urllib.parse.parse_qs(query)
            if "api_key" in params and params["api_key"]:
                return params["api_key"][0].strip()
            if "key" in params and params["key"]:
                return params["key"][0].strip()

        return None

    def _verify_credential(self, token_or_key: str) -> bool:
        if token_or_key in self._valid_keys_cache:
            return True

        # 1. Attempt OAuth 2.0 Bearer JWT validation
        decoded = verify_jwt_token(token_or_key, expected_type="access")
        if decoded is not None:
            return True

        # 2. Attempt API Key hash validation
        storage = self._credential_storage_getter()
        hashed = storage.get_hashed_api_key()
        if not hashed:
            return False

        if isinstance(hashed, str):
            hashed = hashed.encode("utf-8")

        try:
            if bcrypt.checkpw(token_or_key.encode("utf-8"), hashed):
                self._valid_keys_cache.add(token_or_key)
                return True
        except Exception:
            return False

        return False

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Always permit CORS preflight requests
        if scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return

        credential = self._extract_credential(scope)
        if not credential or not self._verify_credential(credential):
            response = JSONResponse(
                {
                    "error": "unauthorized",
                    "message": "Invalid or missing Server API key or Bearer token",
                },
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="mcp", error="invalid_token"'},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
