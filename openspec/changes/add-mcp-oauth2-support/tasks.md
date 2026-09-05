## 1. Implementation
- [x] 1.1 Implement OAuth 2.0 endpoints and PKCE logic in `anki_sync_server/mcp/oauth.py` (`/oauth/authorize`, `/oauth/token`, and discovery metadata)
- [x] 1.2 Implement HTML authorization page template in `anki_sync_server/mcp/oauth.py` for entering Server API key
- [x] 1.3 Update `ApiKeyAuthMiddleware` (or add OAuth support) in `anki_sync_server/mcp/auth.py` to validate both OAuth 2.0 Bearer JWTs and static API keys, returning `WWW-Authenticate: Bearer`
- [x] 1.4 Mount OAuth routes and discovery endpoints in `CompositeApp` in `anki_sync_server/server/main.py`
- [x] 1.5 Add comprehensive unit and integration tests for OAuth authorization code grant, PKCE validation, refresh token, discovery endpoints, and `/mcp` dual auth
- [x] 1.6 Update `README.md` with Gemini CLI (`~/.gemini/settings.json`) and Gemini Enterprise configuration instructions
