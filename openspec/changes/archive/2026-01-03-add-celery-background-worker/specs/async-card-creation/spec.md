# Specification: Async Card Creation

## Overview
Background asynchronous processing of Anki card creation requests via Celery task queue. Decouples API request from long-running operations (media generation, AnkiWeb sync).

## ADDED Requirements

### Requirement: Celery Task for Card Creation
The system SHALL encapsulate the full card creation workflow (validation, note creation, media generation, AnkiWeb sync) as a Celery task executable in background worker processes.

#### Scenario: User submits card creation request
Given a valid cloze note request to `POST /api/v1/clozeNotes`
When the request is processed with `async=true` (default)
Then the task is enqueued to Celery
And the endpoint returns HTTP 202 Accepted
And the response includes a task ID and status URL
And the client can immediately proceed (not blocked)
And the card creation happens in background worker process

#### Scenario: Card is created successfully
Given a queued Celery task for card creation
When the task executes in worker process
Then the note is deserialized from JSON
And `Anki.add_cloze_note()` is called with the note
And media (audio) is generated via TTS
And the card is added to the Anki collection
And AnkiWeb synchronization occurs
And the task status transitions to `SUCCESS`
And the result (card ID, note ID) is stored in SQLite

#### Scenario: Card creation fails with recoverable error
Given a queued task with valid input
When the task encounters an Anki lock contention or transient network error
Then the task auto-retries with exponential backoff (max 3 attempts)
And if all retries fail, task status is `FAILURE`
And error details are logged and stored in SQLite

#### Scenario: Card creation fails with validation error
Given an invalid note request (e.g., missing required field)
When the request is validated before enqueuing
Then the task is not queued
And HTTP 400 Bad Request is returned immediately (unchanged behavior)

#### Scenario: Celery task timeout
Given a task that takes longer than configured timeout (300 seconds)
When the timeout is exceeded
Then the task is terminated
And task status is `FAILURE`
And error message indicates timeout

### Requirement: Task Time Limit Configuration
Each Celery task MUST have a configurable time limit to prevent hung processes.

#### Scenario: Configure default task timeout
Given Celery app initialization
When task time limit is set to 300 seconds
Then any task exceeding 300 seconds is forcefully terminated
And the configuration can be overridden via environment variable `CELERY_TASK_TIME_LIMIT`

### Requirement: Task Serialization
Tasks MUST serialize input and output data to JSON for interoperability and persistence.

#### Scenario: Serialize note data
Given a `ClozeNote` object from request JSON
When enqueuing task
Then the note is passed as a dictionary to Celery
And Celery uses JSON serialization (not pickle)

#### Scenario: Deserialize note in task
Given a dictionary of note data received in worker
When the task executes
Then the data is deserialized to a `ClozeNote` object
Using the marshmallow schema `ClozeNoteScheme().load()`
And validation occurs during deserialization

### Requirement: Error Handling in Task
Task execution MUST include comprehensive error handling to capture and propagate failures.

#### Scenario: Catch Anki-specific exceptions
Given a task that calls `Anki.add_cloze_note()`
When an exception occurs (e.g., `CollectionAlreadyOpenError`)
Then the exception is caught and logged
And error type and message are stored in task result
And task status is set to `FAILURE`
And client can retrieve error details via task status endpoint

#### Scenario: Log task execution
Given a running Celery task
When the task starts, progresses, and completes
Then meaningful log messages are written (task ID, note data, result)
And logs are accessible via worker logs or central logging system

### Requirement: Async Card Creation API Endpoint
The `POST /api/v1/clozeNotes` endpoint SHALL support asynchronous processing with HTTP 202 response and task status polling.

#### Scenario: Submit card creation request (async, default)
Given a client sends `POST /api/v1/clozeNotes` with valid note data
When no query parameter `async` is provided (or `async=true`)
Then the request is immediately validated
And the task is enqueued to Celery
And HTTP 202 Accepted is returned (not 200 OK)
And response contains task ID and status URL
And the client receives response in <100ms (not waiting for card creation)

#### Scenario: Submit card creation request (sync, backward compat)
Given a client sends `POST /api/v1/clozeNotes?async=false`
When the query parameter `async=false` is provided
Then the original synchronous behavior applies
And the card is created immediately before returning
And HTTP 200 OK is returned with `{status: ok}`
And the response time includes full card creation (unchanged behavior)

#### Scenario: Response format for async request
Given a successful async card creation request
When HTTP 202 Accepted is returned
Then the response JSON includes:
- `taskId`: String identifier for the task
- `status`: \"pending\" (initial state)
- `statusUrl`: String URL path to query task status (e.g., `/api/v1/tasks/{taskId}`)

Example:
```json
{
  "taskId": "abc123def456",
  "status": "pending",
  "statusUrl": "/api/v1/tasks/abc123def456"
}
```

#### Scenario: Validation errors still return 400
Given invalid request data (e.g., missing required field)
When validation fails before task enqueuing
Then HTTP 400 Bad Request is returned
And response includes validation error messages (unchanged behavior)
And no task is created

#### Scenario: Authentication errors still return 401/403
Given a request without valid authentication token
When the `@token_required` decorator is checked
Then HTTP 401 Unauthorized or 403 Forbidden is returned (unchanged behavior)
And no task is created
