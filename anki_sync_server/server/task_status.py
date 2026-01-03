from datetime import datetime, timezone
from typing import Any, Dict, Optional

from celery.result import AsyncResult

from anki_sync_server.tasks.celery_app import celery_app


class TaskStatus:
    """Helper class to convert Celery task state to API response format."""

    @staticmethod
    def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch task status from Celery result backend.

        Args:
            task_id: Celery task ID

        Returns:
            Dictionary with task metadata or None if task not found
        """
        try:
            async_result = AsyncResult(task_id, app=celery_app)

            if async_result is None:
                return None

            return TaskStatus._serialize_task_state(async_result)
        except Exception:
            return None

    @staticmethod
    def _serialize_task_state(async_result: AsyncResult) -> Dict[str, Any]:
        """
        Convert Celery AsyncResult to API-friendly JSON format.

        Args:
            async_result: Celery AsyncResult object

        Returns:
            Dictionary with task status in API format
        """
        # Convert Celery's uppercase states to lowercase for API consistency
        state_mapping = {
            "PENDING": "pending",
            "STARTED": "started",
            "SUCCESS": "success",
            "FAILURE": "failure",
            "RETRY": "retry",
        }

        api_state = state_mapping.get(async_result.state, "unknown")

        response = {
            "taskId": async_result.id,
            "status": api_state,
            "createdAt": None,
            "completedAt": None,
            "progress": {
                "current": 0,
                "total": 1,
            },
            "result": None,
            "error": None,
        }

        # Add result if task succeeded
        if async_result.successful():
            response["status"] = "success"
            response["completedAt"] = datetime.now(timezone.utc).isoformat()
            response["result"] = async_result.result

        # Add error if task failed
        elif async_result.failed():
            response["status"] = "failure"
            response["completedAt"] = datetime.now(timezone.utc).isoformat()

            # Extract error info
            exc = async_result.info
            if isinstance(exc, dict) and "error" in exc:
                response["error"] = exc["error"]
            elif isinstance(exc, Exception):
                response["error"] = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }

        return response
