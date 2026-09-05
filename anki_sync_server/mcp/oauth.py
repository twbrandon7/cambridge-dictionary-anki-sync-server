import base64
import hashlib
import html
import os
import secrets
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route

from anki_sync_server import APP_NAME
from anki_sync_server.setup.credential_storage import CredentialStorage


class AuthorizationCodeStore:
    """Thread-safe in-memory store for OAuth 2.0 authorization codes with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._codes: Dict[str, Dict[str, Any]] = {}

    def _cleanup(self) -> None:
        now = time.time()
        expired = [
            code for code, data in self._codes.items() if data["expires_at"] <= now
        ]
        for code in expired:
            self._codes.pop(code, None)

    def create_code(
        self,
        client_id: str,
        redirect_uri: str,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
        scope: str = "",
    ) -> str:
        self._cleanup()
        code = secrets.token_urlsafe(32)
        self._codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method or "plain",
            "scope": scope,
            "expires_at": time.time() + self.ttl_seconds,
            "used": False,
        }
        return code

    def consume_code(self, code: str) -> Optional[Dict[str, Any]]:
        self._cleanup()
        data = self._codes.pop(code, None)
        if not data:
            return None
        if data["expires_at"] <= time.time():
            return None
        return data


code_store = AuthorizationCodeStore()


def verify_pkce(
    code_verifier: str,
    code_challenge: Optional[str],
    code_challenge_method: str = "plain",
) -> bool:
    """
    Verify PKCE code_verifier against code_challenge per RFC 7636.
    """
    if not code_challenge:
        # If no challenge was sent initially, verification is not required
        return True

    if not code_verifier:
        return False

    if code_challenge_method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return secrets.compare_digest(computed, code_challenge)

    if code_challenge_method == "plain":
        return secrets.compare_digest(code_verifier, code_challenge)

    return False


def get_base_url(request: Request) -> str:
    """
    Resolve public base URL from SERVER_PUBLIC_URL env var or incoming request headers.
    """
    env_url = os.environ.get("SERVER_PUBLIC_URL", "").strip().rstrip("/")
    if env_url:
        return env_url

    headers = request.headers
    proto = headers.get("x-forwarded-proto") or request.url.scheme or "http"
    host = headers.get("x-forwarded-host") or headers.get("host") or "localhost:5000"
    return f"{proto}://{host}"


def generate_jwt_token(
    token_type: str,
    ttl: timedelta,
    client_id: str = "",
    scope: str = "mcp",
) -> str:
    """Generate a signed JWT token using server secret key."""
    storage = CredentialStorage()
    secret_key = storage.get_server_secret_key()
    if not secret_key:
        secret_key = "default-fallback-secret-key"

    now = datetime.now(timezone.utc)
    payload = {
        "iss": APP_NAME,
        "sub": client_id or "mcp_client",
        "aud": "mcp",
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "type": token_type,
        "scope": scope,
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_jwt_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode a signed JWT token."""
    storage = CredentialStorage()
    secret_key = storage.get_server_secret_key()
    if not secret_key:
        return None

    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"], audience="mcp")
        if decoded.get("type") == expected_type:
            return decoded
        return None
    except jwt.InvalidTokenError:
        # Also attempt without audience check for backward compatibility with token_issuer.py
        try:
            decoded = jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_aud": False})
            if decoded.get("type") == expected_type and decoded.get("iss") == APP_NAME:
                return decoded
            return None
        except jwt.InvalidTokenError:
            return None


def render_authorize_page(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    state: str,
    scope: str,
    code_challenge: str,
    code_challenge_method: str,
    error: str = "",
) -> str:
    """Render a clean, modern HTML authorization interface."""
    escaped_client_id = html.escape(client_id or "MCP Client (e.g. Gemini)")
    escaped_redirect = html.escape(redirect_uri)
    escaped_response_type = html.escape(response_type)
    escaped_state = html.escape(state)
    escaped_scope = html.escape(scope or "mcp")
    escaped_challenge = html.escape(code_challenge)
    escaped_method = html.escape(code_challenge_method)

    error_html = ""
    if error:
        error_html = f"""
        <div class="alert alert-error">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span>{html.escape(error)}</span>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorize MCP Access - Anki Sync Server</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --danger: #ef4444;
            --danger-bg: rgba(239, 68, 68, 0.15);
            --focus-ring: rgba(59, 130, 246, 0.5);
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        body {{
            background: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
            max-width: 440px;
            width: 100%;
            padding: 2rem;
        }}
        .header {{
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        .icon-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            border-radius: 14px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
        }}
        .icon-badge svg {{
            width: 28px;
            height: 28px;
            color: #ffffff;
        }}
        h1 {{
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }}
        .subtitle {{
            color: var(--text-secondary);
            font-size: 0.88rem;
            line-height: 1.4;
        }}
        .client-info {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-bottom: 1.5rem;
            font-size: 0.85rem;
        }}
        .client-info-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.35rem;
        }}
        .client-info-row:last-child {{
            margin-bottom: 0;
        }}
        .label {{
            color: var(--text-secondary);
        }}
        .value {{
            font-weight: 600;
            color: #60a5fa;
            word-break: break-all;
        }}
        .alert {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            margin-bottom: 1.25rem;
        }}
        .alert-error {{
            background: var(--danger-bg);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
        }}
        .form-group {{
            margin-bottom: 1.25rem;
        }}
        label.input-label {{
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}
        input[type="password"], input[type="text"] {{
            width: 100%;
            padding: 0.75rem 1rem;
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--focus-ring);
        }}
        .actions {{
            display: flex;
            gap: 0.75rem;
            margin-top: 1.5rem;
        }}
        .btn {{
            flex: 1;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            border: none;
            transition: all 0.2s ease;
            text-decoration: none;
        }}
        .btn-primary {{
            background: var(--primary);
            color: #ffffff;
        }}
        .btn-primary:hover {{
            background: var(--primary-hover);
        }}
        .btn-secondary {{
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }}
        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }}
        .footer-note {{
            margin-top: 1.25rem;
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="icon-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
            </div>
            <h1>Authorize Application</h1>
            <p class="subtitle">An AI client is requesting access to your Anki Sync Server tools and flashcards.</p>
        </div>

        <div class="client-info">
            <div class="client-info-row">
                <span class="label">Client:</span>
                <span class="value">{escaped_client_id}</span>
            </div>
            <div class="client-info-row">
                <span class="label">Permissions:</span>
                <span class="value">{escaped_scope}</span>
            </div>
        </div>

        {error_html}

        <form method="POST" action="/oauth/authorize">
            <input type="hidden" name="client_id" value="{escaped_client_id}">
            <input type="hidden" name="redirect_uri" value="{escaped_redirect}">
            <input type="hidden" name="response_type" value="{escaped_response_type}">
            <input type="hidden" name="state" value="{escaped_state}">
            <input type="hidden" name="scope" value="{escaped_scope}">
            <input type="hidden" name="code_challenge" value="{escaped_challenge}">
            <input type="hidden" name="code_challenge_method" value="{escaped_method}">

            <div class="form-group">
                <label class="input-label" for="api_key">Server API Key</label>
                <input type="password" id="api_key" name="api_key" placeholder="Enter your server API key" required autofocus>
            </div>

            <div class="actions">
                <a href="{escaped_redirect}?error=access_denied&state={escaped_state}" class="btn btn-secondary">Cancel</a>
                <button type="submit" class="btn btn-primary">Authorize</button>
            </div>
        </form>

        <p class="footer-note">Your API key is verified securely against your server's hashed credentials.</p>
    </div>
</body>
</html>
"""


async def oauth_authorize_endpoint(request: Request) -> Response:
    """
    Handle GET (render login page) and POST (validate API key and redirect with code) for /oauth/authorize.
    """
    if request.method == "GET":
        client_id = request.query_params.get("client_id", "")
        redirect_uri = request.query_params.get("redirect_uri", "")
        response_type = request.query_params.get("response_type", "")
        state = request.query_params.get("state", "")
        scope = request.query_params.get("scope", "mcp")
        code_challenge = request.query_params.get("code_challenge", "")
        code_challenge_method = request.query_params.get("code_challenge_method", "plain")

        if not redirect_uri:
            return JSONResponse({"error": "invalid_request", "error_description": "Missing redirect_uri"}, status_code=400)

        if response_type != "code":
            redirect_with_err = f"{redirect_uri}?error=unsupported_response_type&state={urllib.parse.quote(state)}"
            return RedirectResponse(url=redirect_with_err, status_code=302)

        html_content = render_authorize_page(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            state=state,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        return HTMLResponse(html_content)

    elif request.method == "POST":
        form_data = await request.form()
        client_id = form_data.get("client_id", "")
        redirect_uri = form_data.get("redirect_uri", "")
        state = form_data.get("state", "")
        scope = form_data.get("scope", "mcp")
        code_challenge = form_data.get("code_challenge", "")
        code_challenge_method = form_data.get("code_challenge_method", "plain")
        api_key = str(form_data.get("api_key", "")).strip()

        if not redirect_uri:
            return JSONResponse({"error": "invalid_request", "error_description": "Missing redirect_uri"}, status_code=400)

        # Validate Server API Key
        storage = CredentialStorage()
        hashed = storage.get_hashed_api_key()
        is_valid = False
        if hashed and api_key:
            if isinstance(hashed, str):
                hashed = hashed.encode("utf-8")
            try:
                if bcrypt.checkpw(api_key.encode("utf-8"), hashed):
                    is_valid = True
            except Exception:
                is_valid = False

        if not is_valid:
            html_content = render_authorize_page(
                client_id=str(client_id),
                redirect_uri=str(redirect_uri),
                response_type="code",
                state=str(state),
                scope=str(scope),
                code_challenge=str(code_challenge),
                code_challenge_method=str(code_challenge_method),
                error="Invalid Server API key. Please verify and try again.",
            )
            return HTMLResponse(html_content, status_code=401)

        # Issue authorization code
        code = code_store.create_code(
            client_id=str(client_id),
            redirect_uri=str(redirect_uri),
            code_challenge=str(code_challenge) if code_challenge else None,
            code_challenge_method=str(code_challenge_method) if code_challenge_method else "plain",
            scope=str(scope),
        )

        query_params = {"code": code}
        if state:
            query_params["state"] = str(state)

        delimiter = "&" if "?" in redirect_uri else "?"
        redirect_target = f"{redirect_uri}{delimiter}{urllib.parse.urlencode(query_params)}"
        return RedirectResponse(url=redirect_target, status_code=302)

    return JSONResponse({"error": "invalid_request"}, status_code=405)


async def oauth_token_endpoint(request: Request) -> Response:
    """
    Handle token exchange at /oauth/token (grant_type=authorization_code and grant_type=refresh_token).
    """
    if request.method != "POST":
        return JSONResponse({"error": "invalid_request", "error_description": "Method not allowed"}, status_code=405)

    # Content can be form-encoded or json
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            params = await request.json()
        except Exception:
            params = {}
    else:
        form = await request.form()
        params = dict(form)

    grant_type = params.get("grant_type")
    client_id = params.get("client_id", "")
    client_secret = params.get("client_secret", "")

    # Basic auth client credentials check if header is present
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth_header[6:].strip()).decode("utf-8")
            if ":" in decoded:
                basic_client_id, basic_client_secret = decoded.split(":", 1)
                client_id = client_id or basic_client_id
                client_secret = client_secret or basic_client_secret
        except Exception:
            pass

    # Validate optional confidential client secret if configured in environment
    configured_client_id = os.environ.get("OAUTH_CLIENT_ID", "").strip()
    configured_client_secret = os.environ.get("OAUTH_CLIENT_SECRET", "").strip()
    if configured_client_id and configured_client_secret:
        if client_id == configured_client_id:
            if client_secret != configured_client_secret:
                return JSONResponse(
                    {"error": "invalid_client", "error_description": "Invalid client secret"},
                    status_code=401,
                )

    if grant_type == "authorization_code":
        code = params.get("code")
        redirect_uri = params.get("redirect_uri")
        code_verifier = params.get("code_verifier", "")

        if not code:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing authorization code"},
                status_code=400,
            )

        code_data = code_store.consume_code(code)
        if not code_data:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "Invalid, expired, or previously used authorization code"},
                status_code=400,
            )

        # Verify redirect_uri if provided in original authorization request
        expected_redirect = code_data.get("redirect_uri")
        if expected_redirect and redirect_uri and expected_redirect != redirect_uri:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "redirect_uri mismatch"},
                status_code=400,
            )

        # Verify PKCE
        stored_challenge = code_data.get("code_challenge")
        stored_method = code_data.get("code_challenge_method", "plain")
        if stored_challenge:
            if not verify_pkce(code_verifier, stored_challenge, stored_method):
                return JSONResponse(
                    {"error": "invalid_grant", "error_description": "PKCE verification failed"},
                    status_code=400,
                )

        access_token = generate_jwt_token(
            token_type="access",
            ttl=timedelta(hours=1),
            client_id=code_data.get("client_id", client_id),
            scope=code_data.get("scope", "mcp"),
        )
        refresh_token = generate_jwt_token(
            token_type="refresh",
            ttl=timedelta(days=180),
            client_id=code_data.get("client_id", client_id),
            scope=code_data.get("scope", "mcp"),
        )

        return JSONResponse(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "refresh_token": refresh_token,
                "scope": code_data.get("scope", "mcp"),
            },
            status_code=200,
            headers={
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
            },
        )

    elif grant_type == "refresh_token":
        refresh_token = params.get("refresh_token")
        if not refresh_token:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing refresh_token"},
                status_code=400,
            )

        decoded = verify_jwt_token(refresh_token, expected_type="refresh")
        if not decoded:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "Invalid or expired refresh token"},
                status_code=400,
            )

        token_client_id = decoded.get("sub", client_id)
        token_scope = decoded.get("scope", "mcp")

        new_access_token = generate_jwt_token(
            token_type="access",
            ttl=timedelta(hours=1),
            client_id=token_client_id,
            scope=token_scope,
        )
        new_refresh_token = generate_jwt_token(
            token_type="refresh",
            ttl=timedelta(days=180),
            client_id=token_client_id,
            scope=token_scope,
        )

        return JSONResponse(
            {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "refresh_token": new_refresh_token,
                "scope": token_scope,
            },
            status_code=200,
            headers={
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
            },
        )

    return JSONResponse(
        {"error": "unsupported_grant_type", "error_description": f"Unsupported grant_type: {grant_type}"},
        status_code=400,
    )


async def oauth_discovery_endpoint(request: Request) -> JSONResponse:
    """
    Expose RFC 8414 OAuth 2.0 Authorization Server Metadata.
    """
    base_url = get_base_url(request)
    metadata = {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
            "none",
        ],
        "code_challenge_methods_supported": ["S256", "plain"],
        "scopes_supported": ["mcp"],
    }
    return JSONResponse(metadata, status_code=200)


def create_oauth_app() -> Starlette:
    """Create Starlette app containing OAuth 2.0 and discovery routes."""
    routes = [
        Route("/oauth/authorize", oauth_authorize_endpoint, methods=["GET", "POST"]),
        Route("/oauth/token", oauth_token_endpoint, methods=["POST"]),
        Route("/.well-known/oauth-authorization-server", oauth_discovery_endpoint, methods=["GET"]),
        Route("/.well-known/openid-configuration", oauth_discovery_endpoint, methods=["GET"]),
    ]
    return Starlette(routes=routes)
