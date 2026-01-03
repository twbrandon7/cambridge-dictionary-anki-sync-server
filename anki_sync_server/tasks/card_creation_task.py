import logging
from typing import Any, Dict

from anki_sync_server.anki.cloze_note import ClozeNote as ClozeNoteSchema
from anki_sync_server.server import anki
from anki_sync_server.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="add_cloze_note")
def add_cloze_note_task(
    self, note_data: Dict[str, Any], user_id: str = None
) -> Dict[str, Any]:
    """
    Celery task for asynchronously creating a cloze note in Anki.

    Args:
        note_data: Dictionary containing note fields (word, definition, etc.)
        user_id: Optional user identifier for tracking

    Returns:
        Dictionary with task result (cardId, noteId) or error details
    """
    try:
        # Deserialize note from JSON using ClozeNote schema
        schema = ClozeNoteSchema()
        cloze_note = schema.load(note_data)

        # Call Anki.add_cloze_note() - wrapped in a list as it expects List[ClozeNote]
        result_note = anki.add_cloze_note([cloze_note])

        # Return success metadata
        return {
            "success": True,
            "cardId": result_note.id if hasattr(result_note, "id") else None,
            "noteId": result_note.id if hasattr(result_note, "id") else None,
        }

    except Exception as e:
        logger.exception(f"Error creating cloze note: {str(e)}")

        # Return error metadata
        return {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
            },
        }
