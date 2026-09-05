# Cambridge Dictionary Anki Sync Server

A Flask-based API server that automatically creates and syncs Anki flashcards with vocabulary from the Cambridge Dictionary. This server integrates with AnkiWeb to create custom cloze deletion cards with definitions, translations, audio pronunciations, and CEFR levels.

## Features

- **Automatic Anki Card Creation**: Creates custom cloze cards with Cambridge Dictionary data
- **Model Context Protocol (MCP)**: Create flashcards directly from LLMs (Cursor, Claude Desktop, Windsurf) using the `/mcp` Streamable HTTP endpoint
- **AnkiWeb Synchronization**: Automatically syncs cards to your AnkiWeb account
- **Asynchronous Card Creation**: Background task processing for non-blocking API responses
- **Text-to-Speech Integration**: Generates audio pronunciations using Google Cloud TTS
- **REST API**: Easy-to-use HTTP endpoints for adding vocabulary
- **Token-based Authentication**: Secure API access with JWT tokens
- **Docker Support**: Ready-to-deploy containerized setup with NGINX reverse proxy
- **Cloudflare Tunnel Support**: Optional tunnel configuration for remote access

## Prerequisites

- Python 3.11 or higher
- AnkiWeb account
- Google Cloud Text-to-Speech API key (for audio generation)
- Docker and Docker Compose (for containerized deployment)
- uv (Python package manager) - [Installation Guide](https://docs.astral.sh/uv/getting-started/)

## Installation

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/twbrandon7/cambridge-dictionary-anki-sync-server.git
   cd cambridge-dictionary-anki-sync-server
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```
   
   This will create a virtual environment and install all dependencies from `pyproject.toml`.

3. **Activate the virtual environment**
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Run the setup wizard**
   ```bash
   python -m anki_sync_server setup
   ```

   The setup wizard will guide you through:
   - **AnkiWeb Login**: Enter your AnkiWeb credentials to sync cards
   - **Google Cloud TTS API Key**: Provide your GCP TTS API key for audio generation
   - **Server API Key**: A secure API key will be generated for authenticating API requests

   **Important**: Save the generated Server API key displayed at the end of setup. You'll need it to authenticate API requests.

5. **Start the server**
   ```bash
   uv run uvicorn anki_sync_server.server.main:app --host 0.0.0.0 --port 5000
   ```

### Docker Deployment

1. **Set up environment variables**
   
   Create a `.env` file in the project root (optional, for Cloudflare tunnel):
   ```bash
   TUNNEL_TOKEN=your_cloudflare_tunnel_token
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - **App container**: The Flask API server
   - **NGINX container**: Reverse proxy on port 5000
   - **Cloudflare Tunnel container**: (Optional) Secure tunnel for remote access

3. **Run the setup wizard in the container**
   ```bash
   docker-compose exec app python -m anki_sync_server setup
   ```

4. **Access the server**
   
   The server will be available at `http://localhost:5000`

## API Documentation

### Base URL

- Local: `http://localhost:5000`
- Production: Your configured domain

### Authentication

All endpoints (except `/login` and `/refresh`) require authentication using a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Endpoints

#### 1. Health Check

**GET** `/`

Returns server status.

**Response:**
```json
{
  "status": "ok"
}
```

---

#### 2. Login

**POST** `/api/v1/login`

Authenticate with your Server API key to receive access and refresh tokens.

**Request Body:**
```json
{
  "key": "your_server_api_key"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Token Lifetimes:**
- Access Token: 1 hour
- Refresh Token: 180 days

---

#### 3. Refresh Token

**POST** `/api/v1/refresh`

Get new access and refresh tokens using a valid refresh token.

**Request Body:**
```json
{
  "refreshToken": "your_refresh_token"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

#### 4. Health Check (Authenticated)

**GET** `/api/v1/health`

Protected health check endpoint.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "ok"
}
```

---

#### 5. Create Cloze Note (Async)

**POST** `/api/v1/clozeNotes`

Creates a new cloze deletion flashcard asynchronously. Returns immediately with a task ID for polling.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "word": "apple",
  "partOfSpeech": "noun",
  "guideWord": "",
  "englishDefinition": "a round fruit with hard skin and soft, white flesh that grows on trees",
  "definitionTranslation": "蘋果",
  "cefrLevel": "A1",
  "code": "[ C or U ]",
  "englishExample": "to peel an {{c1::apple}}",
  "exampleTranslation": "削蘋果"
}
```

**Response (202 Accepted):**
```json
{
  "taskId": "abc123def456",
  "status": "pending",
  "statusUrl": "/api/v1/tasks/abc123def456",
  "createdAt": "2026-01-03T10:30:00Z"
}
```

**Query Parameters:**
- `async` (optional, default: `true`): Set to `false` to use synchronous mode (legacy behavior)

**Synchronous Mode (Legacy):**
```bash
curl -X POST http://localhost:5000/api/v1/clozeNotes?async=false \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{...note_data...}'
```

Response (200 OK):
```json
{
  "status": "ok"
}
```

---

#### 6. Get Task Status

**GET** `/api/v1/tasks/<task_id>`

Fetch the status of an async card creation task.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK) - Pending:**
```json
{
  "taskId": "abc123def456",
  "status": "pending",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": null,
  "progress": {
    "current": 0,
    "total": 1
  },
  "result": null,
  "error": null
}
```

**Response (200 OK) - Completed Successfully:**
```json
{
  "taskId": "abc123def456",
  "status": "success",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": "2026-01-03T10:31:15Z",
  "progress": {
    "current": 1,
    "total": 1
  },
  "result": {
    "noteId": 123456,
    "cardId": 789012
  },
  "error": null
}
```

**Response (200 OK) - Failed:**
```json
{
  "taskId": "abc123def456",
  "status": "failure",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": "2026-01-03T10:31:15Z",
  "progress": {
    "current": 0,
    "total": 1
  },
  "result": null,
  "error": {
    "type": "ValidationError",
    "message": "Missing required field: example"
  }
}
```

**Response (404 Not Found):**
```json
{
  "message": "Task abc123def456 not found"
}
```

---

#### 7. Async Workflow Example

```bash
# 1. Create a cloze note (returns immediately with task ID)
RESPONSE=$(curl -X POST http://localhost:5000/api/v1/clozeNotes \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{...note_data...}')

TASK_ID=$(echo $RESPONSE | jq -r '.taskId')

# 2. Poll task status until completion
while true; do
  STATUS=$(curl -s http://localhost:5000/api/v1/tasks/$TASK_ID \
    -H "Authorization: Bearer <access_token>" | jq -r '.status')
  
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ]; then
    echo "Task completed with status: $STATUS"
    break
  fi
  
  echo "Task still pending..."
  sleep 2
done
```

---

#### 8. Refresh Token

The server creates custom Anki cards with the following features:

- **Front**: Cloze deletion sentence with translation, definition, and translation
- **Back**: Full answer with word details, part of speech, CEFR level, code, and audio
- **Audio**: Automatically generated TTS audio for both the word and example sentence
- **Styling**: Custom CSS matching Cambridge Dictionary design

## Model Context Protocol (MCP) Server

The server natively exposes an MCP endpoint using the **Streamable HTTP** transport at `/mcp`. This allows AI assistants and LLMs (such as Cursor, Claude Desktop, Windsurf, or Open WebUI) to generate and add cloze flashcards directly to your Anki collection.

### MCP Endpoint
- **URL**: `http://localhost:5000/mcp` (or your public/tunnel domain)
- **Transport**: Streamable HTTP

### Authentication
The MCP server supports **Dual Authentication**:
1. **OAuth 2.0 (Standard for Gemini)**: Supports standard OAuth 2.0 Authorization Code Flow with PKCE (for Gemini CLI) and confidential client credentials (for Gemini Enterprise).
   - Authorization URL: `http://localhost:5000/oauth/authorize`
   - Token URL: `http://localhost:5000/oauth/token`
   - Discovery Metadata: `http://localhost:5000/.well-known/oauth-authorization-server`
   - Access tokens are valid for 1 hour, with automatic token refresh supported via refresh tokens.
   - When authorizing in the browser, simply enter your **Server API Key** to approve access.
2. **Static Server API Key**: Direct key authentication for clients that support custom headers (Cursor, Claude Desktop, Windsurf):
   - Via header: `Authorization: Bearer <your_server_api_key>` or `X-API-Key: <your_server_api_key>`
   - Via query parameter: `http://localhost:5000/mcp?api_key=<your_server_api_key>`

### Available MCP Tools

1. **`create_flashcard`**:
   - Enqueues a flashcard creation background task and returns the `taskId` immediately.
   - **Arguments**:
     - `word` (string, required): The target vocabulary word (e.g., `"extraordinary"`).
     - `english_example` (string, required): Example sentence. If cloze markup `{{c1::...}}` is omitted, the tool automatically wraps the word in `{{c1::word}}`.
     - `english_definition` (string, required): English definition.
     - `part_of_speech` (string, optional): e.g., `"adjective"`, `"noun"`. Defaults to `""`.
     - `definition_translation` (string, optional): Translation of the definition. Defaults to `""`.
     - `example_translation` (string, optional): Translation of the example sentence. Defaults to `""`.
     - `guide_word` (string, optional): Cambridge guide word. Defaults to `""`.
     - `cefr_level` (string, optional): CEFR proficiency level (e.g. `"B2"`). Defaults to `""`.
     - `code` (string, optional): Variety code (e.g. `"UK"` or `"US"`). Defaults to `""`.
   - **Returns**: `{"taskId": "...", "status": "pending", "statusUrl": "...", "createdAt": "..."}`.

2. **`get_task_status`**:
   - Checks the processing state of an asynchronous card creation task.
   - **Arguments**: `task_id` (string, required).
   - **Returns**: `{"taskId": "...", "status": "pending" | "started" | "success" | "failure", "result": ...}`.

3. **`check_health`**:
   - Verifies server connectivity and status.

### Available MCP Prompts

- **`create_vocabulary_card`**:
  - Guides the LLM in reading highlighted text or context, identifying vocabulary, and formatting the arguments required by `create_flashcard`.

### Client Configuration Examples

#### Gemini CLI (`~/.gemini/settings.json`)
The Gemini CLI supports automatic OAuth discovery out-of-the-box:

```json
{
  "mcpServers": {
    "anki": {
      "url": "http://localhost:5000/mcp"
    }
  }
}
```

Then in Gemini CLI, authenticate the connection:
```bash
/mcp auth anki
```
This opens your browser to `http://localhost:5000/oauth/authorize`. Enter your Server API Key and click **Authorize**. Gemini CLI will receive the OAuth callback on `http://localhost:7777/oauth/callback` and save the tokens automatically.

If configuring OAuth manually in Gemini:
```json
{
  "mcpServers": {
    "anki": {
      "url": "http://localhost:5000/mcp",
      "oauth": {
        "authorizationUrl": "http://localhost:5000/oauth/authorize",
        "tokenUrl": "http://localhost:5000/oauth/token",
        "clientId": "gemini-cli",
        "scopes": ["mcp"]
      }
    }
  }
}
```

#### Gemini Enterprise / Custom MCP in Google Cloud Console
When adding an MCP custom server in Gemini Enterprise:
- **Server URL**: `https://<your-domain>/mcp` (StreamableHTTP)
- **Authentication**: `OAuth 2.0`
- **Authorization URL**: `https://<your-domain>/oauth/authorize`
- **Access Token URL**: `https://<your-domain>/oauth/token`
- **Client ID**: Configured `OAUTH_CLIENT_ID` in `.env` (or any string if public)
- **Client Secret**: Configured `OAUTH_CLIENT_SECRET` in `.env`
- **PKCE**: Enabled

#### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "anki": {
      "url": "http://localhost:5000/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_SERVER_API_KEY>"
      }
    }
  }
}
```

#### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "anki": {
      "url": "http://localhost:5000/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_SERVER_API_KEY>"
      }
    }
  }
}
```

## Maintenance Guide

### Data Storage

All server data is stored in the `data/` directory:

- `.credentials`: Encrypted credentials (AnkiWeb session, API keys)
- Anki collection database and media files

**Important**: Backup the `data/` directory regularly to prevent data loss.

### Celery Background Worker

The server uses Celery for asynchronous card creation with SQLite as the message broker. This allows the API to return immediately without waiting for card creation, TTS generation, and AnkiWeb sync to complete.

#### Background Worker Configuration

**Environment Variables:**
```bash
CELERY_BROKER_URL=sqla+sqlite:///data/celery_broker.db
CELERY_RESULT_BACKEND=db+sqlite:///data/celery_results.db
CELERY_WORKER_CONCURRENCY=1  # Single-threaded for SQLite compatibility
CELERY_TASK_TIME_LIMIT=300   # 5-minute timeout per task
CELERY_RESULT_EXPIRES=86400  # 24-hour result retention
```

#### Managing the Worker

**Docker Compose:**
```bash
# Start all services (Flask API + Celery worker)
docker-compose up -d

# View worker logs
docker-compose logs -f celery_worker

# Stop the worker
docker-compose stop celery_worker
```

**Local Development:**
```bash
# Terminal 1: Start Flask API
python -m anki_sync_server

# Terminal 2: Start Celery worker
celery -A anki_sync_server.tasks.celery_app worker --loglevel=info --concurrency=1
```

#### Task Status Polling

Tasks are stored in SQLite with automatic cleanup after 24 hours. Use the task status endpoint to monitor progress:

```bash
# Get task status
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:5000/api/v1/tasks/<task_id>
```

### Updating Credentials

To update AnkiWeb credentials or API keys, run the setup wizard again:

```bash
# Local
python -m anki_sync_server setup

# Docker
docker-compose exec app python -m anki_sync_server setup
```

### Monitoring

#### Check Server Logs

**Docker:**
```bash
docker-compose logs -f app
```

**Local:**
Check the console output where uwsgi is running.

#### Check Celery Worker Logs

**Docker:**
```bash
docker-compose logs -f celery_worker
```

#### Check AnkiWeb Sync Status

The server automatically syncs with AnkiWeb after adding each card. Check your Anki client to verify cards are syncing correctly.

### Troubleshooting

#### Authentication Errors

- Verify the API key is correct
- Check if the access token has expired (refresh after 1 hour)
- Ensure the `.credentials` file exists in the `data/` directory

#### Task Status Not Updating

- Verify the Celery worker is running: `docker-compose ps celery_worker`
- Check worker logs for errors: `docker-compose logs celery_worker`
- Ensure SQLite database files exist: `ls -la data/celery_*.db`

#### Sync Failures

- Verify AnkiWeb credentials are valid
- Check network connectivity to `https://sync.ankiweb.net`
- Review server logs for sync-related errors

#### Audio Generation Issues

- Verify Google Cloud TTS API key is valid and has sufficient quota
- Check GCP billing is enabled
- Ensure the API key has Text-to-Speech API permissions

### Updating the Server

1. **Backup your data**
   ```bash
   cp -r data/ data-backup/
   ```

2. **Pull latest changes**
   ```bash
   git pull origin main
   ```

3. **Update dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Restart the server**
   ```bash
   # Docker
   docker-compose restart
   
   # Local
   # Stop the current uwsgi process and restart
   uwsgi --http 0.0.0.0:5000 --master -p 4 --lazy-apps -w anki_sync_server.server.main:app
   ```

### Database Management

The server uses Anki's internal SQLite database. To manage the database:

- **Location**: `data/collection.anki2`
- **Backup**: Copy the entire `data/` directory
- **Reset**: Delete the `data/` directory and re-run setup wizard

### Security Best Practices

1. **Protect API Keys**: Never commit API keys or the `.credentials` file to version control
2. **Use HTTPS**: In production, always use HTTPS (configure NGINX or use Cloudflare Tunnel)
3. **Rotate Tokens**: Regenerate the Server API key periodically
4. **Network Security**: Use firewall rules to restrict access to the server
5. **Environment Variables**: Consider using environment variables for sensitive configuration

### Scaling Considerations

The server uses thread locking to ensure safe concurrent access to the Anki collection. For high-traffic scenarios:

- Increase the number of uwsgi worker processes (`-p` parameter)
- Monitor memory usage (Anki collections are memory-intensive)
- Consider rate limiting at the NGINX level
- Implement a queue system for batch card creation

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest test/

# Run specific test file
python -m pytest test/anki/note_creator_test.py

# Run with coverage
python -m pytest --cov=anki_sync_server test/
```

### Code Style

The project uses:
- **flake8** for linting
- **isort** for import sorting

Configuration files:
- `.flake8`: Flake8 configuration
- `.isort.cfg`: Import sorting configuration

### Project Structure

```
.
├── anki_sync_server/          # Main application package
│   ├── anki/                  # Anki integration modules
│   ├── server/                # Flask server and API
│   ├── setup/                 # Setup wizard components
│   ├── tts/                   # Text-to-speech services
│   ├── assets/                # Anki card templates
│   └── __main__.py            # CLI entry point
├── docker/                    # Docker configuration
│   ├── nginx/                 # NGINX reverse proxy config
│   └── tunnel/                # Cloudflare tunnel config
├── test/                      # Test suite
├── Dockerfile                 # App container definition
├── docker-compose.yml         # Docker Compose configuration
└── requirements.txt           # Python dependencies
```

## License

This project is provided as-is for educational and personal use.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.
