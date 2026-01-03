# Design Document: Celery-Based Async Card Creation

## Architecture Overview

### Current Synchronous Flow
```
Client Request → Flask API → Anki.add_cloze_note() → [Card Create + TTS + Sync] → Response
                                                     ↑ Blocks until complete ↑
```

### Proposed Async Flow
```
Client Request → Flask API → Celery Task (Queued) → Response (Task ID) [~10ms]
                                ↓ (Background)
                     Anki.add_cloze_note() → [Card Create + TTS + Sync]
                                ↓
                        Store Result in SQLite
                                ↓
Client Polls → GET /tasks/{id} → SQLite Lookup → Status Response
```

## System Components

### 1. Celery Worker Infrastructure
- **Broker**: SQLite (file-based message queue via SQLAlchemy)
- **Result Backend**: SQLite (task results and metadata)
- **Concurrency**: 1 worker process (single-threaded for SQLite; concurrent requests queued)
- **Task Timeout**: 300 seconds (5 minutes) per task

### 2. Task Definitions (`anki_sync_server/tasks/card_creation_task.py`)
```python
@celery_app.task(bind=True, name='add_cloze_note')
def add_cloze_note_task(self, note_data, user_id=None):
    # Deserialize note
    # Call Anki.add_cloze_note()
    # Catch and log errors
    # Return success/error metadata
```

**Task State Machine**:
- `PENDING` → `STARTED` → `SUCCESS` or `FAILURE`
- Task ID persisted in Redis with metadata (user, timestamp, errors)

### 3. API Endpoints

#### Modified: `POST /api/v1/clozeNotes`
**Old Behavior** (still available with `?async=false`):
```
POST /api/v1/clozeNotes
Content-Type: application/json
{
  "word": "ephemeral",
  "definition": "lasting for a very short time",
  ...
}

Response (200):
{
  "status": "ok"
}
```

**New Default Behavior** (async):
```
POST /api/v1/clozeNotes
Content-Type: application/json
{
  "word": "ephemeral",
  ...
}

Response (202 Accepted):
{
  "taskId": "abc123def456",
  "status": "pending",
  "statusUrl": "/api/v1/tasks/abc123def456"
}
```

#### New: `GET /api/v1/tasks/{task_id}`
```
GET /api/v1/tasks/abc123def456

Response (200):
{
  "taskId": "abc123def456",
  "status": "pending" | "started" | "success" | "failure",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": "2026-01-03T10:31:15Z",
  "progress": {
    "current": 1,
    "total": 1
  },
  "result": {
    "cardId": 123456,
    "noteId": 987654
  },
  "error": null
}

# Task in progress:
{
  "taskId": "abc123def456",
  "status": "started",
  "createdAt": "2026-01-03T10:30:00Z",
  "progress": { "current": 1, "total": 1 },
  "error": null
}

# Task failed:
{
  "taskId": "abc123def456",
  "status": "failure",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": "2026-01-03T10:31:15Z",
  "error": {
    "type": "MissingFieldError",
    "message": "Missing required field: example"
  }
}
```

### 4. SQLite Configuration
- **File Path**: `CELERY_BROKER_DB_PATH` (default: `data/celery_broker.db`)
- **Database**: SQLAlchemy SQLite backend for both broker and results
- **Result TTL**: 86400 seconds (24 hours) via Celery task expiration
- **Isolation**: Single database file with SQLite's default locking mechanism

### 5. Error Handling & Retries
- **Validation Errors** (400): Rejected before queuing (unchanged)
- **Anki Lock Contention**: Celery auto-retry with exponential backoff (max 3 retries)
- **TTS Failures**: Task marked as failure; error details stored in result
- **Network Timeouts**: Caught, logged, task status = failure

### 6. Backward Compatibility
- Query parameter `?async=false` triggers synchronous behavior (old code path)
- Default is async (`?async=true` implicit)
- Clients expecting immediate response can opt into sync mode
- No breaking changes to authentication or request validation

## Deployment Considerations

### Docker Compose Changes
Add Celery worker service (no additional external service required):
```yaml
celery_worker:
  build: .
  command: celery -A anki_sync_server.tasks.celery_app worker --loglevel=info --concurrency=1
  depends_on:
    - app
  volumes:
    - ./data:/app/data
  environment:
    - CELERY_BROKER_URL=sqla+sqlite:///data/celery_broker.db
    - CELERY_RESULT_BACKEND=db+sqlite:///data/celery_results.db
```

### Environment Variables
```env
# Celery (SQLite-based)
CELERY_BROKER_URL=sqla+sqlite:///data/celery_broker.db
CELERY_RESULT_BACKEND=db+sqlite:///data/celery_results.db
CELERY_WORKER_CONCURRENCY=1
CELERY_TASK_TIME_LIMIT=300
```

## Thread Safety & Concurrency
- **Anki Lock**: Existing `Anki._lock` remains; protects collection during card creation
- **Celery Workers**: Multiple workers share Redis broker; no cross-worker contention for Anki operations
- **Collection Access**: Each worker accesses the same SQLite collection file; Anki SDK's write-ahead logging (WAL) handles concurrent reads

## Testing Strategy
1. **Unit Tests**: Mock Celery tasks; verify task enqueuing and result storage
2. **Integration Tests**: Real Celery + Redis; verify end-to-end workflow
3. **Load Tests**: Multiple concurrent requests; verify queue processing and no race conditions

## Future Enhancements
- WebSocket support for real-time task status updates
- Task priority queue (urgent vs. batch imports)
- Distributed worker scaling across multiple machines
- Task cancellation API
- Batch task creation for bulk imports
