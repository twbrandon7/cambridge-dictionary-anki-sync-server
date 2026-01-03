# Project Context

## Purpose
Cambridge Dictionary Anki Sync Server is a Flask-based REST API that automatically creates and syncs Anki flashcards with vocabulary from the Cambridge Dictionary. The server integrates with AnkiWeb to create custom cloze deletion cards enriched with definitions, translations, audio pronunciations (via Google Cloud TTS), and CEFR proficiency levels. It's designed to streamline vocabulary learning by automating the flashcard creation pipeline.

## Tech Stack
- **Language**: Python 3.11+
- **Package Manager**: uv (fast Python package manager with lock file support)
- **Web Framework**: Flask with Flask-RESTful, Flask-CORS
- **Authentication**: JWT tokens (PyJWT for encoding/decoding)
- **Anki Integration**: Anki SDK for direct collection manipulation and AnkiWeb sync
- **Text-to-Speech**: Google Cloud Text-to-Speech API
- **Deployment**: Docker, Docker Compose with NGINX reverse proxy
- **Optional**: Cloudflare Tunnel for remote access
- **Server**: uWSGI for production deployments
- **Data**: SQLite (via Anki's collection.anki2 database)
- **Utilities**: python-dotenv for environment configuration, bcrypt for password hashing, marshmallow for validation

## Project Conventions

### Code Style
- **Language**: Python with type hints where applicable
- **Naming Conventions**:
  - Classes: PascalCase (e.g., `ModelCreator`, `ClozeNote`)
  - Functions/methods: snake_case (e.g., `create_anki_collection`)
  - Constants: UPPER_SNAKE_CASE
  - Private methods: prefix with underscore (e.g., `_lock`, `_collection`)
- **Imports**: Organized by standard library, third-party, then local imports; alphabetically sorted within groups
- **File Organization**: One primary class per module (e.g., `anki.py` for `Anki` class)
- **String Formatting**: Mix of f-strings and .format() in existing code

### Architecture Patterns
- **Layered Architecture**:
  - `server/` layer: HTTP API endpoints (Flask blueprints) and authentication
  - `anki/` layer: Anki-specific operations (note creation, model management, media handling)
  - `setup/` layer: Wizard pattern for initial configuration and credential management
  - `tts/` layer: Abstract TTS service with pluggable implementations
  
- **Design Patterns**:
  - **Setup Wizard**: Chain of responsibility pattern for multi-step setup (`SetupStep` abstract base class)
  - **Service Abstraction**: TTS service abstraction (`TtsService` ABC) allows swappable implementations
  - **Credential Storage**: Centralized credential management with `CredentialStorage`
  - **Thread Safety**: Use of locks (`threading.Lock`) for thread-safe operations in Anki class
  - **Lazy Initialization**: AnkiWeb sync testing through lazy initialization in tests
  
- **Data Flow**:
  - API receives vocabulary → Validates with marshmallow → Creates note via `Anki` class → Syncs to AnkiWeb asynchronously
  - Media (audio files) generated via TTS → Stored in Anki collection → Synced with AnkiWeb

### Testing Strategy
- **Framework**: Python's `unittest` (not pytest)
- **Test Organization**: `test/` directory mirrors source structure (`test/anki/`, `test/server/`, `test/setup/`, `test/tts/`)
- **Naming Convention**: `*_test.py` files (e.g., `note_creator_test.py`)
- **Test Classes**: Inherit from `unittest.TestCase`; use `test_*` method naming
- **Coverage Focus**: Unit tests for core functionality (note creation, model creation, field injection, media creation, TTS, setup steps, authentication)
- **Mock Usage**: Mock external services (Anki SDK, Google TTS API) in tests
- **Test Execution**: Can run with `python -m unittest discover test/`

### Git Workflow
- **Branch Strategy**: Main branch (`main`) is default
- **Commit Conventions**: (Based on repo structure) Semantic commits recommended
- **PR Process**: Changes should be submitted via pull requests with clear descriptions
- **Deployment**: Docker-based deployment pipeline with support for both local and cloud environments

## Domain Context

### Anki-Specific Knowledge
- **Cloze Notes**: Deletion flashcards with format `{{c1::text}}` that automatically hide and show deleted text
- **Models**: Card templates defining how fields are rendered (front/back HTML + CSS)
- **Collections**: SQLite-backed local database containing all cards, decks, media
- **AnkiWeb Sync**: Two-way synchronization requiring valid AnkiWeb credentials; handles conflict resolution
- **Media Files**: Audio/images stored in `.media/` folder with entries in `.media.db2`
- **Fields**: Custom attributes on notes (e.g., "Word", "Definition", "Example", "CEFR Level")

### Cambridge Dictionary Integration
- Vocabulary items contain: word, definition, example usage, translations, CEFR level
- Cards are created as cloze deletion format to test vocabulary retention
- Audio pronunciations are synced from Google Cloud TTS

### Token & Authentication Model
- **JWT Tokens**: Bearer token in Authorization header for API requests
- **Token Issuer**: Generates access tokens with expiration and refresh tokens
- **Public Endpoints**: `/login` and `/refresh` do not require authentication
- **Protected Endpoints**: All other `/api/v1/*` endpoints require valid Bearer token

## Important Constraints
- **Python Version**: 3.11+ required
- **Package Manager**: uv required for dependency management (installed via `curl https://astral.sh/uv/install.sh | sh`)
- **AnkiWeb Credentials**: Must be valid and available during server setup (cannot add credentials after initial setup)
- **GCP API Key**: Required for audio generation; needs Google Cloud TTS API enabled
- **Concurrency**: Anki operations are protected by locks to prevent race conditions during sync
- **Media Sync Timeout**: Default 600 seconds for media synchronization; can be configured
- **Single Deck**: Server operates on a single Anki deck (default: "English Vocabulary"); configurable at initialization
- **Docker Constraints**: Requires Docker and Docker Compose for containerized deployment

## External Dependencies
- **AnkiWeb**: Online Anki synchronization service; requires valid account credentials
- **Google Cloud Text-to-Speech API**: Audio pronunciation generation; requires GCP project and API key
- **NGINX**: Reverse proxy for containerized deployment (optional but recommended for production)
- **Cloudflare Tunnel**: Optional secure tunneling solution for exposing local server to internet
- **Anki SDK**: Official Anki Python library for collection manipulation and sync protocol
- **Flask Ecosystem**: Flask core framework plus extensions (flask-restful, flask-cors)
