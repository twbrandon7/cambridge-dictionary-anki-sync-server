import os
import unittest
from unittest.mock import MagicMock, patch

import bcrypt
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from anki_sync_server.mcp.auth import ApiKeyAuthMiddleware
from anki_sync_server.mcp.server import (
    check_health,
    create_flashcard,
    create_mcp_app,
    create_vocabulary_card,
    ensure_cloze_syntax,
    get_task_status,
)
from anki_sync_server.server.main import app as composite_app


class TestEnsureClozeSyntax(unittest.TestCase):
    def test_word_wrapped_with_word_boundary(self):
        result = ensure_cloze_syntax("apple", "I ate an apple yesterday.")
        self.assertEqual(result, "I ate an {{c1::apple}} yesterday.")

    def test_case_insensitive_preservation(self):
        result = ensure_cloze_syntax("extraordinary", "He had an Extraordinary day.")
        self.assertEqual(result, "He had an {{c1::Extraordinary}} day.")

    def test_phrase_wrapping(self):
        result = ensure_cloze_syntax("take off", "The plane will take off soon.")
        self.assertEqual(result, "The plane will {{c1::take off}} soon.")

    def test_already_has_cloze(self):
        original = "She is an {{c1::engineer}}."
        result = ensure_cloze_syntax("engineer", original)
        self.assertEqual(result, original)

    def test_word_not_in_sentence(self):
        result = ensure_cloze_syntax("ubiquitous", "Smartphones are everywhere.")
        self.assertEqual(result, "Smartphones are everywhere. ({{c1::ubiquitous}})")


class TestApiKeyAuthMiddleware(unittest.TestCase):
    def setUp(self):
        self.secret = "test-secret-key-123"
        self.hashed = bcrypt.hashpw(self.secret.encode("utf-8"), bcrypt.gensalt())

        self.mock_storage = MagicMock()
        self.mock_storage.get_hashed_api_key.return_value = self.hashed

        async def dummy_endpoint(scope, receive, send):
            response = JSONResponse({"status": "ok"})
            await response(scope, receive, send)

        self.app = ApiKeyAuthMiddleware(
            dummy_endpoint, credential_storage_getter=lambda: self.mock_storage
        )
        self.client = TestClient(self.app)

    def test_missing_key_returns_401(self):
        response = self.client.get("/mcp")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid or missing Server API key", response.json()["message"])

    def test_invalid_key_returns_401(self):
        response = self.client.get(
            "/mcp", headers={"Authorization": "Bearer wrong-key"}
        )
        self.assertEqual(response.status_code, 401)

    def test_bearer_authorization_header(self):
        response = self.client.get(
            "/mcp", headers={"Authorization": f"Bearer {self.secret}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_x_api_key_header(self):
        response = self.client.get("/mcp", headers={"X-API-Key": self.secret})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_query_parameter_api_key(self):
        response = self.client.get(f"/mcp?api_key={self.secret}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_query_parameter_key(self):
        response = self.client.get(f"/mcp?key={self.secret}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_options_preflight_allowed(self):
        response = self.client.options("/mcp")
        self.assertEqual(response.status_code, 200)


class TestMcpTools(unittest.TestCase):
    @patch("anki_sync_server.mcp.server.add_cloze_note_task")
    def test_create_flashcard_minimal(self, mock_task):
        mock_task_instance = MagicMock()
        mock_task_instance.id = "task-12345"
        mock_task.delay.return_value = mock_task_instance

        result = create_flashcard(
            word="ubiquitous",
            english_example="Smartphones are ubiquitous nowadays.",
            english_definition="Present, appearing, or found everywhere.",
        )

        self.assertEqual(result["taskId"], "task-12345")
        self.assertEqual(result["status"], "pending")
        self.assertIn("/api/v1/tasks/task-12345", result["statusUrl"])

        # Check payload passed to Celery task
        mock_task.delay.assert_called_once()
        call_args = mock_task.delay.call_args[0][0]
        self.assertEqual(call_args["word"], "ubiquitous")
        self.assertEqual(
            call_args["englishExample"], "Smartphones are {{c1::ubiquitous}} nowadays."
        )
        self.assertEqual(
            call_args["englishDefinition"], "Present, appearing, or found everywhere."
        )
        self.assertEqual(call_args["partOfSpeech"], "")
        self.assertEqual(call_args["definitionTranslation"], "")
        self.assertEqual(call_args["exampleTranslation"], "")
        self.assertEqual(call_args["guideWord"], "")
        self.assertEqual(call_args["cefrLevel"], "")
        self.assertEqual(call_args["code"], "")

    @patch("anki_sync_server.mcp.server.add_cloze_note_task")
    def test_create_flashcard_full(self, mock_task):
        mock_task_instance = MagicMock()
        mock_task_instance.id = "task-67890"
        mock_task.delay.return_value = mock_task_instance

        result = create_flashcard(
            word="extraordinary",
            english_example="He told the {{c1::extraordinary}} story of his escape.",
            english_definition="very unusual, special, unexpected, or strange",
            part_of_speech="adjective",
            definition_translation="非凡的",
            example_translation="他講述了他非凡的逃生經歷。",
            guide_word="very unusual",
            cefr_level="B2",
            code="UK",
        )

        self.assertEqual(result["taskId"], "task-67890")
        call_args = mock_task.delay.call_args[0][0]
        self.assertEqual(call_args["word"], "extraordinary")
        self.assertEqual(call_args["partOfSpeech"], "adjective")
        self.assertEqual(call_args["guideWord"], "very unusual")
        self.assertEqual(call_args["cefrLevel"], "B2")
        self.assertEqual(call_args["code"], "UK")
        self.assertEqual(
            call_args["englishExample"],
            "He told the {{c1::extraordinary}} story of his escape.",
        )

    @patch("anki_sync_server.mcp.server.TaskStatus.get_task_status")
    def test_get_task_status_found(self, mock_get_status):
        mock_get_status.return_value = {
            "taskId": "task-abc",
            "status": "success",
            "result": {"cardId": 123},
        }

        status = get_task_status("task-abc")
        self.assertEqual(status["status"], "success")
        self.assertEqual(status["taskId"], "task-abc")

    @patch("anki_sync_server.mcp.server.TaskStatus.get_task_status")
    def test_get_task_status_not_found(self, mock_get_status):
        mock_get_status.return_value = None

        status = get_task_status("task-unknown")
        self.assertEqual(status["status"], "not_found")
        self.assertEqual(status["taskId"], "task-unknown")

    def test_check_health(self):
        health = check_health()
        self.assertEqual(health["status"], "ok")
        self.assertIn("Cambridge Dictionary", health["server"])

    def test_create_vocabulary_card_prompt(self):
        prompt = create_vocabulary_card(
            word="serendipity", context="Finding the book was pure serendipity."
        )
        self.assertIn("serendipity", prompt)
        self.assertIn("Finding the book was pure serendipity.", prompt)
        self.assertIn("create_flashcard", prompt)


class TestCompositeAppRouting(unittest.TestCase):
    def test_flask_routes_work(self):
        client = composite_app.test_client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})

    def test_flask_auth_endpoint(self):
        client = composite_app.test_client()
        res = client.get("/api/v1/health")
        # Without token, should return 401
        self.assertEqual(res.status_code, 401)

    def test_asgi_mcp_unauthorized(self):
        with TestClient(composite_app) as client:
            res = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                },
            )
            self.assertEqual(res.status_code, 401)

    def test_asgi_mcp_authorized_initialize(self):
        secret = "test-asgi-secret"
        hashed = bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt())

        from anki_sync_server.setup.credential_storage import CredentialStorage

        with patch.object(CredentialStorage, "get_hashed_api_key", return_value=hashed):
            with TestClient(composite_app) as client:
                res = client.post(
                    "/mcp",
                    headers={"Authorization": f"Bearer {secret}"},
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                    },
                )
                self.assertEqual(res.status_code, 200)
                self.assertIn("capabilities", res.text)

    def test_asgi_flask_route(self):
        with TestClient(composite_app) as client:
            res = client.get("/")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
