# mcp-server Specification

## Purpose
TBD - created by archiving change add-mcp-server-endpoint. Update Purpose after archive.
## Requirements
### Requirement: Streamable HTTP MCP Endpoint
The server SHALL expose a Model Context Protocol (MCP) endpoint at `/mcp` supporting the Streamable HTTP transport specification.

#### Scenario: MCP endpoint responds to protocol initialize
- **WHEN** an MCP client sends an initialize request to `/mcp` with valid credentials
- **THEN** the server returns server capabilities, protocol version, and server metadata

### Requirement: Server API Key Authentication for MCP
The server SHALL validate incoming requests to `/mcp` using the stored Server API key supplied via `Authorization: Bearer <key>`, `X-API-Key: <key>`, or `?api_key=<key>` query parameter.

#### Scenario: Valid API key access
- **WHEN** a request arrives with a valid Server API key matching the hashed credentials
- **THEN** the request is allowed to proceed to the MCP transport handler

#### Scenario: Missing or invalid API key access
- **WHEN** a request arrives at `/mcp` without an API key or with an invalid key
- **THEN** the server responds with HTTP 401 Unauthorized status

### Requirement: Asynchronous Flashcard Creation Tool
The MCP server SHALL provide a `create_flashcard` tool that accepts vocabulary parameters, applies defaults (empty string for omitted optional fields, automatic cloze wrapping for example sentences), enqueues the note creation Celery task, and returns the task ID immediately.

#### Scenario: Create flashcard with minimal parameters
- **WHEN** an LLM calls `create_flashcard` with `word`, `english_example`, and `english_definition`
- **THEN** the example sentence is automatically wrapped in `{{c1::word}}` if not already tagged, optional fields are defaulted to empty strings, the Celery task is dispatched, and the `taskId` and pending status are returned

#### Scenario: Create flashcard with full Cambridge parameters
- **WHEN** an LLM calls `create_flashcard` with all dictionary fields
- **THEN** all provided fields are preserved, the Celery task is dispatched, and the `taskId` is returned

### Requirement: Task Status Tool
The MCP server SHALL provide a `get_task_status` tool that queries the status of any previously dispatched card creation task by `task_id`.

#### Scenario: Query existing task status
- **WHEN** an LLM calls `get_task_status` with a valid `task_id`
- **THEN** the current status (`pending`, `processing`, `completed`, or `failed`) and result metadata are returned

#### Scenario: Query non-existent task status
- **WHEN** an LLM calls `get_task_status` with an unknown `task_id`
- **THEN** an appropriate error or not found status is returned

### Requirement: Server Health Tool
The MCP server SHALL provide a `check_health` tool allowing the LLM client to verify connection and server status.

#### Scenario: Health check invocation
- **WHEN** an LLM calls `check_health`
- **THEN** the server returns `{"status": "ok"}`

### Requirement: Vocabulary Card MCP Prompt
The MCP server SHALL provide an MCP Prompt named `create_vocabulary_card` to guide LLMs in converting highlighted text or word lookups into structured flashcards.

#### Scenario: Retrieve vocabulary card prompt
- **WHEN** an MCP client lists or retrieves the `create_vocabulary_card` prompt
- **THEN** instructions guiding the LLM on word extraction, definition generation, cloze sentences, and translation formatting are returned

