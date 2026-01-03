# Proposal: Add Celery Background Worker for Async Card Creation

## Overview
Integrate Celery as a distributed task queue to enable asynchronous processing of Anki card creation requests. This decouples the API request from long-running Anki operations (card creation, media generation, AnkiWeb synchronization), improving API responsiveness and reliability.

## Problem Statement
Currently, the `/api/v1/clozeNotes` POST endpoint is synchronous and blocks until:
1. Card creation completes
2. Media (audio) is generated via Google Cloud TTS
3. AnkiWeb synchronization finishes (can take 30+ seconds for media)

This causes:
- **API Timeout Risk**: Long-running requests may exceed server timeout limits
- **Poor UX**: Clients wait for full operation to complete
- **Scalability Issues**: Concurrent requests exhaust thread pools
- **Failure Atomicity**: Partial failures mid-sync are hard to recover from

## Solution Overview
Implement Celery for asynchronous task processing with:
- **Message Broker**: SQLite (file-based, lightweight, no external service required; uses SQLAlchemy backend)
- **Task Definitions**: Celery tasks for card creation and media sync
- **Status Tracking**: Persistent job status tracking via API endpoint
- **API Changes**: Modified `/api/v1/clozeNotes` returns task ID immediately; clients poll `/api/v1/tasks/{task_id}` for status

## Scope & Affected Areas

### New Capabilities
1. **Async Card Creation Task** (`anki_sync_server/tasks/`)
   - Encapsulates card creation workflow in Celery task
   - Handles TTS media generation and AnkiWeb sync
   - Error handling and retry logic

2. **Task Status Tracking** (`anki_sync_server/server/`)
   - New Flask endpoint: `GET /api/v1/tasks/{task_id}` for status
   - Persistent storage of task metadata (status, progress, errors)
   - Background result cleanup (old tasks)

### Modified Capabilities
1. **Card Creation API** (`anki_sync_server/server/api_v1.py`)
   - Changed from synchronous to async request model
   - Returns task ID instead of immediate `{status: ok}`
   - Maintains backward compatibility option via query parameter

2. **Server Infrastructure** (`anki_sync_server/server/main.py`)
   - Initialize Celery app and task consumers in main
   - Configure Redis broker connectivity

### New Dependencies
- `celery>=5.3.0` — distributed task queue
- `sqlalchemy>=2.0.0` — SQL toolkit for Celery SQLite backend
- `kombu>=5.3.0` — AMQP library (included with Celery, explicit for clarity)

### Updated Configuration
- `.env` additions: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `pyproject.toml`: Add Celery and SQLAlchemy dependencies
- Docker Compose: No additional services needed (SQLite file-based)

## Implementation Sequence
See `tasks.md` for step-by-step checklist.

## Key Design Decisions
1. **SQLite over Redis/RabbitMQ**: File-based, no external service needed; suitable for small deployments; uses SQLAlchemy ORM backend for Celery
2. **Polling vs WebSocket**: Polling for status is simpler; WebSocket can be added later
3. **Task Retention**: 24-hour result TTL; old tasks cleaned via Celery configuration
4. **No Breaking Changes**: Legacy synchronous endpoint available via `?async=false` for backward compatibility

## Open Questions / Clarifications Needed
- Should we retain synchronous fallback mode, or make async-only? (Proposal assumes backward-compatible option)
- What should be the default timeout for card creation tasks? (Proposal: 300 seconds)
- Should task results be stored in Redis or a separate database? (Proposal: Redis for simplicity)
- Should completed tasks be auto-cleaned? If so, how long to retain? (Proposal: 24 hours)

## Related Work
- See `design.md` for architectural details on Celery integration and task isolation
