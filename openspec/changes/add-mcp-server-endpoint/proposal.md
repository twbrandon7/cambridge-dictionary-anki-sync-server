# Change: Add MCP Server Endpoint

## Why
Users want to generate and add Anki flashcards directly from AI tools and LLMs (such as Cursor, Claude Desktop, Windsurf, or custom AI agents). Currently, adding cards requires either the browser extension or manual REST API calls with short-lived JWT tokens. Exposing a Model Context Protocol (MCP) Streamable HTTP endpoint (`/mcp`) allows any MCP-compatible LLM client to seamlessly inspect server status, queue cloze flashcards with smart defaults, and track background creation tasks.

## What Changes
- Add an MCP server component using `mcp.server.mcpserver.MCPServer` exposing Streamable HTTP transport at `/mcp`.
- Expose tools:
  - `create_flashcard`: Queues cloze flashcard creation with Celery background worker, automatically wrapping target words in cloze syntax `{{c1::word}}` if missing, and defaulting optional fields to empty strings.
  - `get_task_status`: Retrieves the status (`pending`, `processing`, `completed`, `failed`) and result metadata for background tasks.
  - `check_health`: Verifies server connection and status.
- Expose MCP prompt:
  - `create_vocabulary_card`: Guided prompt template instructing LLMs on structured card generation from user-selected text.
- Add long-lived API key authentication for `/mcp` via HTTP `Authorization: Bearer <SERVER_API_KEY>`, `X-API-Key`, or `?api_key=` query parameter.
- Transition server serving to a unified ASGI application (`uvicorn`) combining the Starlette `/mcp` app and the existing Flask WSGI app (`/api/v1` and `/`) using an ASGI-WSGI bridge.
- Update Dockerfile and documentation for MCP setup in AI clients.

## Impact
- Affected specs: `mcp-server` (new capability)
- Affected code:
  - `anki_sync_server/mcp/`: New package for MCP server, tools, prompts, and authentication middleware.
  - `anki_sync_server/server/main.py`: Composite ASGI application mounting MCP and Flask.
  - `Dockerfile`: Updated CMD to use uvicorn for ASGI support.
  - `pyproject.toml`: Add `a2wsgi` if needed for clean WSGI/ASGI bridging.
  - `README.md`: Documentation on MCP client configuration.
