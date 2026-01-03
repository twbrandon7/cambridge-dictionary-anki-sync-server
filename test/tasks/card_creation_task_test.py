import unittest
from unittest.mock import MagicMock, patch

from marshmallow import ValidationError

from anki_sync_server.tasks.card_creation_task import add_cloze_note_task


class TestCardCreationTask(unittest.TestCase):
    """Unit tests for the card creation Celery task."""

    @patch("anki_sync_server.tasks.card_creation_task.anki")
    @patch("anki_sync_server.tasks.card_creation_task.ClozeNoteSchema")
    def test_add_cloze_note_task_success(self, mock_schema_class, mock_anki):
        """Test successful card creation task."""
        # Setup
        mock_schema = MagicMock()
        mock_schema_class.return_value = mock_schema

        note_data = {
            "word": "test",
            "partOfSpeech": "noun",
            "guideWord": "test",
            "englishDefinition": "definition",
            "definitionTranslation": "translation",
            "cefrLevel": "A1",
            "code": "test",
            "englishExample": "example",
            "exampleTranslation": "example translation",
        }

        loaded_note = MagicMock()
        mock_schema.load.return_value = loaded_note

        result_note = MagicMock()
        result_note.id = 123456
        mock_anki.add_cloze_note.return_value = result_note

        # Execute
        result = add_cloze_note_task(note_data)

        # Assert
        assert result["success"] is True
        assert result["noteId"] == 123456
        mock_schema.load.assert_called_once_with(note_data)
        mock_anki.add_cloze_note.assert_called_once_with([loaded_note])

    @patch("anki_sync_server.tasks.card_creation_task.anki")
    @patch("anki_sync_server.tasks.card_creation_task.ClozeNoteSchema")
    def test_add_cloze_note_task_invalid_note(self, mock_schema_class, mock_anki):
        """Test task with invalid note data."""
        # Setup
        mock_schema = MagicMock()
        mock_schema_class.return_value = mock_schema

        invalid_note_data = {"word": "test"}  # Missing required fields

        # Mock schema validation error
        mock_schema.load.side_effect = ValidationError("Missing field: partOfSpeech")

        # Execute
        result = add_cloze_note_task(invalid_note_data)

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "ValidationError"
        mock_anki.add_cloze_note.assert_not_called()

    @patch("anki_sync_server.tasks.card_creation_task.anki")
    @patch("anki_sync_server.tasks.card_creation_task.ClozeNoteSchema")
    def test_add_cloze_note_task_anki_error(self, mock_schema_class, mock_anki):
        """Test task when Anki operation fails."""
        # Setup
        mock_schema = MagicMock()
        mock_schema_class.return_value = mock_schema

        note_data = {
            "word": "test",
            "partOfSpeech": "noun",
            "guideWord": "test",
            "englishDefinition": "definition",
            "definitionTranslation": "translation",
            "cefrLevel": "A1",
            "code": "test",
            "englishExample": "example",
            "exampleTranslation": "example translation",
        }

        loaded_note = MagicMock()
        mock_schema.load.return_value = loaded_note

        # Mock Anki error
        mock_anki.add_cloze_note.side_effect = RuntimeError("Anki collection locked")

        # Execute
        result = add_cloze_note_task(note_data)

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert result["error"]["type"] == "RuntimeError"
        assert "Anki collection locked" in result["error"]["message"]


if __name__ == "__main__":
    unittest.main()
