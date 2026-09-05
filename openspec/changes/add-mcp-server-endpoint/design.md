## Context
The Cambridge Dictionary Anki Sync Server enables flashcard creation and synchronization with AnkiWeb. LLM users on tools like Cursor, Claude Desktop, Windsurf, or custom AI agents need a standard way to interface with this server to create flashcards directly from AI chat sessions.

## Goals / Non-Goals
- **Goals**:
  - Expose an MCP Streamable HTTP endpoint at `/mcp` directly from the server.
  - Implement direct Server API key authentication so long-running MCP clients do not expire like short-lived JWT tokens.
  - Provide a streamlined `create_flashcard` tool that handles automatic cloze tagging and empty string defaults for optional fields.
  - Provide `get_task_status` for asynchronous task monitoring.
  - Provide `check_health` tool and `create_vocabulary_card` MCP prompt.
  - Maintain backwards compatibility for existing `/api/v1` REST endpoints and `/` health route.
  - Run as a unified ASGI service using `uvicorn`.
- **Non-Goals**:
  - Running a separate stdio CLI bridge process (decided in interview to focus on Streamable HTTP).
  - Synchronous blocking card creation within MCP calls (decided in interview to always be asynchronous).

## Decisions
- **Decision 1: MCP Server via `mcp.server.mcpserver.MCPServer`**
  - Use the official Python MCP 2.x SDK `MCPServer` class to define tools and prompts.
  - Generate the Starlette ASGI app using `server.streamable_http_app()`.
- **Decision 2: Authentication Middleware**
  - Starlette HTTP middleware intercepts `/mcp` requests and validates the API key against `CredentialStorage().get_hashed_api_key()` using `bcrypt.checkpw`.
  - Supports `Authorization: Bearer <key>`, `X-API-Key: <key>`, or `?api_key=<key>`.
- **Decision 3: Unified ASGI Architecture via `a2wsgi`**
  - Wrap the Flask WSGI application using `a2wsgi.WSGIMiddleware` and mount it alongside `/mcp` under a top-level Starlette application.
  - Run the application with `uvicorn anki_sync_server.server.main:app --host 0.0.0.0 --port 5000`.
- **Decision 4: Tool Schema & Defaults**
  - `create_flashcard` requires `word`, `english_example`, `english_definition`.
  - Optional fields (`part_of_speech`, `definition_translation`, `example_translation`, `guide_word`, `cefr_level`, `code`) default to `""`.
  - If `{{c1::...}}` is not in `english_example`, the tool locates the first case-insensitive instance of `word` and wraps it as `{{c1::word}}`.
  - Dispatches `add_cloze_note_task.delay(note_dict)`.

## Risks / Trade-offs
- **Risk**: Bcrypt hashing can take ~50ms per request.
  - **Mitigation**: Cache the verified key hash in-memory or session context so subsequent requests within the same stream/session are fast.
- **Risk**: Moving from uWSGI to Uvicorn for production.
  - **Mitigation**: Uvicorn is widely used, production-ready, already installed in the environment, and natively handles ASGI/SSE streams.
