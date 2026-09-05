# Capability: mcp-server

## RENAMED Requirements
- FROM: `### Requirement: Server API Key Authentication for MCP`
- TO: `### Requirement: Dual Authentication for MCP`

## MODIFIED Requirements
### Requirement: Dual Authentication for MCP
The server SHALL validate incoming requests to `/mcp` using either a valid OAuth 2.0 Bearer JWT access token or a stored Server API key supplied via `Authorization: Bearer <token_or_key>`, `X-API-Key: <key>`, or `?api_key=<key>` query parameter. When responding with 401 Unauthorized, the server SHALL include a `WWW-Authenticate: Bearer` header.

#### Scenario: Valid API key access
- **WHEN** a request arrives with a valid Server API key matching the hashed credentials
- **THEN** the request is allowed to proceed to the MCP transport handler

#### Scenario: Valid OAuth 2.0 Bearer token access
- **WHEN** a request arrives with a valid OAuth 2.0 Bearer JWT access token issued by `/oauth/token`
- **THEN** the request is allowed to proceed to the MCP transport handler

#### Scenario: Missing or invalid credentials
- **WHEN** a request arrives at `/mcp` without valid authentication credentials
- **THEN** the server responds with HTTP 401 Unauthorized status and a `WWW-Authenticate: Bearer` header

## ADDED Requirements
### Requirement: OAuth 2.0 Authorization Endpoint
The server SHALL expose an OAuth 2.0 authorization endpoint at `/oauth/authorize` supporting the Authorization Code grant (`response_type=code`) and PKCE (`code_challenge` and `code_challenge_method`).

#### Scenario: Browser authorization with valid Server API key
- **WHEN** a user accesses `/oauth/authorize` with valid query parameters (`client_id`, `redirect_uri`, `response_type=code`, `code_challenge`) and submits their valid Server API key
- **THEN** the server generates a short-lived authorization code and redirects the browser to `redirect_uri` with `code` and `state` parameters

#### Scenario: Browser authorization with invalid Server API key
- **WHEN** a user submits an incorrect Server API key on the `/oauth/authorize` page
- **THEN** the server redisplays the authorization form with an error message and does not issue a code

### Requirement: OAuth 2.0 Token Endpoint
The server SHALL expose an OAuth 2.0 token endpoint at `/oauth/token` supporting `grant_type=authorization_code` with PKCE validation and `grant_type=refresh_token`.

#### Scenario: Exchange authorization code with PKCE for access token
- **WHEN** a client posts to `/oauth/token` with `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, and `code_verifier` matching the earlier `code_challenge`
- **THEN** the server returns a 200 response with JSON containing `access_token` (JWT with 1-hour expiration), `token_type=bearer`, `expires_in=3600`, and `refresh_token`

#### Scenario: Exchange refresh token for new access token
- **WHEN** a client posts to `/oauth/token` with `grant_type=refresh_token` and a valid `refresh_token`
- **THEN** the server returns a 200 response with a new `access_token` and `refresh_token`

### Requirement: OAuth 2.0 Authorization Server Discovery Metadata
The server SHALL expose OAuth 2.0 authorization server metadata conforming to RFC 8414 at `/.well-known/oauth-authorization-server` and `/.well-known/openid-configuration`.

#### Scenario: Retrieve authorization server metadata
- **WHEN** a client sends a GET request to `/.well-known/oauth-authorization-server` or `/.well-known/openid-configuration`
- **THEN** the server returns HTTP 200 with JSON metadata containing `issuer`, `authorization_endpoint`, `token_endpoint`, `response_types_supported`, and `code_challenge_methods_supported`
