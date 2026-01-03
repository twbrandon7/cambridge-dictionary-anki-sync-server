# Implementation Tasks: Add Celery Background Worker

## Checklist

- [x] **Task 1: Update dependencies**
  - Add `celery>=5.3.0`, `sqlalchemy>=2.0.0` to `pyproject.toml`
  - Run `uv sync` to update lock file
  - Verify imports work in Python environment

- [x] **Task 2: Create Celery app configuration**
  - Create `anki_sync_server/tasks/__init__.py`
  - Create `anki_sync_server/tasks/celery_app.py` with Celery app initialization
  - Configure SQLite broker and result backend from environment variables
  - Set SQLite database paths: `CELERY_BROKER_URL=sqla+sqlite:///data/celery_broker.db`
  - Set result backend: `CELERY_RESULT_BACKEND=db+sqlite:///data/celery_results.db`
  - Set task serialization to JSON
  - Set worker concurrency to 1 (SQLite single-threaded)

- [x] **Task 3: Implement card creation task**
  - Create `anki_sync_server/tasks/card_creation_task.py`
  - Define `add_cloze_note_task(self, note_data)` Celery task
  - Deserialize note from JSON using `ClozeNote` schema
  - Call `anki.add_cloze_note()` inside task
  - Capture and log exceptions; return error metadata
  - Set task time limit to 300 seconds

- [x] **Task 4: Create task status tracking module**
  - Create `anki_sync_server/server/task_status.py`
  - Implement `TaskStatus` class to serialize Celery task state
  - Add helper to fetch task status from Celery result backend
  - Add helper to format task response JSON (pending, started, success, failure)

- [x] **Task 5: Modify card creation API endpoint**
  - Update `anki_sync_server/server/api_v1.py` `ClozeNote.post()` method
  - Accept optional query parameter `async` (default: `true`)
  - If `async=false`: use old synchronous code path (backward compat)
  - If `async=true`: queue task with `add_cloze_note_task.delay()`
  - Return 202 Accepted with task ID and status URL instead of 200 OK
  - Include `taskId` and `statusUrl` in response JSON

- [x] **Task 6: Add task status endpoint**
  - Add new Flask route `GET /api/v1/tasks/<task_id>` to `api_v1.py`
  - Protect endpoint with `@token_required` decorator
  - Fetch task status from Celery backend using `task_status.get_task_status()`
  - Return 200 with task metadata; return 404 if task not found

- [x] **Task 7: Initialize Celery in Flask app**
  - Update `anki_sync_server/server/main.py`
  - Import and initialize Celery app
  - Ensure Celery broker/backend config matches environment variables
  - Verify SQLite database paths are accessible

- [x] **Task 8: Update environment configuration**
  - Create/update `.env` template with new Celery/SQLite variables
  - Document `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CELERY_WORKER_CONCURRENCY`, `CELERY_TASK_TIME_LIMIT`
  - Set sensible defaults (SQLite files in `data/` directory)

- [x] **Task 9: Update Docker Compose**
  - Add Celery worker service to `docker-compose.yml`
  - Ensure worker depends on main Flask app service
  - Mount `./data` volume for SQLite database persistence
  - Set `CELERY_BROKER_URL=sqla+sqlite:///data/celery_broker.db`
  - Set `CELERY_RESULT_BACKEND=db+sqlite:///data/celery_results.db`
  - Set `CELERY_WORKER_CONCURRENCY=1`

- [x] **Task 10: Create unit tests**
  - Create `test/tasks/` directory
  - Create `test/tasks/card_creation_task_test.py`
  - Mock Celery task; verify task is enqueued and returns task ID
  - Mock Anki operations; verify task calls `add_cloze_note()`
  - Test error handling (invalid note, TTS failure)
  - Create `test/server/task_status_test.py`
  - Test `GET /api/v1/tasks/{id}` for pending, success, and failure states

- [x] **Task 11: Create integration tests**
  - Create `test/integration/` directory
  - Set up SQLite database for Celery tasks in test fixtures
  - Create temporary test databases in `test/tmp/` directory
  - Create `test/integration/async_card_creation_test.py`
  - End-to-end test: POST to create card → poll task status → verify card in Anki
  - Test timeout and retry behavior
  - Test concurrent card creation requests (queued due to single worker)

- [x] **Task 12: Update documentation**
  - Update `README.md` with Async Card Creation section
  - Document task status endpoint and query parameters
  - Add example curl commands for both sync and async workflows
  - Document environment variables for SQLite/Celery config
  - Add Docker Compose usage notes for Celery worker service

- [x] **Task 13: Run validation and testing**
  - Run `openspec validate add-celery-background-worker --strict` to verify spec syntax
  - Run full test suite: `python -m unittest discover test/`
  - Test with Docker Compose: verify worker and Flask both start and share SQLite
  - Verify SQLite database files are created in `data/` directory
  - Manual testing: POST request, poll status, verify card created in Anki

- [x] **Task 14: Backward compatibility verification**
  - Test `POST /api/v1/clozeNotes?async=false` to verify synchronous mode still works
  - Verify response format for sync mode (should match original `{status: ok}`)
  - Test with legacy clients expecting synchronous response

## Notes
- **Dependency Verification**: Task 1 includes Celery and SQLAlchemy. Kombu (AMQP library) is included with Celery by default; verify if explicit inclusion is needed for SQLite backend during implementation
- **Task Sequencing**: Tasks 1-4, 7-9 can run in parallel; Tasks 5-6 depend on 1-4; comprehensive testing (10-11) happens after implementation
- **Documentation**: Task 12 references SQLite/Celery (not Redis). Update references to state naming convention (lowercase in API, uppercase internally)
- **Media Sync Integration**: During Task 3 implementation, verify interaction between Celery task timeout (300s) and existing Anki media_sync_timeout_seconds parameter
- **Concurrency**: Task 9 sets concurrency=1 for SQLite safety. Future scaling notes added to design.md for reference
