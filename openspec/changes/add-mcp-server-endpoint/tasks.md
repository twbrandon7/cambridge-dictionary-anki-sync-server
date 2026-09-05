## 1. Dependencies & Foundation
- [x] 1.1 Add `a2wsgi>=1.10.0` to `pyproject.toml` dependencies and run `uv sync`
- [x] 1.2 Create `anki_sync_server/mcp/` module structure with authentication middleware and helper utilities

## 2. MCP Server Implementation
- [x] 2.1 Implement `anki_sync_server/mcp/server.py` with `MCPServer` instance
- [x] 2.2 Implement `create_flashcard` tool with auto-cloze tagging, optional parameter defaults, and Celery dispatch
- [x] 2.3 Implement `get_task_status` tool for Celery task querying
- [x] 2.4 Implement `check_health` tool and `create_vocabulary_card` prompt
- [x] 2.5 Implement authentication middleware supporting `Authorization: Bearer <key>`, `X-API-Key`, and query parameters

## 3. Web Server Integration & Deployment
- [x] 3.1 Update `anki_sync_server/server/main.py` to expose a composite ASGI application mounting `/mcp` and Flask
- [x] 3.2 Update `Dockerfile` to run the ASGI app with `uvicorn`
- [x] 3.3 Update `README.md` with MCP setup instructions for Claude Desktop, Cursor, and other AI tools

## 4. Testing & Verification
- [x] 4.1 Write unit tests for MCP authentication middleware and tool handlers
- [x] 4.2 Test MCP Streamable HTTP initialization and tool calls
- [x] 4.3 Verify existing Flask REST endpoints (`/api/v1/health`, `/api/v1/login`) remain functional through the ASGI bridge
