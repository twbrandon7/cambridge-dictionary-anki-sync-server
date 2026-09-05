## Context
Gemini connects to remote MCP servers using OAuth 2.0 (specifically Authorization Code grant with PKCE for CLI clients, and standard client credentials / code grant for enterprise). The current server implementation exclusively accepts static API keys via headers or query parameters, causing Gemini client connections to fail.

## Goals / Non-Goals
- **Goals:**
  - Provide a built-in, lightweight OAuth 2.0 Authorization Server that requires no external identity provider (IdP).
  - Support Authorization Code grant (`response_type=code`) with PKCE (`code_challenge_method=S256` or `plain`).
  - Provide an HTML authorization interface at `/oauth/authorize` where the user authenticates with their Server API key.
  - Implement token issuance (`/oauth/token`) for `authorization_code` and `refresh_token` grant types, signing standard JWTs with the existing server secret key.
  - Support RFC 8414 metadata discovery (`/.well-known/oauth-authorization-server` and `/.well-known/openid-configuration`).
  - Dual authentication on `/mcp`: Accept both OAuth 2.0 Bearer JWT tokens and static Server API keys.
  - Support public clients with PKCE (Gemini CLI) as well as confidential clients configured via `OAUTH_CLIENT_ID` / `OAUTH_CLIENT_SECRET`.
- **Non-Goals:**
  - Replacing the core Flask REST API authentication (`/api/v1`).
  - Third-party social login (Google OAuth login, GitHub login) for Anki cards.

## Decisions
- **Token Signing & Verification**: Use `jwt` (PyJWT) with the existing `server_secret_key` from `CredentialStorage`, emitting access tokens with standard claims (`iss`, `sub`, `aud`, `exp`, `iat`, `token_use="access"`).
- **PKCE Verification**: In `/oauth/token`, compute SHA256 of `code_verifier` (for S256) and base64url-encode without padding, comparing against the stored `code_challenge`.
- **Authorization Code Storage**: Store pending authorization codes in-memory with a short TTL (5 minutes) containing client ID, redirect URI, user authentication status, and code challenge.
- **ASGI Routing**: Mount OAuth endpoints and discovery handlers in the composite ASGI application (`CompositeApp` in `anki_sync_server/server/main.py`) or Starlette application so requests are handled cleanly.

## Risks / Trade-offs
- **In-memory authorization code store**: If multiple worker processes run without shared memory, authorization codes might be routed to a different worker.
  - *Mitigation*: In our default setup (single uvicorn worker or sticky sessions/tunnel), in-memory TTL cache is fast and standard. We will implement thread-safe dictionary storage with expiration cleanup.
