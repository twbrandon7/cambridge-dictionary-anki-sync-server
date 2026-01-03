import unittest
from unittest.mock import MagicMock, patch

from anki_sync_server.server.task_status import TaskStatus


class TestTaskStatus(unittest.TestCase):
    """Unit tests for task status tracking."""

    @patch("anki_sync_server.server.task_status.AsyncResult")
    def test_get_task_status_pending(self, mock_async_result_class):
        """Test fetching status of a pending task."""
        # Setup
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_result.state = "PENDING"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        mock_async_result_class.return_value = mock_result

        # Execute
        status = TaskStatus.get_task_status("task-123")

        # Assert
        assert status is not None
        assert status["taskId"] == "task-123"
        assert status["status"] == "pending"
        assert status["result"] is None
        assert status["error"] is None

    @patch("anki_sync_server.server.task_status.AsyncResult")
    def test_get_task_status_started(self, mock_async_result_class):
        """Test fetching status of a started task."""
        # Setup
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_result.state = "STARTED"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        mock_async_result_class.return_value = mock_result

        # Execute
        status = TaskStatus.get_task_status("task-123")

        # Assert
        assert status is not None
        assert status["taskId"] == "task-123"
        assert status["status"] == "started"

    @patch("anki_sync_server.server.task_status.AsyncResult")
    def test_get_task_status_success(self, mock_async_result_class):
        """Test fetching status of a successful task."""
        # Setup
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_result.state = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"noteId": 456, "cardId": 789}
        mock_async_result_class.return_value = mock_result

        # Execute
        status = TaskStatus.get_task_status("task-123")

        # Assert
        assert status is not None
        assert status["taskId"] == "task-123"
        assert status["status"] == "success"
        assert status["result"] == {"noteId": 456, "cardId": 789}
        assert status["completedAt"] is not None

    @patch("anki_sync_server.server.task_status.AsyncResult")
    def test_get_task_status_failure(self, mock_async_result_class):
        """Test fetching status of a failed task."""
        # Setup
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_result.state = "FAILURE"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.info = {
            "error": {"type": "ValidationError", "message": "Missing required field"}
        }
        mock_async_result_class.return_value = mock_result

        # Execute
        status = TaskStatus.get_task_status("task-123")

        # Assert
        assert status is not None
        assert status["taskId"] == "task-123"
        assert status["status"] == "failure"
        assert status["error"] == {
            "type": "ValidationError",
            "message": "Missing required field",
        }
        assert status["completedAt"] is not None

    @patch("anki_sync_server.server.task_status.AsyncResult")
    def test_get_task_status_not_found(self, mock_async_result_class):
        """Test fetching status of a non-existent task."""
        # Setup
        mock_async_result_class.return_value = None

        # Execute
        status = TaskStatus.get_task_status("nonexistent-task")

        # Assert
        assert status is None


if __name__ == "__main__":
    unittest.main()
