# Change: Add OAuth 2.0 Support for MCP Server

## Why
Gemini (including Gemini CLI and Gemini Enterprise) requires standard OAuth 2.0 for connecting to remote Model Context Protocol (MCP) servers instead of static API keys or headers. Adding a built-in lightweight OAuth 2.0 authorization server allows Gemini clients to authenticate via standard Authorization Code Flow with PKCE, while maintaining backwards compatibility for existing clients (like Claude Desktop, Cursor, and Windsurf) that use direct Server API keys.

## What Changes
- Implement built-in OAuth 2.0 endpoints:
  - `/oauth/authorize`: Serves a browser authorization page where users verify their identity with the Server API key, supporting Authorization Code grant and PKCE (`code_challenge` / `code_challenge_method`).
  - `/oauth/token`: Exchanges authorization codes (verifying PKCE and optional client secret) or refresh tokens for JWT access tokens (1 hour lifetime) and refresh tokens (180 days).
- Implement OAuth 2.0 Authorization Server Discovery metadata at `/.well-known/oauth-authorization-server` and `/.well-known/openid-configuration` (RFC 8414).
- Update the MCP authentication middleware to support dual authentication: validating incoming requests using either OAuth 2.0 Bearer JWT access tokens or static Server API keys, and responding with standard `WWW-Authenticate: Bearer` headers on 401 unauthorized requests.
- Support optional `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` in `.env` for confidential clients, while supporting public clients using PKCE (e.g. Gemini CLI).
- Provide documentation for configuring Gemini CLI (`~/.gemini/settings.json`) and connecting with `/mcp auth`.

## Impact
- Affected specs: `mcp-server`
- Affected code:
  - `anki_sync_server/mcp/oauth.py`: New module for OAuth endpoints, token issuance, PKCE validation, and HTML consent view.
  - `anki_sync_server/mcp/auth.py`: Updated middleware supporting both OAuth 2.0 Bearer JWT tokens and Server API keys.
  - `anki_sync_server/server/main.py`: ASGI routing for `/oauth/*` and `/.well-known/*`.
  - `README.md`: Documentation on Gemini CLI and Gemini Enterprise MCP configuration.
