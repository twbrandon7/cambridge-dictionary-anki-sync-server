# Specification: Task Status Tracking

## Overview
API and persistent storage for querying the status of asynchronous card creation tasks. Provides real-time visibility into task progress (pending, started, completed) and error details.

## ADDED Requirements

### Requirement: Task Status Endpoint
The system MUST provide a new HTTP GET endpoint to query task status and retrieve results.

#### Scenario: Query pending task status
Given a task ID from a recent card creation request
When client sends `GET /api/v1/tasks/{taskId}`
Then HTTP 200 OK is returned
And response includes:
- `taskId`: String identifier
- `status`: \"pending\" (task enqueued but not yet started)
- `createdAt`: ISO 8601 timestamp of task creation
- `completedAt`: null (not yet complete)
- `progress`: Object with `current` and `total` counts (optional)
- `result`: null
- `error`: null

Example:
```json
{
  "taskId": "abc123def456",
  "status": "pending",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": null,
  "progress": { "current": 0, "total": 1 },
  "result": null,
  "error": null
}
```

#### Scenario: Query task in progress
Given a task that is currently executing in a worker
When client sends `GET /api/v1/tasks/{taskId}`
Then HTTP 200 OK is returned
And `status` is \"started\"
And `completedAt` is null
And `progress` may include partial completion info
And `result` is null
And `error` is null

Example:
```json
{
  "taskId": "abc123def456",
  "status": "started",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": null,
  "progress": { "current": 1, "total": 1 },
  "result": null,
  "error": null
}
```

#### Scenario: Query successful task
Given a task that has completed successfully
When client sends `GET /api/v1/tasks/{taskId}`
Then HTTP 200 OK is returned
And `status` is \"success\"
And `completedAt` is set to completion ISO 8601 timestamp
And `result` object includes task-specific data:
- For card creation: `cardId`, `noteId`
And `error` is null

Example:
```json
{
  "taskId": "abc123def456",
  "status": "success",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": "2026-01-03T10:31:15Z",
  "progress": { "current": 1, "total": 1 },
  "result": {
    "cardId": 123456,
    "noteId": 987654
  },
  "error": null
}
```

#### Scenario: Query failed task
Given a task that failed (Anki error, TTS error, timeout, etc.)
When client sends `GET /api/v1/tasks/{taskId}`
Then HTTP 200 OK is returned
And `status` is \"failure\"
And `completedAt` is set to failure ISO 8601 timestamp
And `result` is null
And `error` object includes:
- `type`: Exception class name (e.g., \"MissingFieldError\", \"TimeoutError\")
- `message`: Human-readable error description
- `traceback`: Optional stack trace for debugging (if debug mode enabled)

Example:
```json
{
  "taskId": "abc123def456",
  "status": "failure",
  "createdAt": "2026-01-03T10:30:00Z",
  "completedAt": "2026-01-03T10:31:15Z",
  "progress": { "current": 0, "total": 1 },
  "result": null,
  "error": {
    "type": "MissingFieldError",
    "message": "Required field 'example' missing from note"
  }
}
```

#### Scenario: Query nonexistent task
Given a task ID that does not exist or has expired
When client sends `GET /api/v1/tasks/{taskId}`
Then HTTP 404 Not Found is returned
And response includes error message: \"Task not found or has expired\"

#### Scenario: Authentication required for status endpoint
Given a request to `GET /api/v1/tasks/{taskId}`
When the request lacks valid authentication token
Then HTTP 401 Unauthorized is returned
And the endpoint is protected by `@token_required` decorator

### Requirement: Task Result Storage
Task status and results MUST be persistently stored in SQLite with automatic expiration.

#### Scenario: Store task metadata in SQLite
Given a Celery task execution
When the task completes (success or failure)
Then metadata is stored in SQLite database under table `celery_taskmeta`
And the stored data includes:
- Task ID
- Status (PENDING, STARTED, SUCCESS, FAILURE)
- Timestamps (created, started, completed)
- Result data or error details
- User identifier (if applicable)

#### Scenario: Automatic task expiration
Given a completed task stored in SQLite
When 24 hours have passed since task completion
Then the task result is automatically deleted from SQLite via Celery cleanup
And subsequent queries for that task return HTTP 404
And expiration is configured via `CELERY_RESULT_EXPIRES` environment variable (default: 86400 seconds)

#### Scenario: Query old but not yet expired task
Given a task that completed 12 hours ago
When client sends `GET /api/v1/tasks/{taskId}`
Then HTTP 200 OK is returned with current status and result
And the task remains in SQLite database until 24-hour expiration

### Requirement: Task Status Serialization
Task state MUST be serialized to JSON for API responses and SQLite storage.

#### Scenario: Serialize task state to JSON
Given a Celery task with:
- State (pending, started, success, failure)
- Timestamps
- Result or error data
When the status endpoint is called
Then all data is converted to JSON
And timestamps are ISO 8601 format
And error objects include type and message
And result objects are task-specific (e.g., cardId, noteId for card creation)

### Requirement: Task Status Transitions
Celery MUST manage task lifecycle through well-defined state transitions.

#### Scenario: Task state machine
Given a new Celery task created
When the task is queued
Then the initial state is PENDING

When the worker picks up the task
Then the state transitions to STARTED

When the task completes successfully
Then the state transitions to SUCCESS
And result is stored

When the task fails or times out
Then the state transitions to FAILURE
And error details are stored

Example state path for successful task:
```
PENDING (0 sec) → STARTED (1 sec) → SUCCESS (60 sec)
```

Example state path for failed task:
```
PENDING (0 sec) → STARTED (1 sec) → FAILURE (5 sec, timeout)
```

### Requirement: Polling Strategy
Clients MUST use HTTP polling to check task status without blocking.

#### Scenario: Client polls for task completion
Given a client received a task ID from async card creation request
When the client polls `GET /api/v1/tasks/{taskId}`
Then the response includes current status
And the client can use exponential backoff polling (e.g., 1s, 2s, 4s, 8s intervals)
And the client detects completion when status is \"success\" or \"failure\"
And no blocking or WebSocket connection is required

#### Scenario: Recommended polling backoff
Given a client polling task status
When the task is still pending or started
Then the client should poll with exponential backoff:
- Initial interval: 1 second
- Max interval: 30 seconds
- Multiplier: 2x per attempt
To reduce server load and API calls.
