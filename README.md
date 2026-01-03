# Cambridge Dictionary Anki Sync Server

A Flask-based API server that automatically creates and syncs Anki flashcards with vocabulary from the Cambridge Dictionary. This server integrates with AnkiWeb to create custom cloze deletion cards with definitions, translations, audio pronunciations, and CEFR levels.

## Features

- **Automatic Anki Card Creation**: Creates custom cloze cards with Cambridge Dictionary data
- **AnkiWeb Synchronization**: Automatically syncs cards to your AnkiWeb account
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
   uwsgi --http 0.0.0.0:5000 --master -p 4 --lazy-apps -w anki_sync_server.server.main:app
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

#### 5. Create Cloze Note

**POST** `/api/v1/clozeNotes`

Creates a new cloze deletion flashcard and syncs it to AnkiWeb.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "word": "extraordinary",
  "partOfSpeech": "adjective",
  "guideWord": "very unusual",
  "englishDefinition": "very unusual, special, unexpected, or strange",
  "definitionTranslation": "非凡的；特別的；意想不到的；令人驚奇的",
  "cefrLevel": "B2",
  "code": "UK",
  "englishExample": "He told the {{c1::extraordinary}} story of his escape.",
  "exampleTranslation": "他講述了他非凡的逃生經歷。"
}
```

**Field Descriptions:**
- `word` (required): The vocabulary word
- `partOfSpeech` (required): Part of speech (e.g., noun, verb, adjective)
- `guideWord` (required): Brief guide or context for the word
- `englishDefinition` (required): Full English definition
- `definitionTranslation` (required): Translation of the definition
- `cefrLevel` (required): CEFR level (A1, A2, B1, B2, C1, C2)
- `code` (required): Language/region code (e.g., US, UK)
- `englishExample` (required): Example sentence with cloze deletion markers `{{c1::word}}`
- `exampleTranslation` (required): Translation of the example sentence

**Response:**
```json
{
  "status": "ok"
}
```

**Error Response (400 Bad Request):**
```json
{
  "message": {
    "field_name": ["Error message"]
  }
}
```

## Card Template

The server creates custom Anki cards with the following features:

- **Front**: Cloze deletion sentence with translation, definition, and translation
- **Back**: Full answer with word details, part of speech, CEFR level, code, and audio
- **Audio**: Automatically generated TTS audio for both the word and example sentence
- **Styling**: Custom CSS matching Cambridge Dictionary design

## Maintenance Guide

### Data Storage

All server data is stored in the `data/` directory:

- `.credentials`: Encrypted credentials (AnkiWeb session, API keys)
- Anki collection database and media files

**Important**: Backup the `data/` directory regularly to prevent data loss.

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

#### Check AnkiWeb Sync Status

The server automatically syncs with AnkiWeb after adding each card. Check your Anki client to verify cards are syncing correctly.

### Troubleshooting

#### Authentication Errors

- Verify the API key is correct
- Check if the access token has expired (refresh after 1 hour)
- Ensure the `.credentials` file exists in the `data/` directory

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
